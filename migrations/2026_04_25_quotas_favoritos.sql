-- ===========================================================================
-- Migração: cota diária por tipo de usuário, histórico e favoritos
-- ---------------------------------------------------------------------------
-- - Permite previsões de visitantes (guest) controlados por guest_id
--   (UUID gerado pelo backend e persistido em cookie httpOnly).
-- - Adiciona flag is_favorita para que usuários autenticados favoritem
--   previsões e possam comparar/exportar.
-- - Captura o texto livre digitado pelo usuário (nome_predio_input) para
--   exibição em histórico sem depender de join com `condominios`.
-- - Cria índices para consulta de cota diária O(1).
--
-- Idempotente — pode ser aplicada mais de uma vez.
-- Reversão: remover as colunas e índices abaixo manualmente; valores
--           preexistentes em `avaliacoes` continuarão íntegros.
-- ===========================================================================

ALTER TABLE avaliacoes
    MODIFY COLUMN usuario_id BIGINT NULL;

ALTER TABLE avaliacoes
    ADD COLUMN IF NOT EXISTS guest_id          VARCHAR(64)  NULL AFTER usuario_id,
    ADD COLUMN IF NOT EXISTS is_favorita       TINYINT(1)   NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS nome_predio_input VARCHAR(255) NULL;

CREATE INDEX IF NOT EXISTS ix_avaliacoes_usuario_dia
    ON avaliacoes (usuario_id, criado_em);

CREATE INDEX IF NOT EXISTS ix_avaliacoes_guest_dia
    ON avaliacoes (guest_id, criado_em);

CREATE INDEX IF NOT EXISTS ix_avaliacoes_favoritas
    ON avaliacoes (usuario_id, is_favorita);
