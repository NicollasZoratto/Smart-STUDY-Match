"""Atividade 11 — assinatura recorrente: webhooks assinados e idempotentes, checkout, portal, painel."""
import hashlib
import hmac
import json
import time
from unittest.mock import patch, MagicMock

WHSEC = "whsec_teste_unitario"


def _user(uid=1, role="lider"):
    return {"valid": True, "user_id": uid, "username": "ana", "role": role}


def _evento(tipo, obj, event_id="evt_1"):
    return json.dumps({"id": event_id, "object": "event", "type": tipo, "data": {"object": obj}}).encode()


def _pago(uid="7", event_id="evt_1"):
    return _evento("checkout.session.completed",
                   {"id": "cs_1", "client_reference_id": uid, "payment_status": "paid",
                    "customer": "cus_123", "subscription": "sub_123"}, event_id)


def _assinar(payload, secret=WHSEC):
    ts = int(time.time())
    mac = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={mac}"


def _post(app_mod, payload, sig, rowcount=1):
    """Envia o webhook; devolve (resposta, conexão mock, lista de SQLs executados)."""
    headers = {"Stripe-Signature": sig} if sig is not None else {}
    with patch.object(app_mod, 'STRIPE_WEBHOOK_SECRET', WHSEC), \
         patch.object(app_mod, 'log_event') as log, \
         patch('mysql.connector.connect') as conn:
        cur = conn.return_value.cursor.return_value
        cur.rowcount = rowcount
        res = app_mod.app.test_client().post('/stripe/webhook', data=payload, headers=headers,
                                             content_type='application/json')
    sqls = [c[0][0] for c in cur.execute.call_args_list]
    return res, conn, sqls, log


# --- Webhook: validação de assinatura ---

def test_webhook_sem_assinatura_e_rejeitado(catalog_app):
    res, conn, _, _ = _post(catalog_app, _pago(), None)
    assert res.status_code == 400
    conn.assert_not_called()


def test_webhook_assinatura_forjada_e_rejeitada(catalog_app):
    p = _pago()
    res, conn, _, _ = _post(catalog_app, p, _assinar(p, secret="whsec_atacante"))
    assert res.status_code == 400
    conn.assert_not_called()


def test_webhook_corpo_adulterado_e_rejeitado(catalog_app):
    sig = _assinar(_pago("7"))
    res, conn, _, _ = _post(catalog_app, _pago("8"), sig)
    assert res.status_code == 400
    conn.assert_not_called()


def test_webhook_sem_secret_configurado_retorna_503(catalog_app):
    with patch.object(catalog_app, 'STRIPE_WEBHOOK_SECRET', ""):
        res = catalog_app.app.test_client().post('/stripe/webhook', data=_pago(),
                                                 headers={"Stripe-Signature": "t=1,v1=x"})
    assert res.status_code == 503


# --- Os quatro eventos e o que mudam no banco ---

def test_checkout_completed_ativa_pro(catalog_app):
    p = _pago("7")
    res, conn, sqls, log = _post(catalog_app, p, _assinar(p))
    assert res.status_code == 200
    cur = conn.return_value.cursor.return_value
    insert = cur.execute.call_args_list[-1][0]
    assert "plano = 'pro'" in insert[0] and insert[1] == (7, "cus_123", "sub_123")
    log.assert_called_once_with(7, 'assinatura_premium_ativada')


def test_checkout_nao_pago_nao_ativa(catalog_app):
    p = _evento("checkout.session.completed", {"client_reference_id": "7", "payment_status": "unpaid"})
    res, conn, sqls, log = _post(catalog_app, p, _assinar(p))
    assert res.status_code == 200 and not any('UPDATE' in s or 'ON DUPLICATE' in s for s in sqls)
    log.assert_not_called()


def test_subscription_updated_atualiza_status_e_plano(catalog_app):
    p = _evento("customer.subscription.updated",
                {"id": "sub_123", "customer": "cus_123", "status": "active", "cancel_at_period_end": True,
                 "items": {"data": [{"price": {"id": "price_pro"}}]}})
    res, conn, sqls, log = _post(catalog_app, p, _assinar(p))
    sql, params = conn.return_value.cursor.return_value.execute.call_args_list[-1][0]
    assert res.status_code == 200 and sql.startswith("UPDATE assinaturas")
    assert params[:4] == ('pro', 'active', 1, 1) and 'cus_123' in params and 'price_pro' in params


def test_subscription_updated_past_due_volta_ao_free(catalog_app):
    p = _evento("customer.subscription.updated", {"id": "sub_1", "customer": "cus_1", "status": "past_due"})
    res, conn, _, _ = _post(catalog_app, p, _assinar(p))
    params = conn.return_value.cursor.return_value.execute.call_args_list[-1][0][1]
    assert params[:3] == ('free', 'past_due', 0)


def test_subscription_deleted_volta_ao_free(catalog_app):
    p = _evento("customer.subscription.deleted", {"id": "sub_1", "customer": "cus_1"})
    res, conn, _, log = _post(catalog_app, p, _assinar(p))
    params = conn.return_value.cursor.return_value.execute.call_args_list[-1][0][1]
    assert res.status_code == 200 and params[:3] == ('free', 'canceled', 0)
    log.assert_called_once_with(None, 'assinatura_premium_cancelada')


def test_invoice_payment_failed_marca_inadimplente_e_tira_o_pro(catalog_app):
    p = _evento("invoice.payment_failed", {"customer": "cus_1"})
    res, conn, _, log = _post(catalog_app, p, _assinar(p))
    params = conn.return_value.cursor.return_value.execute.call_args_list[-1][0][1]
    assert res.status_code == 200 and params[:3] == ('free', 'past_due', 0)
    log.assert_called_once_with(None, 'assinatura_pagamento_falhou')


