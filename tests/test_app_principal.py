"""StudyMatch — landing, RBAC (admin/lider/estudante), isolamento e CRUD de grupos."""
import io
from unittest.mock import patch, MagicMock

import pytest

DADOS = {"titulo": "Revisão de JOIN", "descricao": "P2", "disciplina_id": "2", "dia_semana": "2",
         "horario_inicio": "21:00", "horario_fim": "22:30", "vagas": "5", "modalidade": "online"}


def _user(user_id=1, role="lider", username="ana"):
    return {"valid": True, "user_id": user_id, "username": username, "role": role}


def _grupo(lider_id=1, gid=10, foto_key=None):
    return {"id": gid, "lider_id": lider_id, "disciplina_id": 2, "disciplina_nome": "Banco de Dados",
            "titulo": "Revisão de JOIN", "descricao": "P2", "dia_semana": 2, "horario_inicio": "21:00",
            "horario_fim": "22:30", "vagas": 5, "membros": 1, "modalidade": "online", "foto_key": foto_key}


@pytest.fixture
def ctx(catalog_app):
    """App com usuário e log mockados; devolve (módulo, cliente, função pra trocar o usuário)."""
    client = catalog_app.app.test_client()
    return catalog_app, client


def _com(app_mod, user, **extras):
    from contextlib import ExitStack
    st = ExitStack()
    st.enter_context(patch.object(app_mod, 'get_current_user', return_value=user))
    st.enter_context(patch.object(app_mod, 'log_event'))
    for nome, valor in extras.items():
        st.enter_context(patch.object(app_mod, nome, **({"side_effect": valor} if callable(valor) else {"return_value": valor})))
    return st


# --- Landing pública ---

def test_landing_e_publica_e_mostra_proposta_de_valor(ctx):
    app_mod, client = ctx
    with patch.object(app_mod, 'get_current_user', return_value=None):
        res = client.get('/')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'match por disciplina e horário' in html and 'Criar conta' in html


def test_logado_na_raiz_vai_para_grupos(ctx):
    app_mod, client = ctx
    with patch.object(app_mod, 'get_current_user', return_value=_user()):
        res = client.get('/')
    assert res.status_code == 302 and '/grupos' in res.headers['Location']


def test_api_sem_login_retorna_401(ctx):
    app_mod, client = ctx
    with patch.object(app_mod, 'get_current_user', return_value=None):
        assert client.get('/api/grupos').status_code == 401


# --- RBAC: ação proibida = 403 direto na API ---

def test_estudante_nao_pode_criar_grupo_403(ctx):
    app_mod, client = ctx
    with _com(app_mod, _user(role="estudante")):
        res = client.post('/api/grupos', json=DADOS)
    assert res.status_code == 403
    assert res.get_json()['codigo'] == 'papel_sem_permissao'


def test_estudante_nao_pode_editar_nem_excluir_403(ctx):
    app_mod, client = ctx
    with _com(app_mod, _user(user_id=2, role="estudante"), carregar_grupo=_grupo(lider_id=1)):
        assert client.put('/api/grupos/10', json=DADOS).status_code == 403
        assert client.delete('/api/grupos/10').status_code == 403


def test_admin_logs_403_para_nao_admin(ctx):
    app_mod, client = ctx
    with _com(app_mod, _user(role="lider")):
        assert client.get('/admin/logs').status_code == 403


# --- Isolamento: registro de outra pessoa = 403 ---

def test_abrir_grupo_de_outro_usuario_403(ctx):
    app_mod, client = ctx
    with _com(app_mod, _user(user_id=2, role="estudante"), carregar_grupo=_grupo(lider_id=1),
              eh_membro=False):
        res = client.get('/api/grupos/10')
    assert res.status_code == 403


def test_lider_nao_edita_grupo_de_outro_lider_403(ctx):
    app_mod, client = ctx
    with _com(app_mod, _user(user_id=2, role="lider"), carregar_grupo=_grupo(lider_id=1)):
        assert client.put('/api/grupos/10', json=DADOS).status_code == 403
        assert client.delete('/api/grupos/10').status_code == 403


def test_pagina_de_grupo_alheio_403(ctx):
    app_mod, client = ctx
    with _com(app_mod, _user(user_id=2, role="estudante"), carregar_grupo=_grupo(lider_id=1),
              eh_membro=False):
        assert client.get('/grupos/10').status_code == 403


def test_grupo_inexistente_404(ctx):
    app_mod, client = ctx
    with _com(app_mod, _user(), carregar_grupo=None):
        assert client.get('/api/grupos/999').status_code == 404


def test_dono_ve_o_proprio_grupo(ctx):
    app_mod, client = ctx
    with _com(app_mod, _user(user_id=1), carregar_grupo=_grupo(lider_id=1)):
        res = client.get('/api/grupos/10')
    assert res.status_code == 200 and res.get_json()['titulo'] == 'Revisão de JOIN'
    assert res.get_json()['horario_inicio'] == '21:00'


# --- CRUD do líder ---

