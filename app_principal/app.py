import functools
import glob
import io
import json
import os
import uuid
import datetime

import requests
import stripe
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify
import mysql.connector
from minio import Minio
from minio.error import S3Error
from PIL import Image

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave_secreta_padrao_desenv")

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:5001")
LOG_SERVICE_URL = os.getenv("LOG_SERVICE_URL", "http://log_service:5002")

DB_HOST = os.getenv("DB_HOST", "35.226.64.52")
DB_USER = os.getenv("DB_USER", "IAC_2026_02_nicollas_carvalho")
DB_PASSWORD = os.getenv("DB_PASSWORD", "nico11as")
DB_NAME = os.getenv("DB_NAME", "IAC_2026_02_nicollas_carvalho")

# --- MinIO (Atividade 6: fotos de perfil) ---
# Endpoint INTERNO: usado pra upload/leitura de verdade, via rede Docker (rápido, não depende do host).
MINIO_INTERNAL_ENDPOINT = os.getenv("MINIO_INTERNAL_ENDPOINT", "minio:9000")
# Endpoint PÚBLICO: usado só pra MONTAR a URL pré-assinada, porque é o navegador do
# usuário (não o container) que vai baixar a imagem direto do MinIO.
# Se vazio, o host é deduzido do endereço que o usuário abriu no navegador
# (IP/domínio do servidor) + MINIO_PUBLIC_PORT (porta publicada do MinIO).
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_ENDPOINT", "")
MINIO_PUBLIC_PORT = os.getenv("MINIO_PUBLIC_PORT", "29517")
# Região fixa: assina as URLs localmente, sem chamada de rede ao MinIO.
MINIO_REGION = "us-east-1"
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "nicoflix_admin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "nicoflix_minio_secret")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "studymatch-arquivos")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
PRESIGNED_URL_EXPIRY_SECONDS = int(os.getenv("PRESIGNED_URL_EXPIRY_SECONDS", "3600"))  # 1h

# --- Stripe (Atividade 7: plano Premium, modo teste) ---
# As chaves vêm SEMPRE de variáveis de ambiente (nunca no código/Git).
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")        # sk_test_...
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")  # whsec_...
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")            # price_... (opcional)
# Benefício Pro: grupos próprios ilimitados. Plano grátis tem este teto (líder).
GRUPOS_LIMITE_GRATIS = int(os.getenv("GRUPOS_LIMITE_GRATIS", "1"))
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

MAX_FOTO_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB
FORMATOS_AGEITOS = {"jpeg", "png", "webp"}

minio_client = Minio(
    MINIO_INTERNAL_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
    region=MINIO_REGION,
)


def get_db():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )


def init_app_tables():
    """Garante perfis/assinaturas e roda as migrações db/*.sql do domínio (grupos)."""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perfis (
                user_id INT PRIMARY KEY,
                nome_exibicao VARCHAR(100) NOT NULL,
                bio VARCHAR(280) NOT NULL DEFAULT '',
                foto_key VARCHAR(255),
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        # Atividade 7: só guarda o status premium e IDs do Stripe (NUNCA dados de cartão).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assinaturas (
                user_id INT PRIMARY KEY,
                premium TINYINT(1) NOT NULL DEFAULT 0,
                stripe_customer_id VARCHAR(64),
                stripe_subscription_id VARCHAR(64),
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        db.commit()
        cursor.close()
        db.close()
    except Exception as e:
        print(f"Erro ao inicializar tabelas da app principal: {e}")
    aplicar_migracoes()


def _pasta_db():
    base = os.path.dirname(os.path.abspath(__file__))
    for cand in (os.path.join(base, 'db'), os.path.join(os.path.dirname(base), 'db')):
        if os.path.isdir(cand):
            return cand
    return None


def aplicar_migracoes():
    """Executa db/*.sql em ordem alfabética (scripts idempotentes, versionados no Git)."""
    pasta = _pasta_db()
    if not pasta:
        print("[DB] Pasta db/ não encontrada; migrações ignoradas.")
        return
    try:
        db = get_db()
        cursor = db.cursor()
        for arquivo in sorted(glob.glob(os.path.join(pasta, '*.sql'))):
            with open(arquivo, encoding='utf-8') as f:
                linhas = [l for l in f.read().splitlines() if not l.strip().startswith('--')]
            for comando in "\n".join(linhas).split(';'):
                if comando.strip():
                    cursor.execute(comando)
            print(f"[DB] Migração aplicada: {os.path.basename(arquivo)}")
        db.commit()
        cursor.close()
        db.close()
    except Exception as e:
        print(f"[DB ERROR] Falha ao aplicar migrações: {e}")


def init_minio_bucket():
    """Garante que o bucket dedicado deste projeto existe no MinIO."""
    try:
        if not minio_client.bucket_exists(MINIO_BUCKET):
            minio_client.make_bucket(MINIO_BUCKET)
            print(f"[MINIO] Bucket '{MINIO_BUCKET}' criado.")
    except Exception as e:
        print(f"[MINIO ERROR] Falha ao preparar bucket '{MINIO_BUCKET}': {e}")


init_app_tables()
init_minio_bucket()


def log_event(usuario_id, acao):
    try:
        requests.post(
            f"{LOG_SERVICE_URL}/log",
            json={"usuario_id": usuario_id, "acao": acao, "ip": request.remote_addr},
            timeout=3
        )
    except Exception as e:
        print(f"[LOG WARNING] Não foi possível registrar evento '{acao}': {e}")


def get_current_user():
    token = session.get('jwt_token')
    if not token:
        cabecalho = request.headers.get('Authorization', '')
        if cabecalho.lower().startswith('bearer '):
            token = cabecalho[7:].strip()
    if not token:
        return None
    try:
        res = requests.post(f"{AUTH_SERVICE_URL}/validate-token", json={"token": token}, timeout=5)
        if res.status_code == 200 and res.json().get('valid'):
            return res.json()
    except Exception as e:
        print(f"Erro ao validar token no Auth Service: {e}")
    return None


def usuario_e_premium(user_id):
    """True se o usuário tem assinatura Premium ativa. Falha fechada (False) em erro."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT premium FROM assinaturas WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        db.close()
        return bool(row and row.get('premium'))
    except Exception as e:
        print(f"Erro ao consultar premium: {e}")
        return False


def get_or_create_perfil(user_id, username_padrao):
    """Busca o perfil do usuário; cria um com valores padrão se ainda não existir."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM perfis WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                "INSERT INTO perfis (user_id, nome_exibicao, bio, foto_key) VALUES (%s, %s, '', NULL)",
                (user_id, username_padrao)
            )
            db.commit()
            row = {"user_id": user_id, "nome_exibicao": username_padrao, "bio": "", "foto_key": None}
        cursor.close()
        db.close()
        return row
    except Exception as e:
        print(f"Erro ao buscar/criar perfil: {e}")
        return {"user_id": user_id, "nome_exibicao": username_padrao, "bio": "", "foto_key": None}


