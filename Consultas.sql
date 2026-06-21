USE Equipe567258;

DELIMITER $$

CREATE TRIGGER tg_funcionario_insert AFTER INSERT ON Funcionario
FOR EACH ROW
BEGIN
    UPDATE Agencia 
    SET sal_total = sal_total + NEW.salario 
    WHERE num_ag = NEW.num_ag;
END$$

CREATE TRIGGER tg_funcionario_delete AFTER DELETE ON Funcionario
FOR EACH ROW
BEGIN
    UPDATE Agencia 
    SET sal_total = sal_total - OLD.salario 
    WHERE num_ag = OLD.num_ag;
END$$

CREATE TRIGGER tg_funcionario_update AFTER UPDATE ON Funcionario
FOR EACH ROW
BEGIN
    UPDATE Agencia 
    SET sal_total = sal_total - OLD.salario 
    WHERE num_ag = OLD.num_ag;
    
    UPDATE Agencia 
    SET sal_total = sal_total + NEW.salario 
    WHERE num_ag = NEW.num_ag;
END$$

CREATE TRIGGER tg_atualizar_saldo_transacao AFTER INSERT ON Transacao
FOR EACH ROW
BEGIN
    DECLARE v_saldo REAL;
    DECLARE v_limite REAL;
    DECLARE v_tipo_conta VARCHAR(50);
    
    SELECT saldo, limite_credito, tipo_conta 
    INTO v_saldo, v_limite, v_tipo_conta 
    FROM Conta 
    WHERE num_conta = NEW.num_conta;
    
    IF NEW.tipo IN ('saque', 'pagamento', 'transferência', 'PIX') THEN
        IF v_tipo_conta = 'conta especial' THEN
            IF (v_saldo - NEW.valor) < (-IFNULL(v_limite, 0)) THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Saldo insuficiente. Limite de crédito excedido.';
            END IF;
        ELSE
            IF (v_saldo - NEW.valor) < 0 THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Saldo insuficiente para realizar a transação.';
            END IF;
        END IF;
        
        UPDATE Conta SET saldo = saldo - NEW.valor WHERE num_conta = NEW.num_conta;
        
    ELSEIF NEW.tipo IN ('depósito', 'estorno') THEN
        UPDATE Conta SET saldo = saldo + NEW.valor WHERE num_conta = NEW.num_conta;
    END IF;
END$$

-- Modificado em 2026-06-20: Adicionada assinatura de 6 parâmetros e validação de titularidade/permissão diretamente no banco de dados.
DROP PROCEDURE IF EXISTS sp_executar_transferencia;

DELIMITER $$
CREATE PROCEDURE sp_executar_transferencia(
    IN p_username_solicitante VARCHAR(50),
    IN p_conta_origem INT,
    IN p_conta_destino INT,
    IN p_valor REAL,
    IN p_num_trans_origem INT,
    IN p_num_trans_destino INT
)
BEGIN
    DECLARE v_role VARCHAR(20);
    DECLARE v_cpf CHAR(11);
    DECLARE v_eh_titular INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    -- 1. Identificar quem está solicitando e o seu papel
    SELECT role, cpf INTO v_role, v_cpf
    FROM Usuario
    WHERE username = p_username_solicitante;

    IF v_role IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Usuário solicitante não encontrado.';
    END IF;

    -- 2. Restringir cliente a movimentar apenas suas próprias contas de titularidade
    IF v_role = 'client' THEN
        SELECT COUNT(*) INTO v_eh_titular
        FROM Titularidade_Conta
        WHERE num_conta = p_conta_origem AND cpf_cliente = v_cpf;

        IF v_eh_titular = 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Você não tem permissão para movimentar essa conta de origem.';
        END IF;
    END IF;

    -- 3. Impedir transferências para a própria conta de origem
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

CREATE VIEW v_contas_gerente AS
SELECT 
    c.matricula_gerente,
    c.num_conta,
    c.tipo_conta,
    c.saldo,
    cl.cpf,
    cl.nome_completo
FROM Conta c
JOIN Titularidade_Conta tc ON c.num_conta = tc.num_conta
JOIN Cliente cl ON tc.cpf_cliente = cl.cpf;

CREATE VIEW v_extrato_completo AS
SELECT 
    num_conta,
    num_transacao,
    tipo,
    data_hora,
    valor
FROM Transacao;

SET @busca_agencia = '1';
SET @busca_cpf = '01234567890';
SET @busca_cidade = 'Sobral';

SELECT f.nome_completo, f.cargo, f.tipo_logradouro, f.nome_logradouro, f.numero, f.cidade, f.salario, COUNT(d.nome_completo) AS dependentes
FROM Funcionario f
LEFT JOIN Dependente d ON f.matricula = d.matricula_func
WHERE f.num_ag = @busca_agencia
GROUP BY f.matricula
ORDER BY f.nome_completo ASC;

