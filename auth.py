"""Autenticação, cadastro e gestão de usuários (login, hash de senha, promoção de cargo)."""
import hashlib

import mysql.connector
import streamlit as st

from database import conectar_banco
from utils import limpar_cpf


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def inicializar_autenticacao(conexao):
    """Cria a tabela Usuario (se não existir) e sincroniza Funcionario/Cliente nela."""
    if not conexao:
        return
    cursor = conexao.cursor()
    # Verificar se a tabela Usuario existe
    try:
        cursor.execute("SELECT 1 FROM Usuario LIMIT 1")
        cursor.fetchall()
        
        # Garantir que o administrador fixo existe mesmo se a tabela já foi criada anteriormente
        cursor.execute("SELECT 1 FROM Usuario WHERE username = 'Admin'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO Usuario (username, nome, senha, role) VALUES (%s, %s, %s, %s)",
                ('Admin', 'Administrador DBA', hash_senha('Root'), 'admin')
            )
            conexao.commit()
    except mysql.connector.Error:
        # Tabela não existe, criar
        try:
            cursor.execute("""
                CREATE TABLE Usuario (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    nome VARCHAR(150) NOT NULL,
                    senha VARCHAR(255) NOT NULL,
                    role ENUM('client', 'atendente', 'caixa', 'gerente', 'admin') NOT NULL DEFAULT 'client',
                    cpf CHAR(11) UNIQUE NULL,
                    matricula VARCHAR(20) UNIQUE NULL,
                    FOREIGN KEY (cpf) REFERENCES Cliente(cpf) ON DELETE CASCADE,
                    FOREIGN KEY (matricula) REFERENCES Funcionario(matricula) ON DELETE CASCADE
                )
            """)
            conexao.commit()

            # Sincronizar funcionários existentes
            cursor.execute("SELECT matricula, nome_completo, senha, cargo FROM Funcionario")
            funcs = cursor.fetchall()
            for matricula, nome, senha, cargo in funcs:
                # O cargo 'gerente' da tabela Funcionario já corresponde 1:1 ao
                # role 'gerente'. 'atendente' e 'caixa' também mapeiam direto.
                # O role 'admin' nunca é atribuído automaticamente aqui — só
                # via promoção manual (ver promover_usuario).
                role = cargo  # 'gerente', 'atendente' ou 'caixa'
                cursor.execute(
                    "INSERT IGNORE INTO Usuario (username, nome, senha, role, matricula) VALUES (%s, %s, %s, %s, %s)",
                    (matricula, nome, senha, role, matricula)
                )

            # Sincronizar clientes existentes
            cursor.execute("""
                SELECT c.cpf, c.nome_completo, co.senha
                FROM Cliente c
                LEFT JOIN Titularidade_Conta tc ON c.cpf = tc.cpf_cliente
                LEFT JOIN Conta co ON tc.num_conta = co.num_conta
            """)
            clients = cursor.fetchall()
            for cpf, nome, senha_conta in clients:
                senha = senha_conta if senha_conta else 'hashsenha123'
                cursor.execute(
                    "INSERT IGNORE INTO Usuario (username, nome, senha, role, cpf) VALUES (%s, %s, %s, %s, %s)",
                    (cpf, nome, senha, 'client', cpf)
                )

            # Inserir o administrador fixo no banco recém-criado
            cursor.execute(
                "INSERT IGNORE INTO Usuario (username, nome, senha, role) VALUES (%s, %s, %s, %s)",
                ('Admin', 'Administrador DBA', hash_senha('Root'), 'admin')
            )

            conexao.commit()
        except mysql.connector.Error as err:
            st.error(f"Erro ao inicializar banco de dados de autenticação: {err}")
    finally:
        cursor.close()


def obter_agencia_funcionario(matricula):
    """Retorna o num_ag do funcionário, ou None se não encontrado."""
    if not matricula:
        return None
    conexao = conectar_banco()
    num_ag = None
    if conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("SELECT num_ag FROM Funcionario WHERE matricula = %s", (matricula,))
            res = cursor.fetchone()
            num_ag = res[0] if res else None
        except mysql.connector.Error as err:
            st.error(f"Erro ao buscar agência do funcionário: {err}")
        finally:
            cursor.close()
            conexao.close()
    return num_ag


def conta_pertence_a_agencia(num_conta, num_ag):
    """Verifica se a conta informada pertence à agência indicada."""
    conexao = conectar_banco()
    pertence = False
    if conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("SELECT 1 FROM Conta WHERE num_conta = %s AND num_ag = %s", (num_conta, num_ag))
            pertence = cursor.fetchone() is not None
        except mysql.connector.Error as err:
            st.error(f"Erro ao validar agência da conta: {err}")
        finally:
            cursor.close()
            conexao.close()
    return pertence


