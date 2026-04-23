-- ===========================================================================
-- Hardening: índice UNIQUE em email_verificacao_token_hash
-- ===========================================================================
-- Compatível com MySQL 5.7+ e 8.x (sem depender de IF [NOT] EXISTS em DDL).
-- É seguro executar em produção:
--   - NULL é aceito múltiplas vezes em UNIQUE no InnoDB (usuários sem token
--     pendente não conflitam).
--   - Se existir duplicata ativa (não deveria), o CREATE UNIQUE falha e
--     nenhuma alteração ocorre — resolva manualmente antes de reexecutar.
-- Idempotência é garantida via INFORMATION_SCHEMA dentro de um procedure.
-- ===========================================================================

DELIMITER //

DROP PROCEDURE IF EXISTS pr_prevismob_unique_verif_hash //
CREATE PROCEDURE pr_prevismob_unique_verif_hash()
BEGIN
    DECLARE has_unique INT DEFAULT 0;
    DECLARE has_legacy INT DEFAULT 0;
    DECLARE dup_count  INT DEFAULT 0;

    SELECT COUNT(*) INTO has_unique
      FROM INFORMATION_SCHEMA.STATISTICS
     WHERE TABLE_SCHEMA = DATABASE()
       AND TABLE_NAME = 'usuarios'
       AND COLUMN_NAME = 'email_verificacao_token_hash'
       AND NON_UNIQUE = 0;

    SELECT COUNT(*) INTO has_legacy
      FROM INFORMATION_SCHEMA.STATISTICS
     WHERE TABLE_SCHEMA = DATABASE()
       AND TABLE_NAME = 'usuarios'
       AND INDEX_NAME = 'ix_usuarios_email_verif_hash';

    IF has_unique = 0 THEN
        IF has_legacy > 0 THEN
            ALTER TABLE usuarios DROP INDEX ix_usuarios_email_verif_hash;
        END IF;

        SELECT COUNT(*) INTO dup_count FROM (
            SELECT email_verificacao_token_hash
              FROM usuarios
             WHERE email_verificacao_token_hash IS NOT NULL
             GROUP BY email_verificacao_token_hash
            HAVING COUNT(*) > 1
        ) d;

        IF dup_count = 0 THEN
            ALTER TABLE usuarios
                ADD UNIQUE INDEX ux_usuarios_email_verif_hash (email_verificacao_token_hash);
        END IF;
    END IF;
END //

DELIMITER ;

CALL pr_prevismob_unique_verif_hash();
DROP PROCEDURE IF EXISTS pr_prevismob_unique_verif_hash;
