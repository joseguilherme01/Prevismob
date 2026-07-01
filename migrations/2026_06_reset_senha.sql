-- ===========================================================================
-- Migração: recuperação de senha via e-mail
-- Acrescenta colunas para gerenciar o ciclo de vida do token de reset.
-- Idempotente: pode ser aplicada mais de uma vez.
-- ===========================================================================
--
-- MySQL 8.0.29+ suporta ALTER TABLE ... ADD COLUMN IF NOT EXISTS.
-- Para versões anteriores, o mesmo resultado é obtido no runtime da API,
-- que verifica INFORMATION_SCHEMA e adiciona as colunas apenas se ausentes.
-- ===========================================================================

ALTER TABLE usuarios
  ADD COLUMN IF NOT EXISTS reset_senha_token_hash VARCHAR(128) NULL DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS reset_senha_expira_em  DATETIME     NULL DEFAULT NULL;

CREATE INDEX IF NOT EXISTS ix_usuarios_reset_token ON usuarios (reset_senha_token_hash);