def obter_contas_usuario(cpf):
    """Retorna a lista de números de conta vinculados a um CPF de cliente."""
    conexao = conectar_banco()
    contas = []
    if conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("SELECT num_conta FROM Titularidade_Conta WHERE cpf_cliente = %s", (cpf,))
            contas = [row[0] for row in cursor.fetchall()]
        except mysql.connector.Error as err:
            st.error(f"Erro ao buscar contas: {err}")
        finally:
            cursor.close()
            conexao.close()
    return contas


def autenticar(username, senha):
    """
    Tenta autenticar pelo username, CPF (com ou sem máscara) ou matrícula.
    Retorna o dict do usuário em caso de sucesso, ou None.
    """
    conexao = conectar_banco()
    if not conexao:
        return None

    cursor = conexao.cursor(dictionary=True)
    username_cpf_limpo = limpar_cpf(username)  # caso o usuário digite o CPF com pontuação
    cursor.execute(
        "SELECT * FROM Usuario WHERE username = %s OR cpf = %s OR matricula = %s",
        (username, username_cpf_limpo, username)
    )
    usuario = cursor.fetchone()
    cursor.close()
    conexao.close()

    if not usuario:
        return None

    db_pass = usuario['senha']
    hashed_input = hash_senha(senha)
    if db_pass == hashed_input:
        return usuario
    return None


def promover_usuario(id_usuario, novo_cargo):
    """Promove um usuário para 'gerente' ou 'admin', criando o Funcionario se necessário."""
    conexao = conectar_banco()
    if conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("UPDATE Usuario SET role = %s WHERE id = %s", (novo_cargo, id_usuario))

            cursor.execute("SELECT username, nome, cpf, matricula FROM Usuario WHERE id = %s", (id_usuario,))
            user_data = cursor.fetchone()
            if user_data:
                username, nome, cpf, matricula = user_data

                # Se não tem matrícula de funcionário, criar um funcionário
                if not matricula:
                    cursor.execute("SELECT IFNULL(MAX(CAST(SUBSTRING(matricula, 4) AS UNSIGNED)), 1000) + 1 FROM Funcionario")
                    max_num = cursor.fetchone()[0]
                    matricula = f"MAT{max_num}"

                    # Buscar dados do cliente para preencher
                    cursor.execute("SELECT * FROM Cliente WHERE cpf = %s", (cpf,))
                    c_data = cursor.fetchone()
                    if c_data:
                        # Obter dados do cliente
                        # Cliente: cpf, nome_completo, rg_num, rg_org, rg_uf, birth, tipo_log, nome_log, num, comp, bairro, cep, cidade, estado
                        # Funcionario: matricula, nome_completo, senha, tipo_log, nome_log, num, comp, bairro, cidade, estado, cep, cargo, genero, birth, salario, num_ag
                        # No Funcionario, 'admin' não existe como cargo — equivale a 'gerente'.
                        # Demais roles (gerente, atendente, caixa) mapeiam 1:1.
                        cargo_funcionario = 'gerente' if novo_cargo == 'admin' else novo_cargo
                        sql_func = """
                            INSERT INTO Funcionario (
                                matricula, nome_completo, senha, tipo_logradouro, nome_logradouro, numero, complemento, bairro, cidade, estado, cep,
                                cargo, genero, data_nascimento, salario, num_ag
                            ) VALUES (%s, %s, 'hashsenha123', %s, %s, %s, %s, %s, %s, %s, %s, %s, 'não-binário', %s, 3000.00, 1)
                        """
                        cursor.execute(sql_func, (
                            matricula, nome, c_data[6], c_data[7], c_data[8], c_data[9], c_data[10], c_data[12], c_data[13], c_data[11],
                            cargo_funcionario, c_data[5]
                        ))

                        cursor.execute("UPDATE Usuario SET matricula = %s WHERE id = %s", (matricula, id_usuario))
                else:
                    # Se já tem matrícula, apenas atualizar o cargo (mesma regra de mapeamento)
                    cargo_funcionario = 'gerente' if novo_cargo == 'admin' else novo_cargo
                    cursor.execute("UPDATE Funcionario SET cargo = %s WHERE matricula = %s", (
                        cargo_funcionario, matricula
                    ))
            conexao.commit()
        except mysql.connector.Error as err:
            conexao.rollback()
            st.error(f"Erro ao promover usuário: {err}")
        finally:
            cursor.close()
            conexao.close()