SELECT cl.nome_completo, cl.cpf, c.num_conta, c.tipo_conta
FROM Cliente cl
JOIN Titularidade_Conta tc ON cl.cpf = tc.cpf_cliente
JOIN Conta c ON tc.num_conta = c.num_conta
WHERE c.num_ag = @busca_agencia
ORDER BY c.tipo_conta;

SELECT num_conta, saldo, limite_credito
FROM Conta
WHERE tipo_conta = 'conta especial' AND saldo < 0
ORDER BY saldo ASC;

SELECT num_conta, saldo
FROM Conta
WHERE tipo_conta = 'poupança' AND saldo > 0
ORDER BY saldo DESC;

SELECT num_conta, COUNT(id_transacao) AS total FROM Transacao 
WHERE data_hora >= NOW() - INTERVAL 7 DAY AND num_conta IN (SELECT num_conta FROM Conta WHERE tipo_conta = 'conta-corrente')
GROUP BY num_conta ORDER BY total DESC;

SELECT num_conta, COUNT(id_transacao) AS total FROM Transacao 
WHERE data_hora >= NOW() - INTERVAL 30 DAY AND num_conta IN (SELECT num_conta FROM Conta WHERE tipo_conta = 'conta-corrente')
GROUP BY num_conta ORDER BY total DESC;

SELECT num_conta, COUNT(id_transacao) AS total FROM Transacao 
WHERE data_hora >= NOW() - INTERVAL 365 DAY AND num_conta IN (SELECT num_conta FROM Conta WHERE tipo_conta = 'conta-corrente')
GROUP BY num_conta ORDER BY total DESC;

SELECT num_conta, SUM(valor) AS volume FROM Transacao WHERE data_hora >= NOW() - INTERVAL 7 DAY GROUP BY num_conta ORDER BY volume DESC;
SELECT num_conta, SUM(valor) AS volume FROM Transacao WHERE data_hora >= NOW() - INTERVAL 30 DAY GROUP BY num_conta ORDER BY volume DESC;
SELECT num_conta, SUM(valor) AS volume FROM Transacao WHERE data_hora >= NOW() - INTERVAL 365 DAY GROUP BY num_conta ORDER BY volume DESC;

SELECT c.num_conta, c.tipo_conta, a.nome_ag, f.nome_completo AS gerente, c.saldo
FROM Conta c
JOIN Titularidade_Conta tc ON c.num_conta = tc.num_conta
JOIN Agencia a ON c.num_ag = a.num_ag
JOIN Funcionario f ON c.matricula_gerente = f.matricula
WHERE tc.cpf_cliente = @busca_cpf;

SELECT DISTINCT cl.nome_completo, cl.cpf
FROM Titularidade_Conta tc1
JOIN Titularidade_Conta tc2 ON tc1.num_conta = tc2.num_conta AND tc1.cpf_cliente <> tc2.cpf_cliente
JOIN Cliente cl ON tc2.cpf_cliente = cl.cpf
WHERE tc1.cpf_cliente = @busca_cpf;

SELECT t.num_conta, COUNT(t.id_transacao) AS total 
FROM Transacao t
JOIN Titularidade_Conta tc ON t.num_conta = tc.num_conta
JOIN Conta c ON t.num_conta = c.num_conta
WHERE tc.cpf_cliente = @busca_cpf AND c.tipo_conta = 'conta-corrente' AND t.data_hora >= NOW() - INTERVAL 7 DAY
GROUP BY t.num_conta ORDER BY total DESC;

SELECT t.num_conta, SUM(t.valor) AS volume 
FROM Transacao t
JOIN Titularidade_Conta tc ON t.num_conta = tc.num_conta
WHERE tc.cpf_cliente = @busca_cpf AND t.data_hora >= NOW() - INTERVAL 7 DAY
GROUP BY t.num_conta ORDER BY volume DESC;

SELECT nome_completo, tipo_logradouro, nome_logradouro, numero, bairro, TIMESTAMPDIFF(YEAR, data_nascimento, CURDATE()) AS idade
FROM Cliente
WHERE cidade = @busca_cidade
ORDER BY idade ASC;

SELECT f.nome_completo, f.cargo, f.salario, a.nome_ag
FROM Funcionario f
JOIN Agencia a ON f.num_ag = a.num_ag
WHERE a.cidade = @busca_cidade
ORDER BY a.num_ag, f.cargo, f.salario DESC;

SELECT nome_ag, sal_total
FROM Agencia
WHERE cidade = @busca_cidade
ORDER BY sal_total DESC;