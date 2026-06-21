"""Aba: Área do Gerente.

Conforme o enunciado: os gerentes devem ser capazes de cadastrar e alterar
dados de funcionários, abrir contas de clientes e alterar dados destas contas,
mas sem realizar movimentações financeiras diretas. As contas listadas
devem ser apenas as gerenciadas por ele (ou todas para administrador).
"""
from datetime import date
import random
import mysql.connector
import streamlit as st

from database import conectar_banco
from auth import hash_senha, limpar_cpf
from utils import formatar_datas_dataframe


def render(user):
    st.header("💼 Painel de Gerência")
    st.write("Central de administração de contas, funcionários e dependentes.")

    # Criação de abas para organizar o fluxo do gerente
    tab_relatorio, tab_abrir_conta, tab_funcionario, tab_dependente = st.tabs([
        "📊 Relatório de Contas",
        "🆕 Abrir Conta",
        "👤 Cadastrar Funcionário",
        "👶 Dependente"
    ])

    # ==================== TAB 1: RELATÓRIO DE CONTAS ====================
    with tab_relatorio:
        st.subheader("Contas Cadastradas")
        if user['role'] == 'admin':
            st.caption("Visualizando todas as contas (Permissão: Admin/DBA)")
        else:
            st.caption(f"Visualizando contas sob gerência da matrícula {user['matricula']}")

        if st.button("Carregar Relatório de Contas", key="btn_relatorio"):
            conexao = conectar_banco()
            if conexao:
                cursor = conexao.cursor(dictionary=True)
                try:
                    if user['role'] == 'admin':
                        cursor.execute("SELECT * FROM v_contas_gerente ORDER BY num_conta")
                    else:
                        cursor.execute(
                            "SELECT * FROM v_contas_gerente WHERE matricula_gerente = %s ORDER BY num_conta",
                            (user['matricula'],)
                        )
                    resultados = cursor.fetchall()

                    if resultados:
                        resultados = formatar_datas_dataframe(resultados)
                        st.dataframe(resultados, width="stretch")
                    else:
                        st.info("Nenhuma conta encontrada.")
                except mysql.connector.Error as err:
                    st.error(f"Erro ao carregar relatório: {err}")
                finally:
                    cursor.close()
                    conexao.close()

    # ==================== TAB 2: ABRIR CONTA ====================
    with tab_abrir_conta:
        st.subheader("Abertura de Nova Conta")
        
        fluxo_cliente = st.radio(
            "Cliente já está cadastrado no banco?",
            ["Sim, já é cliente", "Não, cadastrar novo cliente"],
            key="abrir_fluxo_cliente"
        )

        cpf_cliente = ""
        cliente_valido = False
        dados_novo_cliente = {}

        if fluxo_cliente == "Sim, já é cliente":
            cpf_cliente_raw = st.text_input("CPF do Cliente (apenas números):", max_chars=11, key="abrir_cpf_existente")
            cpf_cliente = limpar_cpf(cpf_cliente_raw)
            if cpf_cliente:
                if len(cpf_cliente) == 11:
                    cliente_valido = True
                else:
                    st.warning("O CPF deve conter exatamente 11 dígitos.")
        else:
            # Formulário de Cadastro do Cliente
            st.markdown("#### Dados Pessoais do Cliente")
            col1, col2 = st.columns(2)
            with col1:
                cpf_raw = st.text_input("CPF (apenas números):", max_chars=11, key="cad_cpf")
                nome_completo = st.text_input("Nome Completo:", key="cad_nome")
                data_nasc = st.date_input("Data de Nascimento:", min_value=date(1900, 1, 1), max_value=date.today(), key="cad_nasc")
            with col2:
                rg_num = st.text_input("RG (Número):", key="cad_rg")
                rg_org = st.text_input("Órgão Emissor (ex: SSP):", key="cad_rg_org")
                rg_uf = st.selectbox("UF do RG:", ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"], key="cad_rg_uf")

            st.markdown("#### Endereço")
            col3, col4, col5 = st.columns([1, 2, 1])
            with col3:
                tipo_log = st.selectbox("Tipo:", ["Rua", "Avenida", "Praça", "Travessa", "Rodovia"], key="cad_tipo_log")
                numero = st.text_input("Número:", key="cad_num")
            with col4:
                nome_log = st.text_input("Nome do Logradouro:", key="cad_log_nome")
                complemento = st.text_input("Complemento:", key="cad_comp")
            with col5:
                bairro = st.text_input("Bairro:", key="cad_bairro")
                cep = st.text_input("CEP (8 dígitos):", max_chars=8, key="cad_cep")

            col6, col7 = st.columns(2)
            with col6:
                cidade = st.text_input("Cidade:", key="cad_cidade")
            with col7:
                estado = st.selectbox("Estado (UF):", ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"], key="cad_estado")

            st.markdown("#### Contatos")
            col8, col9 = st.columns(2)
            with col8:
                email = st.text_input("E-mail:", key="cad_email")
            with col9:
                telefone = st.text_input("Telefone (DDD + número):", key="cad_telefone")

            username_usuario = st.text_input("Nome de Usuário para Login:", key="cad_username")
            senha_usuario = st.text_input("Senha do Usuário:", type="password", key="cad_senha")

            cpf_cliente = limpar_cpf(cpf_raw)
            if cpf_cliente and nome_completo and username_usuario and senha_usuario:
                if len(cpf_cliente) == 11 and len(cep) == 8:
                    cliente_valido = True
                    dados_novo_cliente = {
                        "cpf": cpf_cliente,
                        "nome": nome_completo,
                        "data_nasc": data_nasc,
                        "rg_num": rg_num,
                        "rg_orgao": rg_org,
                        "rg_uf": rg_uf,
                        "tipo_log": tipo_log,
                        "nome_log": nome_log,
                        "numero": numero,
                        "complemento": complemento,
                        "bairro": bairro,
                        "cep": cep,
                        "cidade": cidade,
                        "estado": estado,
                        "email": email,
                        "telefone": telefone,
                        "cad_user": username_usuario,
                        "cad_pass": senha_usuario
                    }

        # Dados da nova conta
        if cliente_valido:
            st.markdown("#### Configurações da Conta Bancária")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                tipo_conta = st.selectbox(
                    "Tipo de Conta:",
                    ["conta-corrente", "poupança", "conta especial"],
                    key="abrir_tipo_conta"
                )
                saldo_inicial = st.number_input("Saldo Inicial (R$):", min_value=0.00, value=1000.00, step=100.0, key="abrir_saldo")
                senha_conta = st.text_input("Senha da Conta (6 dígitos ou alfa):", type="password", key="abrir_senha_conta")
            with col_c2:
                # Buscar agências disponíveis
                agencias = []
                conexao = conectar_banco()
                if conexao:
                    cursor = conexao.cursor()
                    try:
                        cursor.execute("SELECT num_ag, nome_ag FROM Agencia")
                        agencias = cursor.fetchall()
                    except mysql.connector.Error:
                        pass
                    finally:
                        cursor.close()
                        conexao.close()
                
                if agencias:
                    num_ag = st.selectbox(
                        "Agência:",
                        [ag[0] for ag in agencias],
                        format_func=lambda x: next(f"Ag. {ag[0]} - {ag[1]}" for ag in agencias if ag[0] == x),
                        key="abrir_agencia"
                    )
                else:
                    num_ag = st.number_input("Número da Agência:", min_value=1, value=1, key="abrir_agencia_manual")

                # Campos condicionais
                taxa_juros = None
                limite_credito = None
                if tipo_conta == "poupança":
                    taxa_juros = st.number_input("Taxa de Juros (% a.m.):", min_value=0.0, max_value=100.0, value=0.5, step=0.1, key="abrir_juros")
                elif tipo_conta == "conta especial":
                    limite_credito = st.number_input("Limite de Crédito (R$):", min_value=0.0, value=500.0, step=100.0, key="abrir_limite")

            if st.button("Abrir Conta", key="btn_abrir_conta_confirm"):
                if not senha_conta:
                    st.error("A conta deve ter uma senha cadastrada.")
                    return

                conexao = conectar_banco()
                if conexao:
                    cursor = conexao.cursor()
                    try:
                        # Se for novo cliente, cadastrar primeiro
                        if fluxo_cliente == "Não, cadastrar novo cliente":
                            # Inserir Cliente
                            sql_cl = """
                                INSERT INTO Cliente (
                                    cpf, nome_completo, rg_numero, rg_orgao, rg_uf, data_nascimento,
                                    tipo_logradouro, nome_logradouro, numero, complemento, bairro, cep, cidade, estado
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            cursor.execute(sql_cl, (
                                dados_novo_cliente["cpf"], dados_novo_cliente["nome"], dados_novo_cliente["rg_num"],
                                dados_novo_cliente["rg_orgao"], dados_novo_cliente["rg_uf"],
                                dados_novo_cliente["data_nasc"].strftime('%Y-%m-%d'), dados_novo_cliente["tipo_log"],
                                dados_novo_cliente["nome_log"], dados_novo_cliente["numero"], dados_novo_cliente["complemento"],
                                dados_novo_cliente["bairro"], dados_novo_cliente["cep"], dados_novo_cliente["cidade"],
                                dados_novo_cliente["estado"]
                            ))

                            # Contatos
                            if dados_novo_cliente["email"]:
                                cursor.execute("INSERT INTO Email_Cliente (cpf_cliente, email, descricao) VALUES (%s, %s, 'pessoal')", (dados_novo_cliente["cpf"], dados_novo_cliente["email"]))
                            if dados_novo_cliente["telefone"]:
                                cursor.execute("INSERT INTO Telefone_Cliente (cpf_cliente, telefone, descricao) VALUES (%s, %s, 'celular')", (dados_novo_cliente["cpf"], dados_novo_cliente["telefone"]))

                            # Inserir Usuario
                            cursor.execute(
                                "INSERT INTO Usuario (username, nome, senha, role, cpf) VALUES (%s, %s, %s, 'client', %s)",
                                (dados_novo_cliente["cad_user"], dados_novo_cliente["nome"], hash_senha(dados_novo_cliente["cad_pass"]), dados_novo_cliente["cpf"])
                            )

                        else:
                            # Validar se o cliente realmente existe
                            cursor.execute("SELECT nome_completo FROM Cliente WHERE cpf = %s", (cpf_cliente,))
                            cli_row = cursor.fetchone()
                            if not cli_row:
                                st.error("Erro: O CPF digitado não está cadastrado como cliente no banco.")
                                return

                        # Gerar número da conta
                        cursor.execute("SELECT MAX(num_conta) FROM Conta")
                        max_c = cursor.fetchone()[0]
                        num_conta = (max_c + 1) if max_c else 50502

                        # Determinar matrícula do gerente da conta
                        mat_gerente = user['matricula'] if user['role'] == 'gerente' else 'MAT1001'

                        # Inserir Conta (saldo = 0 para ser atualizado pelo trigger de depósito inicial)
                        sql_conta = """
                            INSERT INTO Conta (num_conta, saldo, senha, tipo_conta, taxa_juros, limite_credito, data_aniversario_contrato, num_ag, matricula_gerente)
                            VALUES (%s, 0.00, %s, %s, %s, %s, CURDATE(), %s, %s)
                        """
                        cursor.execute(sql_conta, (num_conta, hash_senha(senha_conta), tipo_conta, taxa_juros, limite_credito, num_ag, mat_gerente))

                        # Inserir Titularidade
                        cursor.execute(
                            "INSERT INTO Titularidade_Conta (num_conta, cpf_cliente, tipo_titular) VALUES (%s, %s, '1º titular')",
                            (num_conta, cpf_cliente)
                        )

                        # Registrar depósito de saldo inicial, se houver
                        if saldo_inicial > 0:
                            cursor.execute("SELECT IFNULL(MAX(num_transacao), 0) + 1 FROM Transacao WHERE num_conta = %s", (num_conta,))
                            num_trans = cursor.fetchone()[0]
                            cursor.execute(
                                """
                                INSERT INTO Transacao (num_transacao, num_conta, tipo, data_hora, valor)
                                VALUES (%s, %s, 'depósito', NOW(), %s)
                                """,
                                (num_trans, num_conta, saldo_inicial)
                            )

                        conexao.commit()
                        st.success(f"🎉 Conta número {num_conta} aberta com sucesso! Saldo inicial: R$ {saldo_inicial:.2f}")
                    except mysql.connector.Error as err:
                        conexao.rollback()
                        st.error(f"Erro ao abrir conta: {err}")
                    finally:
                        cursor.close()
                        conexao.close()
        else:
            st.info("Preencha as informações do cliente acima para configurar a conta bancária.")

    # ==================== TAB 3: CADASTRAR FUNCIONÁRIO ====================
    with tab_funcionario:
        st.subheader("Cadastro de Funcionário")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            f_nome = st.text_input("Nome Completo:", key="func_nome")
            f_genero = st.selectbox("Gênero:", ["masculino", "feminino", "não-binário"], key="func_genero")
            f_nasc = st.date_input("Data de Nascimento:", min_value=date(1900, 1, 1), max_value=date.today(), key="func_nasc")
            f_cargo = st.selectbox("Cargo:", ["gerente", "atendente", "caixa"], key="func_cargo")
            f_salario = st.number_input("Salário (R$):", min_value=2286.00, value=3000.00, step=100.0, key="func_salario")
        with col_f2:
            f_tipo_log = st.selectbox("Tipo Logradouro:", ["Rua", "Avenida", "Praça", "Travessa", "Rodovia"], key="func_tipo_log")
            f_nome_log = st.text_input("Nome Logradouro:", key="func_nome_log")
            f_numero = st.text_input("Número:", key="func_numero")
            f_complemento = st.text_input("Complemento:", key="func_comp")
            f_bairro = st.text_input("Bairro:", key="func_bairro")
            f_cidade = st.text_input("Cidade:", key="func_cidade")
            f_estado = st.selectbox("Estado (UF):", ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"], key="func_estado")
            f_cep = st.text_input("CEP:", max_chars=8, key="func_cep")

        f_senha = st.text_input("Senha do Funcionário (será hasheada):", type="password", key="func_senha")

        # Buscar agências para vincular o funcionário
        f_agencias = []
        conexao = conectar_banco()
        if conexao:
            cursor = conexao.cursor()
            try:
                cursor.execute("SELECT num_ag, nome_ag FROM Agencia")
                f_agencias = cursor.fetchall()
            except mysql.connector.Error:
                pass
            finally:
                cursor.close()
                conexao.close()

        if f_agencias:
            f_num_ag = st.selectbox(
                "Agência do Funcionário:",
                [ag[0] for ag in f_agencias],
                format_func=lambda x: next(f"Ag. {ag[0]} - {ag[1]}" for ag in f_agencias if ag[0] == x),
                key="func_agencia"
            )
        else:
            f_num_ag = st.number_input("Número da Agência:", min_value=1, value=1, key="func_ag_manual")

        if st.button("Cadastrar Funcionário", key="btn_cadastrar_func"):
            if not f_nome or not f_senha or not f_cep or len(f_cep) != 8:
                st.error("Por favor, preencha todos os campos obrigatórios (Nome, Senha e CEP com 8 dígitos).")
                return

            conexao = conectar_banco()
            if conexao:
                cursor = conexao.cursor()
                try:
                    # Gerar matrícula
                    cursor.execute("SELECT IFNULL(MAX(CAST(SUBSTRING(matricula, 4) AS UNSIGNED)), 1000) + 1 FROM Funcionario")
                    max_num = cursor.fetchone()[0]
                    f_matricula = f"MAT{max_num}"

                    # Hashear senha
                    senha_criptografada = hash_senha(f_senha)

                    # Inserir no Funcionario
                    sql_func = """
                        INSERT INTO Funcionario (
                            matricula, nome_completo, senha, tipo_logradouro, nome_logradouro, numero, complemento,
                            bairro, cidade, estado, cep, cargo, genero, data_nascimento, salario, num_ag
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql_func, (
                        f_matricula, f_nome, senha_criptografada, f_tipo_log, f_nome_log, f_numero, f_complemento,
                        f_bairro, f_cidade, f_estado, f_cep, f_cargo, f_genero, f_nasc.strftime('%Y-%m-%d'),
                        f_salario, f_num_ag
                    ))

                    # Inserir no Usuario (username será a matrícula do funcionário)
                    sql_usr = """
                        INSERT INTO Usuario (username, nome, senha, role, matricula)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql_usr, (f_matricula, f_nome, senha_criptografada, f_cargo, f_matricula))

                    conexao.commit()
                    st.success(f"🎉 Funcionário cadastrado com sucesso! Matrícula gerada: **{f_matricula}**")
                except mysql.connector.Error as err:
                    conexao.rollback()
                    st.error(f"Erro ao cadastrar funcionário: {err}")
                finally:
                    cursor.close()
                    conexao.close()

    # ==================== TAB 4: DEPENDENTE ====================
    with tab_dependente:
        st.subheader("Cadastro de Dependente")
        
        # Buscar lista de funcionários para vincular o dependente
        funcionarios_lista = []
        conexao = conectar_banco()
        if conexao:
            cursor = conexao.cursor()
            try:
                cursor.execute("SELECT matricula, nome_completo FROM Funcionario ORDER BY nome_completo")
                funcionarios_lista = cursor.fetchall()
            except mysql.connector.Error:
                pass
            finally:
                cursor.close()
                conexao.close()

        if funcionarios_lista:
            dep_matricula = st.selectbox(
                "Funcionário Titular:",
                [f[0] for f in funcionarios_lista],
                format_func=lambda x: next(f"{f[1]} ({f[0]})" for f in funcionarios_lista if f[0] == x),
                key="dep_mat_func"
            )
        else:
            dep_matricula = st.text_input("Matrícula do Funcionário:", key="dep_mat_func_manual")

        dep_nome = st.text_input("Nome do Dependente Completo:", key="dep_nome")
        dep_nasc = st.date_input("Data de Nascimento do Dependente:", min_value=date(1900, 1, 1), max_value=date.today(), key="dep_nasc")
        dep_parentesco = st.selectbox("Parentesco:", ["filho(a)", "cônjuge", "genitor(a)"], key="dep_parentesco")

        if st.button("Adicionar Dependente", key="btn_add_dependente"):
            if not dep_nome or not dep_matricula:
                st.error("Por favor, preencha o nome do dependente e selecione um funcionário.")
                return

            # Calcular idade
            hoje = date.today()
            dep_idade = hoje.year - dep_nasc.year - ((hoje.month, hoje.day) < (dep_nasc.month, dep_nasc.day))

            conexao = conectar_banco()
            if conexao:
                cursor = conexao.cursor()
                try:
                    # Validar limite de 5 dependentes
                    cursor.execute("SELECT COUNT(*) FROM Dependente WHERE matricula_func = %s", (dep_matricula,))
                    qtd_dependentes = cursor.fetchone()[0]

                    if qtd_dependentes >= 5:
                        st.error("Erro: Este funcionário já possui o limite máximo de 5 dependentes cadastrados.")
                        return

                    sql_dep = """
                        INSERT INTO Dependente (nome_completo, matricula_func, data_nascimento, parentesco, idade)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql_dep, (dep_nome, dep_matricula, dep_nasc.strftime('%Y-%m-%d'), dep_parentesco, dep_idade))
                    conexao.commit()

                    st.success(f"✅ Dependente {dep_nome} vinculado ao funcionário {dep_matricula} com sucesso!")
                except mysql.connector.Error as err:
                    conexao.rollback()
                    st.error(f"Erro ao cadastrar dependente: {err}")
                finally:
                    cursor.close()
                    conexao.close()