def cadastrar_cliente(dados):
    """
    Cadastra um novo cliente: Cliente, contatos, Conta padrão, Titularidade,
    transação inicial e Usuario. `dados` é um dict com as chaves:
    cpf, nome, cad_user, cad_pass, data_nasc, email, telefone, rg_num,
    rg_orgao, rg_uf, tipo_log, nome_log, numero, complemento, bairro, cep, cidade, estado.
    Retorna (sucesso: bool, mensagem: str, num_conta: int|None).
    """
    conexao = conectar_banco()
    if not conexao:
        return False, "Não foi possível conectar ao banco de dados.", None

    cursor = conexao.cursor()
    try:
        cpf = dados["cpf"]
        nome = dados["nome"]
        cad_user = dados["cad_user"]
        cad_pass = dados["cad_pass"]

        # Validar duplicidade
        cursor.execute("SELECT 1 FROM Usuario WHERE username = %s OR cpf = %s", (cad_user, cpf))
        if cursor.fetchone():
            return False, "O nome de usuário ou CPF já está cadastrado.", None

        # 1. Inserir Cliente
        sql_cliente = """
            INSERT INTO Cliente (
                cpf, nome_completo, rg_numero, rg_orgao, rg_uf, data_nascimento,
                tipo_logradouro, nome_logradouro, numero, complemento, bairro, cep, cidade, estado
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql_cliente, (
            cpf, nome, dados["rg_num"], dados["rg_orgao"], dados["rg_uf"], dados["data_nasc"].strftime('%Y-%m-%d'),
            dados["tipo_log"], dados["nome_log"], dados["numero"], dados["complemento"], dados["bairro"],
            dados["cep"], dados["cidade"], dados["estado"]
        ))

        # 2. Contato
        if dados.get("email"):
            cursor.execute("INSERT INTO Email_Cliente (cpf_cliente, email, descricao) VALUES (%s, %s, 'pessoal')", (cpf, dados["email"]))
        if dados.get("telefone"):
            cursor.execute("INSERT INTO Telefone_Cliente (cpf_cliente, telefone, descricao) VALUES (%s, %s, 'celular')", (cpf, dados["telefone"]))

        # 3. Conta Bancária Padrão (saldo inicial = 1000.00)
        cursor.execute("SELECT MAX(num_conta) FROM Conta")
        max_c = cursor.fetchone()[0]
        num_conta = (max_c + 1) if max_c else 50502

        # Agência e Gerente Padrão
        cursor.execute("SELECT num_ag FROM Agencia LIMIT 1")
        res_ag = cursor.fetchone()
        num_ag = res_ag[0] if res_ag else 1

        cursor.execute("SELECT matricula FROM Funcionario WHERE cargo = 'gerente' LIMIT 1")
        res_ger = cursor.fetchone()
        mat_gerente = res_ger[0] if res_ger else 'MAT1001'

        # Inserir Conta com saldo = 0 (o trigger vai atualizar para 1000 no depósito)
        cursor.execute("""
            INSERT INTO Conta (num_conta, saldo, senha, tipo_conta, taxa_juros, limite_credito, data_aniversario_contrato, num_ag, matricula_gerente)
            VALUES (%s, 0.00, %s, 'conta-corrente', NULL, NULL, CURDATE(), %s, %s)
        """, (num_conta, hash_senha(cad_pass), num_ag, mat_gerente))

        # Titularidade
        cursor.execute("INSERT INTO Titularidade_Conta (num_conta, cpf_cliente, tipo_titular) VALUES (%s, %s, '1º titular')", (num_conta, cpf))

        # Lançar Transação inicial
        cursor.execute("SELECT IFNULL(MAX(num_transacao), 0) + 1 FROM Transacao WHERE num_conta = %s", (num_conta,))
        num_trans = cursor.fetchone()[0]
        cursor.execute("""
            INSERT INTO Transacao (num_transacao, num_conta, tipo, data_hora, valor)
            VALUES (%s, %s, 'depósito', NOW(), 1000.00)
        """, (num_trans, num_conta))

        # 4. Inserir Usuario
        cursor.execute("""
            INSERT INTO Usuario (username, nome, senha, role, cpf)
            VALUES (%s, %s, %s, 'client', %s)
        """, (cad_user, nome, hash_senha(cad_pass), cpf))

        conexao.commit()
        return True, f"Conta criada! Sua conta é {num_conta} com saldo inicial de R$ 1.000,00.", num_conta
    except mysql.connector.Error as err:
        conexao.rollback()
        return False, f"Erro ao registrar: {err}", None
    finally:
        cursor.close()
        conexao.close()