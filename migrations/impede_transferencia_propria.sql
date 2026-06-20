-- Migração 001: Impede transferência de uma conta para ela mesma
-- Data: 2026-06-20
-- Contexto: sp_executar_transferencia (criada em Consultas.sql) não validava
--           se conta_origem == conta_destino, permitindo "transferências" sem
--           sentido para a própria conta.
--
-- Como aplicar:
--   1. Selecione o banco correto antes de rodar este arquivo:
--        USE Equipe567258;
--   2. Rode este script inteiro (ou via SOURCE migrations/001_impede_transferencia_propria.sql;)

USE Equipe567258;

DROP PROCEDURE IF EXISTS sp_executar_transferencia;

DELIMITER $$
CREATE PROCEDURE sp_executar_transferencia(
    IN p_conta_origem INT,
    IN p_conta_destino INT,
    IN p_valor REAL,
    IN p_num_trans_origem INT,
    IN p_num_trans_destino INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_conta_origem = p_conta_destino THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Conta de origem e destino não podem ser iguais.';
    END IF;

    START TRANSACTION;

    INSERT INTO Transacao (num_transacao, num_conta, tipo, data_hora, valor)
    VALUES (p_num_trans_origem, p_conta_origem, 'transferência', NOW(), p_valor);

    INSERT INTO Transacao (num_transacao, num_conta, tipo, data_hora, valor)
    VALUES (p_num_trans_destino, p_conta_destino, 'transferência', NOW(), p_valor);

    COMMIT;
END$$
DELIMITER ;