def _endpoint_publico_minio():
    """Host:porta que o NAVEGADOR usa pra alcançar o MinIO."""
    if MINIO_PUBLIC_ENDPOINT:
        return MINIO_PUBLIC_ENDPOINT
    host = request.host.split(':')[0]
    return f"{host}:{MINIO_PUBLIC_PORT}"


def gerar_url_foto(foto_key):
    """Gera uma URL pré-assinada (temporária) pra servir a foto de perfil
    direto do MinIO pro navegador, sem o bucket precisar ser público."""
    if not foto_key:
        return None
    try:
        cliente_publico = Minio(
            _endpoint_publico_minio(),
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE,
            region=MINIO_REGION,
        )
        return cliente_publico.presigned_get_object(
            MINIO_BUCKET, foto_key,
            expires=datetime.timedelta(seconds=PRESIGNED_URL_EXPIRY_SECONDS)
        )
    except Exception as e:
        print(f"Erro ao gerar URL assinada da foto: {e}")
        return None


def _buscar_usuarios():
    try:
        res = requests.get(f"{AUTH_SERVICE_URL}/users", timeout=5)
        if res.status_code == 200:
            return {u['id']: u['username'] for u in res.json().get('users', [])}
    except Exception as e:
        print(f"Erro ao buscar usuários no Auth Service: {e}")
    return {}


_ACAO_LABELS = {
    'login': '🔓 Login',
    'logout': '🔒 Logout',
    'grupo_criado': '📚 Grupo de estudo criado',
    'grupo_editado': '✏️ Grupo de estudo editado',
    'grupo_removido': '🗑️ Grupo de estudo removido',
    'foto_grupo_enviada': '🖼️ Foto do grupo enviada',
    'editar_perfil': '📝 Editou o perfil',
    'upload_foto_perfil': '🖼️ Trocou a foto de perfil',
    'assinatura_checkout_iniciado': '💳 Iniciou checkout Pro',
    'assinatura_premium_ativada': '👑 Plano Pro ativado (webhook Stripe)',
    'assinatura_premium_cancelada': '❎ Plano Pro cancelado (webhook Stripe)',
    'limite_grupos_gratis_atingido': '🚫 Limite de grupos do plano grátis',
}


def _rotular_acao(acao_bruta):
    base = acao_bruta.split(':')[0]
    if base in _ACAO_LABELS:
        return _ACAO_LABELS[base]
    if base.startswith('403'):
        return f"🚫 Ação negada (403) — {acao_bruta}"
    return acao_bruta


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            res = requests.post(f"{AUTH_SERVICE_URL}/login", json={"username": username, "password": password}, timeout=5)
            if res.status_code == 200:
                data = res.json()
                session['pending_username'] = username
                dev_code = data.get('dev_code', '')
                flash(f"Código 2FA gerado: {dev_code}", "info")
                return redirect(url_for('verify_2fa_page'))
            else:
                err_msg = res.json().get('error', 'Erro ao realizar login')
                flash(err_msg, "danger")
        except Exception as e:
            flash(f"Erro de conexão com serviço de autenticação: {e}", "danger")

    return render_template('login.html')


