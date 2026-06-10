CREATE DATABASE Equipe567258;
USE Equipe567258;

CREATE TABLE Agencia (
    num_ag INT AUTO_INCREMENT PRIMARY KEY,
    nome_ag VARCHAR(100) NOT NULL,
    sal_total REAL DEFAULT 0.00,
    cidade VARCHAR(100) NOT NULL
);

CREATE TABLE Funcionario (
    matricula VARCHAR(20) PRIMARY KEY,
    nome_completo VARCHAR(150) NOT NULL,
    senha VARCHAR(255) NOT NULL,
    tipo_logradouro VARCHAR(30),
    nome_logradouro VARCHAR(100),
    numero VARCHAR(10),
    complemento VARCHAR(50),
    bairro VARCHAR(50),
    cidade VARCHAR(100),
    estado CHAR(2),
    cep CHAR(8),
    cargo ENUM('gerente', 'atendente', 'caixa') NOT NULL,
    genero ENUM('masculino', 'feminino', 'não-binário') NOT NULL,
    data_nascimento DATE NOT NULL,
    salario REAL NOT NULL CHECK (salario >= 2286.00),
    num_ag INT NOT NULL,
    FOREIGN KEY (num_ag) REFERENCES Agencia(num_ag)
);

CREATE TABLE Dependente (
    nome_completo VARCHAR(150) NOT NULL,
    matricula_func VARCHAR(20) NOT NULL,
    data_nascimento DATE NOT NULL,
    parentesco ENUM('filho(a)', 'cônjuge', 'genitor(a)') NOT NULL,
    idade INT,
    PRIMARY KEY (matricula_func, nome_completo),
    FOREIGN KEY (matricula_func) REFERENCES Funcionario(matricula)
);

CREATE TABLE Cliente (
    cpf CHAR(11) PRIMARY KEY,
    nome_completo VARCHAR(150) NOT NULL,
    rg_numero VARCHAR(15) NOT NULL,
    rg_orgao VARCHAR(20) NOT NULL,
    rg_uf CHAR(2) NOT NULL,
    data_nascimento DATE NOT NULL,
    tipo_logradouro VARCHAR(30),
    nome_logradouro VARCHAR(100),
    numero VARCHAR(10),
    complemento VARCHAR(50),
    bairro VARCHAR(50),
    cep CHAR(8),
    cidade VARCHAR(100),
    estado CHAR(2)
);

CREATE TABLE Telefone_Cliente (
    cpf_cliente CHAR(11) NOT NULL,
    telefone VARCHAR(11) NOT NULL,
    descricao VARCHAR(30),
    PRIMARY KEY (cpf_cliente, telefone),
    FOREIGN KEY (cpf_cliente) REFERENCES Cliente(cpf)
);

CREATE TABLE Email_Cliente (
    cpf_cliente CHAR(11) NOT NULL,
    email VARCHAR(254) NOT NULL,
    descricao VARCHAR(30),
    PRIMARY KEY (cpf_cliente, email),
    FOREIGN KEY (cpf_cliente) REFERENCES Cliente(cpf)
);

CREATE TABLE Conta (
    num_conta INT PRIMARY KEY,
    saldo REAL DEFAULT 0.00,
    senha VARCHAR(255) NOT NULL,
    tipo_conta ENUM('conta-corrente', 'poupança', 'conta especial') NOT NULL,
    taxa_juros REAL,
    limite_credito REAL,
    data_aniversario_contrato DATE,
    num_ag INT NOT NULL,
    matricula_gerente VARCHAR(20) NOT NULL,
    FOREIGN KEY (num_ag) REFERENCES Agencia(num_ag),
    FOREIGN KEY (matricula_gerente) REFERENCES Funcionario(matricula)
);

CREATE TABLE Titularidade_Conta (
    num_conta INT NOT NULL,
    cpf_cliente CHAR(11) NOT NULL,
    tipo_titular ENUM('1º titular', '2º titular') NOT NULL,
    PRIMARY KEY (num_conta, cpf_cliente),
    FOREIGN KEY (num_conta) REFERENCES Conta(num_conta),
    FOREIGN KEY (cpf_cliente) REFERENCES Cliente(cpf)
);

CREATE TABLE Transacao (
    id_transacao INT AUTO_INCREMENT PRIMARY KEY,
    num_transacao INT NOT NULL,
    num_conta INT NOT NULL,
    tipo ENUM('saque', 'depósito', 'pagamento', 'estorno', 'transferência', 'PIX') NOT NULL,
    data_hora DATETIME NOT NULL,
    valor REAL NOT NULL,
    UNIQUE (num_conta, num_transacao),
    FOREIGN KEY (num_conta) REFERENCES Conta(num_conta)
);

INSERT INTO Agencia (nome_ag, cidade, sal_total) VALUES
('Agência Central', 'Sobral', 0.00),
('Agência Boulevard', 'Fortaleza', 0.00);

INSERT INTO Funcionario (matricula, nome_completo, senha, tipo_logradouro, nome_logradouro, numero, complemento, bairro, cidade, estado, cep, cargo, genero, data_nascimento, salario, num_ag) VALUES
('MAT1001', 'Fernando Alves', 'a1b2c3d4e5f6', 'Rua', 'Menino Deus', '15', 'Apto 101', 'Centro', 'Sobral', 'CE', '62010000', 'gerente', 'masculino', '1980-05-20', 6500.00, 1),
('MAT1002', 'Lara Mendes', 'f6e5d4c3b2a1', 'Avenida', 'Dom José', '1020', '', 'Derby', 'Sobral', 'CE', '62042000', 'caixa', 'feminino', '1995-10-12', 3200.00, 1);

INSERT INTO Dependente (nome_completo, matricula_func, data_nascimento, parentesco, idade) VALUES
('Lucas Alves', 'MAT1001', '2010-03-15', 'filho(a)', 16);

INSERT INTO Cliente (cpf, nome_completo, rg_numero, rg_orgao, rg_uf, data_nascimento, tipo_logradouro, nome_logradouro, numero, complemento, bairro, cep, cidade, estado) VALUES
('01234567890', 'Camila Rocha', '123456789', 'SSP', 'CE', '1988-07-25', 'Rua', 'Oriano Mendes', '400', 'Casa 2', 'Centro', '62010000', 'Sobral', 'CE');

INSERT INTO Telefone_Cliente (cpf_cliente, telefone, descricao) VALUES
('01234567890', '88991234567', 'celular1');

INSERT INTO Email_Cliente (cpf_cliente, email, descricao) VALUES
('01234567890', 'camila.rocha@email.com', 'particular');

INSERT INTO Conta (num_conta, saldo, senha, tipo_conta, taxa_juros, limite_credito, data_aniversario_contrato, num_ag, matricula_gerente) VALUES
(50501, 1200.50, 'hashsenha123', 'conta-corrente', NULL, NULL, '2020-01-15', 1, 'MAT1001');

INSERT INTO Titularidade_Conta (num_conta, cpf_cliente, tipo_titular) VALUES
(50501, '01234567890', '1º titular');

INSERT INTO Transacao (num_transacao, num_conta, tipo, data_hora, valor) VALUES
(1, 50501, 'depósito', '2026-06-09 10:30:00', 1200.50);