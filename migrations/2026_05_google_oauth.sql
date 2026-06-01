-- ===========================================================================
-- Migração: Google OAuth 2.0
-- Adiciona suporte a autenticação via Google Identity Services.
-- Idempotente: requer MySQL 8.0.29+ para IF NOT EXISTS em ADD COLUMN.
-- Para versões anteriores, a migração runtime em api.py aplica as mesmas
-- alterações via INFORMATION_SCHEMA antes de qualquer requisição.
-- ===========================================================================

-- google_id: identificador único e imutável da conta Google ("sub" do ID Token).
-- UNIQUE impede que uma mesma conta Google seja vinculada a dois usuários distintos.
-- NULL permite contas criadas pelo fluxo normal (email+senha) sem Google vinculado.
ALTER TABLE usuarios
    ADD COLUMN IF NOT EXISTS google_id  VARCHAR(128) NULL AFTER email,
    ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(512) NULL AFTER google_id;

-- Índice UNIQUE em google_id.
-- MySQL/InnoDB permite múltiplos NULLs em colunas UNIQUE, portanto usuários
-- sem Google vinculado não conflitam entre si.
CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_google_id
    ON usuarios (google_id);

-- senha_hash passa a aceitar NULL para usuários OAuth-only.
-- Contas normais continuam armazenando o hash bcrypt.
-- Usuários OAuth que tentarem login com senha receberão 401 (hash NULL
-- falha na verificação bcrypt normalmente — sem mudança de comportamento).
ALTER TABLE usuarios
    MODIFY COLUMN senha_hash VARCHAR(255) NULL;