@app.route('/cadastro', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            res = requests.post(
                f"{AUTH_SERVICE_URL}/register",
                json={"username": username, "email": email, "password": password,
                      "role": request.form.get('role', 'estudante')},
                timeout=5
            )
            if res.status_code == 201:
                flash("Conta criada com sucesso! Faça login abaixo.", "success")
                return redirect(url_for('login'))
            else:
                err_msg = res.json().get('error', 'Erro ao cadastrar usuário')
                flash(err_msg, "danger")
        except Exception as e:
            flash(f"Erro de conexão com serviço de autenticação: {e}", "danger")

    return render_template('login.html')


@app.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa_page():
    username = session.get('pending_username')
    if not username:
        return redirect(url_for('login'))

    if request.method == 'POST':
        code = request.form.get('code')
        try:
            res = requests.post(
                f"{AUTH_SERVICE_URL}/verify-2fa",
                json={"username": username, "code": code, "ip": request.remote_addr},
                timeout=5
            )
            if res.status_code == 200:
                data = res.json()
                session.pop('pending_username', None)
                session['jwt_token'] = data['token']
                return redirect(url_for('grupos_lista'))
            else:
                err_msg = res.json().get('error', 'Código 2FA inválido')
                flash(err_msg, "danger")
        except Exception as e:
            flash(f"Erro ao validar 2FA: {e}", "danger")

    return render_template('verify_2fa.html', username=username)


@app.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        email = request.form.get('email')
        try:
            res = requests.post(f"{AUTH_SERVICE_URL}/forgot-password", json={"email": email}, timeout=5)
            if res.status_code == 200:
                flash(res.json().get('message', 'Se o e-mail existir, um link foi enviado.'), "success")
            else:
                flash(res.json().get('error', 'Erro ao solicitar redefinição de senha'), "danger")
        except Exception as e:
            flash(f"Erro de conexão com serviço de autenticação: {e}", "danger")
        return redirect(url_for('login'))

    return render_template('forgot_password.html')


@app.route('/reset-senha/<token>', methods=['GET', 'POST'])
def reset_senha(token):
    if request.method == 'POST':
        nova_senha = request.form.get('password')
        confirmar_senha = request.form.get('confirm_password')

        if nova_senha != confirmar_senha:
            flash("As senhas não coincidem.", "danger")
            return render_template('reset_password.html', token=token)

        try:
            res = requests.post(
                f"{AUTH_SERVICE_URL}/reset-password",
                json={"token": token, "new_password": nova_senha},
                timeout=5
            )
            if res.status_code == 200:
                flash("Senha redefinida com sucesso! Faça login com a nova senha.", "success")
                return redirect(url_for('login'))
            else:
                flash(res.json().get('error', 'Não foi possível redefinir a senha'), "danger")
                return render_template('reset_password.html', token=token)
        except Exception as e:
            flash(f"Erro de conexão com serviço de autenticação: {e}", "danger")
            return render_template('reset_password.html', token=token)

    try:
        res = requests.post(f"{AUTH_SERVICE_URL}/validate-reset-token", json={"token": token}, timeout=5)
        if res.status_code != 200 or not res.json().get('valid'):
            flash(res.json().get('error', 'Link inválido ou expirado. Solicite um novo.'), "danger")
            return redirect(url_for('esqueci_senha'))
    except Exception as e:
        flash(f"Erro ao validar link: {e}", "danger")
        return redirect(url_for('esqueci_senha'))

    return render_template('reset_password.html', token=token)


@app.route('/logout')
def logout():
    user = get_current_user()
    if user:
        log_event(user['user_id'], 'logout')
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin/logs')
def admin_logs():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user.get('role') != 'admin':
        log_event(user['user_id'], '403_acesso_logs_negado')
        abort(403)

    usuarios_por_id = _buscar_usuarios()
    eventos = []
    try:
        res = requests.get(f"{LOG_SERVICE_URL}/events", params={"limit": 100}, timeout=5)
        if res.status_code == 200:
            for e in res.json().get('events', []):
                uid = e.get('usuario_id')
                try:
                    uid_int = int(uid)
                except (TypeError, ValueError):
                    uid_int = uid
                eventos.append({
                    "usuario": usuarios_por_id.get(uid_int, f"Usuário #{uid}"),
                    "acao": _rotular_acao(e.get('acao', '')),
                    "timestamp": e.get('timestamp', ''),
                    "ip": e.get('ip', ''),
                })
        else:
            flash("Não foi possível consultar o serviço de logs.", "danger")
    except Exception as e:
        flash(f"Erro de conexão com o serviço de logs: {e}", "danger")

    return render_template('admin_logs.html', eventos=eventos, usuario=user['username'])


@app.route('/assinar', methods=['POST'])
def assinar():
    """Cria uma Checkout Session (modo assinatura) e redireciona o usuário logado ao Stripe."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if not STRIPE_SECRET_KEY:
        flash('Pagamentos não configurados no servidor (STRIPE_SECRET_KEY ausente).', 'error')
        return redirect(url_for('perfil'))
    if usuario_e_premium(user['user_id']):
        flash('Você já é Pro. 👑', 'success')
        return redirect(url_for('perfil'))

    if STRIPE_PRICE_ID:
        item = {"price": STRIPE_PRICE_ID, "quantity": 1}
    else:  # fallback: cria o preço inline (R$ 9,90/mês)
        item = {"quantity": 1, "price_data": {
            "currency": "brl", "unit_amount": 990,
            "recurring": {"interval": "month"},
            "product_data": {"name": "StudyMatch Pro"}}}
    base = request.host_url.rstrip('/')
    try:
        checkout = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[item],
            # id vem do JWT validado, nunca de um campo do formulário
            client_reference_id=str(user['user_id']),
            success_url=f"{base}/assinatura/sucesso",
            cancel_url=f"{base}/perfil",
        )
    except Exception as e:
        print(f"Erro ao criar checkout Stripe: {e}")
        flash('Não foi possível iniciar o pagamento agora. Tente novamente.', 'error')
        return redirect(url_for('perfil'))
    log_event(user['user_id'], 'assinatura_checkout_iniciado')
    return redirect(checkout.url, code=303)


@app.route('/assinatura/sucesso')
def assinatura_sucesso():
    """Só informativa: o Premium é liberado EXCLUSIVAMENTE pelo webhook assinado."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if usuario_e_premium(user['user_id']):
        flash('Pagamento confirmado! Seu plano Pro está ativo. 👑', 'success')
    else:
        flash('Pagamento recebido. Estamos aguardando a confirmação do Stripe — '
              'atualize a página em alguns segundos.', 'success')
    return redirect(url_for('perfil'))


@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Recebe eventos do Stripe. Rejeita (400) qualquer requisição sem assinatura válida."""
    if not STRIPE_WEBHOOK_SECRET:
        return {"error": "webhook nao configurado"}, 503
    payload = request.get_data()  # corpo CRU: a assinatura é calculada sobre ele
    sig = request.headers.get('Stripe-Signature', '')
    try:
        stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        return {"error": "payload invalido"}, 400
    except Exception as e:  # SignatureVerificationError (e qualquer falha de verificação)
        print(f"[STRIPE] assinatura rejeitada: {type(e).__name__}")
        return {"error": "assinatura invalida"}, 400

    evento = json.loads(payload)
    tipo = evento.get('type')
    obj = (evento.get('data') or {}).get('object') or {}
    try:
        if tipo == 'checkout.session.completed':
            ref = str(obj.get('client_reference_id') or '')
            if ref.isdigit() and obj.get('payment_status') in ('paid', 'no_payment_required'):
                user_id = int(ref)
                db = get_db()
                cursor = db.cursor()
                cursor.execute(
                    """INSERT INTO assinaturas (user_id, premium, stripe_customer_id, stripe_subscription_id)
                       VALUES (%s, 1, %s, %s)
                       ON DUPLICATE KEY UPDATE premium = 1,
                         stripe_customer_id = VALUES(stripe_customer_id),
                         stripe_subscription_id = VALUES(stripe_subscription_id)""",
                    (user_id, obj.get('customer'), obj.get('subscription')))
                db.commit(); cursor.close(); db.close()
                _log_sem_request(user_id, 'assinatura_premium_ativada')
        elif tipo == 'customer.subscription.deleted':
            sub_id = obj.get('id')
            if sub_id:
                db = get_db()
                cursor = db.cursor()
                cursor.execute("UPDATE assinaturas SET premium = 0 WHERE stripe_subscription_id = %s", (sub_id,))
                db.commit(); cursor.close(); db.close()
                _log_sem_request(None, 'assinatura_premium_cancelada')
    except Exception as e:
        print(f"[STRIPE] erro ao processar evento {tipo}: {e}")
        return {"error": "falha ao processar"}, 500  # Stripe reenviará
    return {"received": True}, 200


def _log_sem_request(usuario_id, acao):
    log_event(usuario_id, acao)


@app.route('/perfil/<int:user_id>/editar', methods=['POST'])
def editar_perfil(user_id):
    """Edita nome de exibição e bio. Só o dono do perfil pode editar —
    o backend confere a identidade de quem está logado (user['user_id']
    vindo do JWT validado pelo auth_service), e NUNCA confia no user_id
    que vier no corpo da requisição além do que está na própria URL."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if user_id != int(user['user_id']):
        log_event(user['user_id'], f'403_editar_perfil_negado:alvo_{user_id}')
        abort(403)

    nome_exibicao = (request.form.get('nome_exibicao') or user['username']).strip()[:100]
    bio = (request.form.get('bio') or '').strip()[:280]

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO perfis (user_id, nome_exibicao, bio)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE nome_exibicao = VALUES(nome_exibicao), bio = VALUES(bio)
        """, (user_id, nome_exibicao, bio))
        db.commit()
        cursor.close()
        db.close()
        log_event(user['user_id'], 'editar_perfil')
        flash("Perfil atualizado!", "success")
    except Exception as e:
        print(f"Erro ao editar perfil: {e}")
        flash("Erro ao atualizar o perfil.", "danger")

    return redirect(url_for('perfil'))


@app.route('/perfil/<int:user_id>/foto', methods=['POST'])
def upload_foto_perfil(user_id):
    """Upload da foto de perfil pro MinIO. Mesma checagem de identidade
    da edição de perfil: só o dono pode trocar a própria foto, mesmo
    manipulando o user_id na requisição."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if user_id != int(user['user_id']):
        log_event(user['user_id'], f'403_upload_foto_negado:alvo_{user_id}')
        abort(403)

    arquivo = request.files.get('foto')
    if not arquivo or arquivo.filename == '':
        flash("Selecione uma imagem para enviar.", "danger")
        return redirect(url_for('perfil'))

    conteudo = arquivo.read()

    if len(conteudo) > MAX_FOTO_SIZE_BYTES:
        flash("Imagem maior que o limite de 2 MB.", "danger")
        return redirect(url_for('perfil'))

    # Não confia no Content-Type que o navegador mandou — abre a imagem de
    # verdade com Pillow pra confirmar que é um arquivo de imagem válido.
    try:
        img = Image.open(io.BytesIO(conteudo))
        img.verify()
        formato = (img.format or '').lower()
    except Exception:
        flash("O arquivo enviado não é uma imagem válida.", "danger")
        return redirect(url_for('perfil'))

    if formato not in FORMATOS_AGEITOS:
        flash("Formato não suportado. Envie uma imagem JPEG, PNG ou WEBP.", "danger")
        return redirect(url_for('perfil'))

    extensao = 'jpg' if formato == 'jpeg' else formato
    object_key = f"perfis/{user_id}/{uuid.uuid4().hex}.{extensao}"
    content_type = f"image/{formato}"

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT foto_key FROM perfis WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        foto_antiga = row['foto_key'] if row else None

        init_minio_bucket()  # garante o bucket mesmo se o MinIO subiu depois do web
        minio_client.put_object(
            MINIO_BUCKET, object_key, io.BytesIO(conteudo),
            length=len(conteudo), content_type=content_type
        )

        cursor.execute("""
            INSERT INTO perfis (user_id, nome_exibicao, bio, foto_key)
            VALUES (%s, %s, '', %s)
            ON DUPLICATE KEY UPDATE foto_key = VALUES(foto_key)
        """, (user_id, user['username'], object_key))
        db.commit()
        cursor.close()
        db.close()

        if foto_antiga:
            try:
                minio_client.remove_object(MINIO_BUCKET, foto_antiga)
            except Exception as e:
                print(f"Aviso: não foi possível remover a foto antiga '{foto_antiga}': {e}")

        log_event(user['user_id'], 'upload_foto_perfil')
        flash("Foto de perfil atualizada!", "success")
    except S3Error as e:
        print(f"Erro MinIO ao enviar foto: {e}")
        flash("Erro ao enviar a imagem pro armazenamento. Tente novamente.", "danger")
    except Exception as e:
        print(f"Erro ao salvar foto de perfil: {e}")
        flash("Erro ao atualizar a foto de perfil.", "danger")

    return redirect(url_for('perfil'))


# =====================================================================
# StudyMatch — domínio: grupos de estudo (recurso principal do negócio)
# =====================================================================
PAPEIS = ("admin", "lider", "estudante")
DIAS_SEMANA = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
MODALIDADES = ("online", "presencial")

_SQL_GRUPO = """
    SELECT g.*, d.nome AS disciplina_nome,
           (SELECT COUNT(*) FROM grupo_membros m WHERE m.grupo_id = g.id) AS membros
    FROM grupos g JOIN disciplinas d ON d.id = g.disciplina_id
"""


class ErroNegocio(Exception):
    """Erro com status HTTP, usado igualmente pela API (JSON) e pelas telas (HTML)."""
    def __init__(self, status, mensagem, codigo=None):
        super().__init__(mensagem)
        self.status, self.mensagem, self.codigo = status, mensagem, codigo


def papel_de(user):
    """'usuario' era o papel do projeto anterior: vale como 'estudante'."""
    role = (user or {}).get('role', 'estudante')
    return 'estudante' if role == 'usuario' else role


def _hhmm(valor):
    if isinstance(valor, datetime.timedelta):
        total = int(valor.total_seconds())
        return f"{total // 3600:02d}:{(total % 3600) // 60:02d}"
    if isinstance(valor, datetime.time):
        return valor.strftime("%H:%M")
    return str(valor)[:5]


def grupo_para_dict(row):
    return {
        "id": row["id"],
        "lider_id": row["lider_id"],
        "disciplina_id": row["disciplina_id"],
        "disciplina": row.get("disciplina_nome"),
        "titulo": row["titulo"],
        "descricao": row.get("descricao") or "",
        "dia_semana": int(row["dia_semana"]),
        "dia_semana_nome": DIAS_SEMANA[int(row["dia_semana"]) % 7],
        "horario_inicio": _hhmm(row["horario_inicio"]),
        "horario_fim": _hhmm(row["horario_fim"]),
        "vagas": int(row["vagas"]),
        "membros": int(row.get("membros") or 0),
        "modalidade": row["modalidade"],
        "foto_url": gerar_url_foto(row.get("foto_key")),
    }


def _consulta(sql, params=(), um=False):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(sql, params)
    res = cursor.fetchone() if um else cursor.fetchall()
    cursor.close()
    db.close()
    return res


def carregar_grupo(grupo_id):
    return _consulta(_SQL_GRUPO + " WHERE g.id = %s", (grupo_id,), um=True)


def listar_grupos(user):
    """Cada papel enxerga só o que é seu: admin vê tudo, líder os próprios, estudante os que participa."""
    papel = papel_de(user)
    if papel == 'admin':
        rows = _consulta(_SQL_GRUPO + " ORDER BY g.id DESC")
    elif papel == 'lider':
        rows = _consulta(_SQL_GRUPO + " WHERE g.lider_id = %s ORDER BY g.id DESC", (user['user_id'],))
    else:
        rows = _consulta(_SQL_GRUPO + " WHERE g.id IN (SELECT grupo_id FROM grupo_membros WHERE user_id = %s)"
                         " ORDER BY g.id DESC", (user['user_id'],))
    return [grupo_para_dict(r) for r in rows]


def listar_disciplinas():
    try:
        return _consulta("SELECT id, codigo, nome FROM disciplinas ORDER BY nome")
    except Exception as e:
        print(f"Erro ao listar disciplinas: {e}")
        return []


def contar_grupos_do_lider(user_id):
    row = _consulta("SELECT COUNT(*) AS total FROM grupos WHERE lider_id = %s", (user_id,), um=True)
    return int(row['total']) if row else 0


def eh_membro(grupo_id, user_id):
    return bool(_consulta("SELECT 1 AS x FROM grupo_membros WHERE grupo_id = %s AND user_id = %s",
                          (grupo_id, user_id), um=True))


def exigir_papel_escrita(user, acao):
    if papel_de(user) not in ('admin', 'lider'):
        log_event(user['user_id'], f'403_{acao}_grupo_negado')
        raise ErroNegocio(403, "Seu papel não permite esta ação. Só líderes de grupo e admins.", "papel_sem_permissao")


def exigir_dono(user, grupo, acao):
    """Isolamento: só o líder dono (ou admin) altera o grupo. Outro usuário recebe 403."""
    exigir_papel_escrita(user, acao)
    if papel_de(user) != 'admin' and int(grupo['lider_id']) != int(user['user_id']):
        log_event(user['user_id'], f'403_{acao}_grupo_negado:grupo_{grupo["id"]}')
        raise ErroNegocio(403, "Este grupo pertence a outro usuário.", "grupo_de_outro_usuario")


def obter_grupo_visivel(user, grupo_id):
    grupo = carregar_grupo(grupo_id)
    if not grupo:
        raise ErroNegocio(404, "Grupo não encontrado.")
    if papel_de(user) == 'admin' or int(grupo['lider_id']) == int(user['user_id']) \
            or eh_membro(grupo_id, user['user_id']):
        return grupo
    log_event(user['user_id'], f'403_acesso_grupo_alheio:grupo_{grupo_id}')
    raise ErroNegocio(403, "Este grupo pertence a outro usuário.", "grupo_de_outro_usuario")


def _validar_horario(valor, campo):
    try:
        h, m = str(valor).strip()[:5].split(':')
        h, m = int(h), int(m)
        if not (0 <= h < 24 and 0 <= m < 60):
            raise ValueError
        return f"{h:02d}:{m:02d}"
    except Exception:
        raise ErroNegocio(400, f"{campo} inválido. Use HH:MM.")


def validar_dados_grupo(dados):
    dados = dados or {}
    titulo = (dados.get('titulo') or '').strip()
    if not 3 <= len(titulo) <= 120:
        raise ErroNegocio(400, "O título deve ter de 3 a 120 caracteres.")
    descricao = (dados.get('descricao') or '').strip()
    if len(descricao) > 500:
        raise ErroNegocio(400, "A descrição pode ter no máximo 500 caracteres.")
    try:
        disciplina_id = int(dados.get('disciplina_id'))
        dia = int(dados.get('dia_semana'))
        vagas = int(dados.get('vagas', 5))
    except (TypeError, ValueError):
        raise ErroNegocio(400, "Disciplina, dia da semana e vagas devem ser números.")
    if not 0 <= dia <= 6:
        raise ErroNegocio(400, "Dia da semana deve ir de 0 (domingo) a 6 (sábado).")
    if not 2 <= vagas <= 50:
        raise ErroNegocio(400, "Vagas deve ficar entre 2 e 50.")
    modalidade = (dados.get('modalidade') or 'online').strip().lower()
    if modalidade not in MODALIDADES:
        raise ErroNegocio(400, "Modalidade deve ser 'online' ou 'presencial'.")
    inicio = _validar_horario(dados.get('horario_inicio'), "Horário de início")
    fim = _validar_horario(dados.get('horario_fim'), "Horário de término")
    if fim <= inicio:
        raise ErroNegocio(400, "O horário de término deve ser depois do início.")
    if not _consulta("SELECT id FROM disciplinas WHERE id = %s", (disciplina_id,), um=True):
        raise ErroNegocio(400, "Disciplina inexistente.")
    return {"titulo": titulo, "descricao": descricao, "disciplina_id": disciplina_id, "dia_semana": dia,
            "horario_inicio": inicio, "horario_fim": fim, "vagas": vagas, "modalidade": modalidade}


def criar_grupo(user, dados):
    exigir_papel_escrita(user, 'criar')
    if papel_de(user) == 'lider' and not usuario_e_premium(user['user_id']) \
            and contar_grupos_do_lider(user['user_id']) >= GRUPOS_LIMITE_GRATIS:
        log_event(user['user_id'], 'limite_grupos_gratis_atingido')
        raise ErroNegocio(403, f"O plano grátis permite {GRUPOS_LIMITE_GRATIS} grupo(s). "
                               "Assine o StudyMatch Pro para criar quantos quiser.", "limite_plano_gratis")
    d = validar_dados_grupo(dados)
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO grupos (lider_id, disciplina_id, titulo, descricao, dia_semana,
                               horario_inicio, horario_fim, vagas, modalidade)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (user['user_id'], d['disciplina_id'], d['titulo'], d['descricao'], d['dia_semana'],
         d['horario_inicio'], d['horario_fim'], d['vagas'], d['modalidade']))
    grupo_id = cursor.lastrowid
    db.commit(); cursor.close(); db.close()
    log_event(user['user_id'], f'grupo_criado:grupo_{grupo_id}')
    return carregar_grupo(grupo_id)