# --- Idempotência: mesmo evento duas vezes ---

def test_evento_duplicado_nao_e_processado_de_novo(catalog_app):
    p = _pago("7", event_id="evt_repetido")
    res, conn, sqls, log = _post(catalog_app, p, _assinar(p), rowcount=0)  # INSERT IGNORE não inseriu
    assert res.status_code == 200 and res.get_json()['duplicate'] is True
    assert len(sqls) == 1 and sqls[0].startswith("INSERT IGNORE INTO stripe_eventos")
    log.assert_not_called()


def test_erro_ao_processar_devolve_500_para_o_stripe_reenviar(catalog_app):
    p = _pago()
    with patch.object(catalog_app, 'STRIPE_WEBHOOK_SECRET', WHSEC), \
         patch('mysql.connector.connect', side_effect=Exception("banco fora")):
        res = catalog_app.app.test_client().post('/stripe/webhook', data=p,
                                                 headers={"Stripe-Signature": _assinar(p)})
    assert res.status_code == 500


# --- Checkout e portal ---

def test_assinar_exige_login(catalog_app):
    with patch.object(catalog_app, 'get_current_user', return_value=None):
        res = catalog_app.app.test_client().post('/assinar')
    assert res.status_code == 302 and '/login' in res.headers['Location']


def test_assinar_cria_checkout_de_assinatura_ligado_ao_customer(catalog_app):
    fake = MagicMock(url="https://checkout.stripe.com/c/pay/cs_test_abc")
    with patch.object(catalog_app, 'STRIPE_SECRET_KEY', 'sk_test_x'), \
         patch.object(catalog_app, 'get_current_user', return_value=_user(5)), \
         patch.object(catalog_app, 'usuario_e_premium', return_value=False), \
         patch.object(catalog_app, 'obter_ou_criar_customer', return_value='cus_9'), \
         patch.object(catalog_app, 'log_event'), \
         patch('stripe.checkout.Session.create', return_value=fake) as create:
        res = catalog_app.app.test_client().post('/assinar', data={"user_id": "999"})
    assert res.status_code == 303 and res.headers['Location'] == fake.url
    kw = create.call_args.kwargs
    assert kw['mode'] == 'subscription' and kw['customer'] == 'cus_9'
    assert kw['client_reference_id'] == '5'  # vem do JWT, não do formulário


def test_portal_abre_billing_portal_do_proprio_customer(catalog_app):
    fake = MagicMock(url="https://billing.stripe.com/p/session/abc")
    with patch.object(catalog_app, 'STRIPE_SECRET_KEY', 'sk_test_x'), \
         patch.object(catalog_app, 'get_current_user', return_value=_user(5)), \
         patch.object(catalog_app, 'obter_assinatura', return_value={"stripe_customer_id": "cus_5"}), \
         patch.object(catalog_app, 'log_event'), \
         patch('stripe.billing_portal.Session.create', return_value=fake) as create:
        res = catalog_app.app.test_client().post('/assinatura/portal')
    assert res.status_code == 303 and res.headers['Location'] == fake.url
    assert create.call_args.kwargs['customer'] == 'cus_5'


def test_portal_sem_customer_nao_abre(catalog_app):
    with patch.object(catalog_app, 'STRIPE_SECRET_KEY', 'sk_test_x'), \
         patch.object(catalog_app, 'get_current_user', return_value=_user(5)), \
         patch.object(catalog_app, 'obter_assinatura', return_value={"stripe_customer_id": None}):
        res = catalog_app.app.test_client().post('/assinatura/portal')
    assert res.status_code == 302 and '/perfil' in res.headers['Location']


# --- Painel admin ---

def test_painel_403_para_nao_admin(catalog_app):
    with patch.object(catalog_app, 'get_current_user', return_value=_user(role="lider")), \
         patch.object(catalog_app, 'log_event') as log:
        res = catalog_app.app.test_client().get('/admin/painel')
    assert res.status_code == 403
    log.assert_called_once_with(1, '403_acesso_painel_negado')


def test_painel_admin_mostra_planos_mrr_e_eventos(catalog_app):
    dados = {"total_usuarios": 10, "usuarios_pro": 3, "usuarios_free": 7, "assinaturas_ativas": 3,
             "inadimplentes": 1, "mrr_reais": 29.7,
             "eventos": [{"timestamp": "t", "usuario": "ana", "acao": "👑 Plano Pro ativado", "ip": ""}]}
    with patch.object(catalog_app, 'get_current_user', return_value=_user(role="admin")), \
         patch.object(catalog_app, 'dados_painel', return_value=dados):
        res = catalog_app.app.test_client().get('/admin/painel')
    html = res.get_data(as_text=True)
    assert res.status_code == 200 and 'R$ 29,70' in html and 'Plano Pro ativado' in html


def test_dados_painel_calcula_mrr_com_assinaturas_ativas(catalog_app):
    with patch.object(catalog_app, '_buscar_usuarios', return_value={1: 'a', 2: 'b', 3: 'c', 4: 'd'}), \
         patch.object(catalog_app, '_consulta', side_effect=[{"n": 2}, {"n": 1}]), \
         patch.object(catalog_app, '_eventos_recentes', return_value=[]):
        d = catalog_app.dados_painel()
    assert d['usuarios_pro'] == 2 and d['usuarios_free'] == 2 and d['mrr_reais'] == 19.8 and d['inadimplentes'] == 1
