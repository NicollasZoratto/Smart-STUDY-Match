-- Atividade 11: idempotência dos webhooks do Stripe.
-- Cada event.id é gravado uma única vez; se o Stripe reenviar, o app ignora o duplicado.
-- (As colunas plano/status/stripe_price_id/cancelar_no_fim da tabela assinaturas são
--  acrescentadas, de forma idempotente, por migrar_assinaturas() em app_principal/app.py.)
CREATE TABLE IF NOT EXISTS stripe_eventos (
    event_id VARCHAR(80) PRIMARY KEY,
    tipo VARCHAR(80) NOT NULL,
    processado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