def atualizar_grupo(user, grupo_id, dados):
    grupo = carregar_grupo(grupo_id)
    if not grupo:
        raise ErroNegocio(404, "Grupo não encontrado.")
    exigir_dono(user, grupo, 'editar')
    d = validar_dados_grupo(dados)
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """UPDATE grupos SET disciplina_id=%s, titulo=%s, descricao=%s, dia_semana=%s,
                             horario_inicio=%s, horario_fim=%s, vagas=%s, modalidade=%s WHERE id=%s""",
        (d['disciplina_id'], d['titulo'], d['descricao'], d['dia_semana'], d['horario_inicio'],
         d['horario_fim'], d['vagas'], d['modalidade'], grupo_id))
    db.commit(); cursor.close(); db.close()
    log_event(user['user_id'], f'grupo_editado:grupo_{grupo_id}')
    return carregar_grupo(grupo_id)


def remover_grupo(user, grupo_id):
    grupo = carregar_grupo(grupo_id)
    if not grupo:
        raise ErroNegocio(404, "Grupo não encontrado.")
    exigir_dono(user, grupo, 'excluir')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM grupos WHERE id = %s", (grupo_id,))
    db.commit(); cursor.close(); db.close()
    if grupo.get('foto_key'):
        try:
            minio_client.remove_object(MINIO_BUCKET, grupo['foto_key'])
        except Exception as e:
            print(f"Aviso: não foi possível remover a foto do grupo: {e}")
    log_event(user['user_id'], f'grupo_removido:grupo_{grupo_id}')