def test_lider_cria_grupo_e_gera_log_de_negocio(ctx):
    app_mod, client = ctx
    cur = MagicMock(); cur.lastrowid = 10
    with _com(app_mod, _user(), usuario_e_premium=False, contar_grupos_do_lider=0,
              carregar_grupo=_grupo(), _consulta={"id": 2}) as st, \
         patch('mysql.connector.connect') as conn:
        conn.return_value.cursor.return_value = cur
        res = client.post('/api/grupos', json=DADOS)
        log = app_mod.log_event
    assert res.status_code == 201
    assert log.call_args[0][1] == 'grupo_criado:grupo_10'


def test_lider_edita_e_remove_o_proprio_grupo(ctx):
    app_mod, client = ctx
    with _com(app_mod, _user(user_id=1), carregar_grupo=_grupo(lider_id=1), _consulta={"id": 2}), \
         patch('mysql.connector.connect'):
        assert client.put('/api/grupos/10', json=DADOS).status_code == 200
        assert client.delete('/api/grupos/10').status_code == 204
        assert app_mod.log_event.call_args[0][1] == 'grupo_removido:grupo_10'


def test_validacao_rejeita_horario_invertido_400(ctx):
    app_mod, client = ctx
    ruim = dict(DADOS, horario_inicio="22:00", horario_fim="21:00")
    with _com(app_mod, _user(), usuario_e_premium=True, _consulta={"id": 2}):
        res = client.post('/api/grupos', json=ruim)
    assert res.status_code == 400


def test_admin_lista_todos_e_estudante_so_os_seus(ctx):
    app_mod, client = ctx
    with _com(app_mod, _user(role="admin"), _consulta=[_grupo(1, 1), _grupo(2, 2)]):
        assert len(client.get('/api/grupos').get_json()) == 2
    with _com(app_mod, _user(user_id=3, role="estudante"), _consulta=[]) :
        assert client.get('/api/grupos').get_json() == []


# --- Upload no MinIO ligado ao grupo ---

def _png():
    from PIL import Image
    buf = io.BytesIO(); Image.new('RGB', (4, 4)).save(buf, format='PNG'); return buf.getvalue()


def test_dono_envia_capa_para_o_minio(ctx):
    app_mod, client = ctx
    with _com(app_mod, _user(user_id=1), carregar_grupo=_grupo(lider_id=1)), \
         patch.object(app_mod, 'minio_client') as minio, patch.object(app_mod, 'init_minio_bucket'), \
         patch('mysql.connector.connect'):
        res = client.post('/api/grupos/10/foto', data={"foto": (io.BytesIO(_png()), "c.png")},
                          content_type='multipart/form-data')
        chave = minio.put_object.call_args[0][1]
    assert res.status_code == 200 and chave.startswith('grupos/10/')


def test_outro_usuario_nao_envia_capa_403(ctx):
    app_mod, client = ctx
    with _com(app_mod, _user(user_id=2, role="lider"), carregar_grupo=_grupo(lider_id=1)):
        res = client.post('/api/grupos/10/foto', data={"foto": (io.BytesIO(_png()), "c.png")},
                          content_type='multipart/form-data')
    assert res.status_code == 403


# --- Plano Free x Pro ---

def test_lider_gratis_no_limite_nao_cria_mais_grupos(ctx):
    app_mod, client = ctx
    with _com(app_mod, _user(), usuario_e_premium=False, contar_grupos_do_lider=app_mod.GRUPOS_LIMITE_GRATIS):
        res = client.post('/api/grupos', json=DADOS)
        log = app_mod.log_event
    assert res.status_code == 403 and res.get_json()['codigo'] == 'limite_plano_gratis'
    msg = res.get_json()['error']
    assert 'Limite do plano Free' in msg and 'Pro' in msg  # diz qual é o limite e como liberar
    assert log.call_args[0][1] == 'limite_grupos_gratis_atingido'


def test_lider_pro_cria_alem_do_limite(ctx):
    app_mod, client = ctx
    cur = MagicMock(); cur.lastrowid = 11
    with _com(app_mod, _user(), usuario_e_premium=True, contar_grupos_do_lider=99,
              carregar_grupo=_grupo(gid=11), _consulta={"id": 2}), patch('mysql.connector.connect') as conn:
        conn.return_value.cursor.return_value = cur
        assert client.post('/api/grupos', json=DADOS).status_code == 201


# --- Telas renderizam com os textos do negócio ---

def test_telas_de_grupos_renderizam(ctx):
    app_mod, client = ctx
    disc = [{"id": 2, "codigo": "BDD001", "nome": "Banco de Dados"}]
    with _com(app_mod, _user(user_id=1), usuario_e_premium=False, listar_disciplinas=disc,
              _consulta=[_grupo()], carregar_grupo=_grupo()):
        lista = client.get('/grupos').get_data(as_text=True)
        form = client.get('/grupos/novo').get_data(as_text=True)
        det = client.get('/grupos/10').get_data(as_text=True)
        edit = client.get('/grupos/10/editar').get_data(as_text=True)
    assert 'Revisão de JOIN' in lista and 'Assinar Pro' in lista
    assert 'Banco de Dados' in form and 'Salvar' in form
    assert 'Banco de Dados' in det and 'Excluir' in det
    assert 'value="Revisão de JOIN"' in edit


def test_tela_de_novo_grupo_403_para_estudante(ctx):
    app_mod, client = ctx
    with _com(app_mod, _user(role="estudante")):
        assert client.get('/grupos/novo').status_code == 403
