-- ===========================================================================
-- Migração: verificação obrigatória de e-mail
-- Acrescenta colunas para gerenciar o ciclo de vida do token de verificação.
-- Idempotente: pode ser aplicada mais de uma vez.
-- ===========================================================================
--
-- MySQL 8.0.29+ suporta ALTER TABLE ... ADD COLUMN IF NOT EXISTS.
-- Para versões anteriores, o mesmo resultado é obtido no runtime da API,
-- que verifica INFORMATION_SCHEMA e adiciona as colunas apenas se ausentes.
-- ===========================================================================

ALTER TABLE usuarios
    ADD COLUMN IF NOT EXISTS email_verificacao_token_hash VARCHAR(128) NULL AFTER email_verificado_em,
    ADD COLUMN IF NOT EXISTS email_verificacao_expira_em  DATETIME     NULL AFTER email_verificacao_token_hash,
    ADD COLUMN IF NOT EXISTS email_verificacao_enviado_em DATETIME     NULL AFTER email_verificacao_expira_em;

-- Índice opcional para acelerar lookup por hash (não há unique pois o hash é curto por design):
CREATE INDEX IF NOT EXISTS ix_usuarios_email_verif_hash
    ON usuarios (email_verificacao_token_hash);