def salvar_foto_grupo(user, grupo_id, arquivo):
    """Upload da capa do grupo no MinIO, ligada ao registro certo (grupos.foto_key)."""
    grupo = carregar_grupo(grupo_id)
    if not grupo:
        raise ErroNegocio(404, "Grupo não encontrado.")
    exigir_dono(user, grupo, 'foto')
    if not arquivo or arquivo.filename == '':
        raise ErroNegocio(400, "Selecione uma imagem para enviar.")
    conteudo = arquivo.read()
    if len(conteudo) > MAX_FOTO_SIZE_BYTES:
        raise ErroNegocio(400, "Imagem maior que o limite de 2 MB.")
    try:
        img = Image.open(io.BytesIO(conteudo))
        img.verify()
        formato = (img.format or '').lower()
    except Exception:
        raise ErroNegocio(400, "O arquivo enviado não é uma imagem válida.")
    if formato not in FORMATOS_AGEITOS:
        raise ErroNegocio(400, "Formato não suportado. Envie JPEG, PNG ou WEBP.")
    chave = f"grupos/{grupo_id}/{uuid.uuid4().hex}.{'jpg' if formato == 'jpeg' else formato}"
    try:
        init_minio_bucket()
        minio_client.put_object(MINIO_BUCKET, chave, io.BytesIO(conteudo),
                                length=len(conteudo), content_type=f"image/{formato}")
    except Exception as e:
        print(f"Erro MinIO ao enviar capa do grupo: {e}")
        raise ErroNegocio(502, "Erro ao enviar a imagem para o armazenamento.")
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE grupos SET foto_key = %s WHERE id = %s", (chave, grupo_id))
    db.commit(); cursor.close(); db.close()
    if grupo.get('foto_key'):
        try:
            minio_client.remove_object(MINIO_BUCKET, grupo['foto_key'])
        except Exception as e:
            print(f"Aviso: não foi possível remover a capa antiga: {e}")
    log_event(user['user_id'], f'foto_grupo_enviada:grupo_{grupo_id}')
    return carregar_grupo(grupo_id)


def _dados_requisicao():
    return request.get_json(silent=True) or request.form.to_dict()


# ---------------- API REST (JSON) ----------------
def _api(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Não autenticado."}), 401
        try:
            return fn(user, *args, **kwargs)
        except ErroNegocio as e:
            return jsonify({"error": e.mensagem, "codigo": e.codigo}), e.status
    return wrapper


@app.route('/api/grupos', methods=['GET', 'POST'])
@_api
def api_grupos(user):
    if request.method == 'POST':
        return jsonify(grupo_para_dict(criar_grupo(user, _dados_requisicao()))), 201
    return jsonify([g for g in listar_grupos(user)])


@app.route('/api/grupos/<int:grupo_id>', methods=['GET', 'PUT', 'DELETE'])
@_api
def api_grupo(user, grupo_id):
    if request.method == 'PUT':
        return jsonify(grupo_para_dict(atualizar_grupo(user, grupo_id, _dados_requisicao())))
    if request.method == 'DELETE':
        remover_grupo(user, grupo_id)
        return '', 204
    return jsonify(grupo_para_dict(obter_grupo_visivel(user, grupo_id)))


@app.route('/api/grupos/<int:grupo_id>/foto', methods=['POST'])
@_api
def api_grupo_foto(user, grupo_id):
    return jsonify(grupo_para_dict(salvar_foto_grupo(user, grupo_id, request.files.get('foto'))))


@app.route('/api/disciplinas', methods=['GET'])
@_api
def api_disciplinas(user):
    return jsonify(listar_disciplinas())


# ---------------- Telas (HTML) ----------------
def _pagina(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        try:
            return fn(user, *args, **kwargs)
        except ErroNegocio as e:
            if e.status in (403, 404) and e.codigo != 'limite_plano_gratis':
                abort(e.status)
            flash(e.mensagem, 'danger')
            return redirect(request.referrer or url_for('grupos_lista'))
    return wrapper


@app.route('/')
def landing():
    """Página pública (sem login) com a proposta de valor e o botão de criar conta."""
    if get_current_user():
        return redirect(url_for('grupos_lista'))
    return render_template('landing.html', limite=GRUPOS_LIMITE_GRATIS)


@app.route('/grupos')
@_pagina
def grupos_lista(user):
    papel = papel_de(user)
    try:
        grupos = listar_grupos(user)
    except Exception as e:
        print(f"Erro ao listar grupos: {e}")
        grupos = []
    return render_template('grupos.html', grupos=grupos, usuario=user['username'], role=papel,
                           premium=usuario_e_premium(user['user_id']), limite=GRUPOS_LIMITE_GRATIS,
                           pode_criar=papel in ('admin', 'lider'))


@app.route('/grupos/novo', methods=['GET', 'POST'])
@_pagina
def grupo_novo(user):
    if request.method == 'POST':
        try:
            grupo = criar_grupo(user, request.form.to_dict())
        except ErroNegocio as e:
            if e.status != 400:
                raise
            flash(e.mensagem, 'danger')
            return render_template('grupo_form.html', grupo=request.form, disciplinas=listar_disciplinas(),
                                   usuario=user['username'], role=papel_de(user), editando=False,
                                   dias=DIAS_SEMANA)
        flash('Grupo criado!', 'success')
        return redirect(url_for('grupo_detalhe', grupo_id=grupo['id']))
    exigir_papel_escrita(user, 'criar')
    return render_template('grupo_form.html', grupo={}, disciplinas=listar_disciplinas(),
                           usuario=user['username'], role=papel_de(user), editando=False, dias=DIAS_SEMANA)


@app.route('/grupos/<int:grupo_id>')
@_pagina
def grupo_detalhe(user, grupo_id):
    grupo = grupo_para_dict(obter_grupo_visivel(user, grupo_id))
    pode_editar = papel_de(user) == 'admin' or (papel_de(user) == 'lider' and grupo['lider_id'] == user['user_id'])
    return render_template('grupo_detalhe.html', grupo=grupo, usuario=user['username'],
                           role=papel_de(user), pode_editar=pode_editar)


@app.route('/grupos/<int:grupo_id>/editar', methods=['GET', 'POST'])
@_pagina
def grupo_editar(user, grupo_id):
    grupo = carregar_grupo(grupo_id)
    if not grupo:
        raise ErroNegocio(404, "Grupo não encontrado.")
    exigir_dono(user, grupo, 'editar')
    if request.method == 'POST':
        try:
            atualizar_grupo(user, grupo_id, request.form.to_dict())
        except ErroNegocio as e:
            if e.status != 400:
                raise
            flash(e.mensagem, 'danger')
            return render_template('grupo_form.html', grupo=dict(request.form, id=grupo_id),
                                   disciplinas=listar_disciplinas(), usuario=user['username'],
                                   role=papel_de(user), editando=True, dias=DIAS_SEMANA)
        flash('Grupo atualizado!', 'success')
        return redirect(url_for('grupo_detalhe', grupo_id=grupo_id))
    return render_template('grupo_form.html', grupo=grupo_para_dict(grupo), disciplinas=listar_disciplinas(),
                           usuario=user['username'], role=papel_de(user), editando=True, dias=DIAS_SEMANA)


@app.route('/grupos/<int:grupo_id>/excluir', methods=['POST'])
@_pagina
def grupo_excluir(user, grupo_id):
    remover_grupo(user, grupo_id)
    flash('Grupo removido.', 'success')
    return redirect(url_for('grupos_lista'))


@app.route('/grupos/<int:grupo_id>/foto', methods=['POST'])
@_pagina
def grupo_foto(user, grupo_id):
    salvar_foto_grupo(user, grupo_id, request.files.get('foto'))
    flash('Capa do grupo atualizada!', 'success')
    return redirect(url_for('grupo_detalhe', grupo_id=grupo_id))


@app.route('/perfil')
def perfil():
    """Perfil do usuário logado: nome, bio, foto, plano e seus grupos."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    dados_perfil = get_or_create_perfil(user['user_id'], user['username'])
    try:
        meus_grupos = listar_grupos(user)
    except Exception as e:
        print(f"Erro ao buscar grupos do perfil: {e}")
        meus_grupos = []
    return render_template(
        'perfil.html',
        usuario=user['username'],
        role=papel_de(user),
        perfil=dados_perfil,
        foto_url=gerar_url_foto(dados_perfil.get('foto_key')),
        meu_user_id=user['user_id'],
        premium=usuario_e_premium(user['user_id']),
        limite_grupos=GRUPOS_LIMITE_GRATIS,
        meus_grupos=meus_grupos,
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
