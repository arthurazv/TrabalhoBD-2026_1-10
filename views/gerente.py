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
from auth import hash_senha, limpar_cpf, autenticar
from utils import formatar_datas_dataframe, formatar_cpf


def render(user):
    st.header("💼 Painel de Gerência")
    st.write("Central de administração de contas, funcionários e dependentes.")

    # Criação de abas para organizar o fluxo do gerente
    tab_relatorio, tab_abrir_conta, tab_alterar_conta, tab_funcionario, tab_dependente, tab_taxa = st.tabs([
        "📊 Relatório de Contas",
        "🆕 Abrir Conta",
        "✏️ Alterar Conta/Cliente",
        "👤 Funcionários",
        "👶 Dependentes",
        "💰 Cobrança de Taxa"
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

    # ==================== TAB 3: ALTERAR CONTA / CLIENTE ====================
    with tab_alterar_conta:
        st.subheader("Alteração de Dados de Conta e Cliente")
        
        # Buscar lista de contas sob gerência deste gerente (ou todas se admin)
        contas_gerenciadas = []
        conexao = conectar_banco()
        if conexao:
            cursor = conexao.cursor(dictionary=True)
            try:
                if user['role'] == 'admin':
                    cursor.execute("""
                        SELECT DISTINCT c.num_conta, cl.nome_completo 
                        FROM Conta c 
                        JOIN Titularidade_Conta tc ON c.num_conta = tc.num_conta 
                        JOIN Cliente cl ON tc.cpf_cliente = cl.cpf 
                        ORDER BY c.num_conta
                    """)
                else:
                    cursor.execute("""
                        SELECT DISTINCT c.num_conta, cl.nome_completo 
                        FROM Conta c 
                        JOIN Titularidade_Conta tc ON c.num_conta = tc.num_conta 
                        JOIN Cliente cl ON tc.cpf_cliente = cl.cpf 
                        WHERE c.matricula_gerente = %s 
                        ORDER BY c.num_conta
                    """, (user['matricula'],))
                contas_gerenciadas = cursor.fetchall()
            except mysql.connector.Error as err:
                st.error(f"Erro ao listar contas: {err}")
            finally:
                cursor.close()
                conexao.close()

        if contas_gerenciadas:
            conta_edit_selecionada = st.selectbox(
                "Selecione a Conta para Alterar:",
                contas_gerenciadas,
                format_func=lambda c: f"Conta {c['num_conta']} - {c['nome_completo']}",
                key="alterar_conta_select_box"
            )

            # Buscar dados atuais
            conexao = conectar_banco()
            c_detalhes = None
            cl_detalhes = None
            email_atual = ""
            telefone_atual = ""
            
            if conexao:
                cursor = conexao.cursor(dictionary=True)
                try:
                    cursor.execute("SELECT * FROM Conta WHERE num_conta = %s", (conta_edit_selecionada['num_conta'],))
                    c_detalhes = cursor.fetchone()
                    
                    cursor.execute("SELECT cpf_cliente FROM Titularidade_Conta WHERE num_conta = %s AND tipo_titular = '1º titular'", (conta_edit_selecionada['num_conta'],))
                    tit_row = cursor.fetchone()
                    if tit_row:
                        cursor.execute("SELECT * FROM Cliente WHERE cpf = %s", (tit_row['cpf_cliente'],))
                        cl_detalhes = cursor.fetchone()
                        
                        cursor.execute("SELECT email FROM Email_Cliente WHERE cpf_cliente = %s LIMIT 1", (tit_row['cpf_cliente'],))
                        em_row = cursor.fetchone()
                        if em_row:
                            email_atual = em_row['email']
                            
                        cursor.execute("SELECT telefone FROM Telefone_Cliente WHERE cpf_cliente = %s LIMIT 1", (tit_row['cpf_cliente'],))
                        tel_row = cursor.fetchone()
                        if tel_row:
                            telefone_atual = tel_row['telefone']
                except mysql.connector.Error as err:
                    st.error(f"Erro ao carregar detalhes para edição: {err}")
                finally:
                    cursor.close()
                    conexao.close()

            if c_detalhes and cl_detalhes:
                st.markdown("---")
                st.markdown("#### 💳 Alterar Dados da Conta")
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    e_tipo_conta = st.selectbox(
                        "Tipo de Conta:",
                        ["conta-corrente", "poupança", "conta especial"],
                        index=["conta-corrente", "poupança", "conta especial"].index(c_detalhes['tipo_conta']),
                        key="edit_tipo_conta"
                    )
                    # Senha opcional
                    e_senha_conta = st.text_input("Nova Senha da Conta (deixe em branco para não alterar):", type="password", key="edit_senha_conta")
                with col_e2:
                    # Buscar agências disponíveis
                    list_ag = []
                    conexao = conectar_banco()
                    if conexao:
                        cursor = conexao.cursor()
                        try:
                            cursor.execute("SELECT num_ag, nome_ag FROM Agencia")
                            list_ag = cursor.fetchall()
                        except mysql.connector.Error:
                            pass
                        finally:
                            cursor.close()
                            conexao.close()
                    
                    if list_ag:
                        idx_ag = 0
                        for i, ag in enumerate(list_ag):
                            if ag[0] == c_detalhes['num_ag']:
                                idx_ag = i
                                break
                        e_num_ag = st.selectbox(
                            "Agência:",
                            [ag[0] for ag in list_ag],
                            index=idx_ag,
                            format_func=lambda x: next(f"Ag. {ag[0]} - {ag[1]}" for ag in list_ag if ag[0] == x),
                            key="edit_agencia"
                        )
                    else:
                        e_num_ag = st.number_input("Número da Agência:", min_value=1, value=int(c_detalhes['num_ag']), key="edit_agencia_manual")

                    # Juros e Limite
                    e_taxa_juros = None
                    e_limite_credito = None
                    if e_tipo_conta == "poupança":
                        val_juros = c_detalhes['taxa_juros'] if c_detalhes['taxa_juros'] is not None else 0.5
                        e_taxa_juros = st.number_input("Taxa de Juros (% a.m.):", min_value=0.0, max_value=100.0, value=float(val_juros), step=0.1, key="edit_juros")
                    elif e_tipo_conta == "conta especial":
                        val_limite = c_detalhes['limite_credito'] if c_detalhes['limite_credito'] is not None else 500.0
                        e_limite_credito = st.number_input("Limite de Crédito (R$):", min_value=0.0, value=float(val_limite), step=100.0, key="edit_limite")

                st.markdown("#### 👤 Alterar Dados do Titular (Cliente)")
                col_e3, col_e4 = st.columns(2)
                with col_e3:
                    e_nome = st.text_input("Nome Completo:", value=cl_detalhes['nome_completo'], key="edit_cli_nome")
                    e_nasc = st.date_input("Data de Nascimento:", value=cl_detalhes['data_nascimento'], min_value=date(1900, 1, 1), max_value=date.today(), key="edit_cli_nasc")
                with col_e4:
                    e_rg_num = st.text_input("RG (Número):", value=cl_detalhes['rg_numero'], key="edit_cli_rg")
                    e_rg_org = st.text_input("Órgão Emissor:", value=cl_detalhes['rg_orgao'], key="edit_cli_rg_org")
                    list_uf = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
                    e_rg_uf = st.selectbox("UF do RG:", list_uf, index=list_uf.index(cl_detalhes['rg_uf']) if cl_detalhes['rg_uf'] in list_uf else 5, key="edit_cli_rg_uf")

                st.markdown("##### Endereço do Cliente")
                col_e5, col_e6, col_e7 = st.columns([1, 2, 1])
                with col_e5:
                    e_tipo_log = st.selectbox("Tipo:", ["Rua", "Avenida", "Praça", "Travessa", "Rodovia"], index=["Rua", "Avenida", "Praça", "Travessa", "Rodovia"].index(cl_detalhes['tipo_logradouro']) if cl_detalhes['tipo_logradouro'] in ["Rua", "Avenida", "Praça", "Travessa", "Rodovia"] else 0, key="edit_cli_tipo_log")
                    e_numero = st.text_input("Número:", value=cl_detalhes['numero'], key="edit_cli_num")
                with col_e6:
                    e_nome_log = st.text_input("Nome do Logradouro:", value=cl_detalhes['nome_logradouro'], key="edit_cli_log_nome")
                    e_complemento = st.text_input("Complemento:", value=cl_detalhes['complemento'], key="edit_cli_comp")
                with col_e7:
                    e_bairro = st.text_input("Bairro:", value=cl_detalhes['bairro'], key="edit_cli_bairro")
                    e_cep = st.text_input("CEP:", max_chars=8, value=cl_detalhes['cep'], key="edit_cli_cep")

                col_e8, col_e9 = st.columns(2)
                with col_e8:
                    e_cidade = st.text_input("Cidade:", value=cl_detalhes['cidade'], key="edit_cli_cidade")
                with col_e9:
                    e_estado = st.selectbox("Estado (UF):", list_uf, index=list_uf.index(cl_detalhes['estado']) if cl_detalhes['estado'] in list_uf else 5, key="edit_cli_estado")

                st.markdown("##### Contatos do Cliente")
                col_e10, col_e11 = st.columns(2)
                with col_e10:
                    e_email = st.text_input("E-mail:", value=email_atual, key="edit_cli_email")
                with col_e11:
                    e_telefone = st.text_input("Telefone:", value=telefone_atual, key="edit_cli_telefone")

                if st.button("Salvar Alterações da Conta e Cliente", key="btn_confirmar_edicao_conta"):
                    if not e_nome or not e_cep or len(e_cep) != 8:
                        st.error("Por favor, preencha os campos obrigatórios (Nome e CEP com 8 dígitos).")
                        return

                    conexao = conectar_banco()
                    if conexao:
                        cursor = conexao.cursor()
                        try:
                            # 1. Atualizar Cliente
                            sql_cli_up = """
                                UPDATE Cliente SET
                                    nome_completo = %s, rg_numero = %s, rg_orgao = %s, rg_uf = %s, data_nascimento = %s,
                                    tipo_logradouro = %s, nome_logradouro = %s, numero = %s, complemento = %s,
                                    bairro = %s, cep = %s, cidade = %s, estado = %s
                                WHERE cpf = %s
                            """
                            cursor.execute(sql_cli_up, (
                                e_nome, e_rg_num, e_rg_org, e_rg_uf, e_nasc.strftime('%Y-%m-%d'),
                                e_tipo_log, e_nome_log, e_numero, e_complemento, e_bairro, e_cep,
                                e_cidade, e_estado, cl_detalhes['cpf']
                            ))

                            # 2. Atualizar Contatos
                            if e_email:
                                cursor.execute("INSERT INTO Email_Cliente (cpf_cliente, email, descricao) VALUES (%s, %s, 'pessoal') ON DUPLICATE KEY UPDATE email = VALUES(email)", (cl_detalhes['cpf'], e_email))
                            if e_telefone:
                                cursor.execute("INSERT INTO Telefone_Cliente (cpf_cliente, telefone, descricao) VALUES (%s, %s, 'celular') ON DUPLICATE KEY UPDATE telefone = VALUES(telefone)", (cl_detalhes['cpf'], e_telefone))

                            # 3. Atualizar Conta
                            if e_senha_conta:
                                sql_cta_up = """
                                    UPDATE Conta SET
                                        tipo_conta = %s, taxa_juros = %s, limite_credito = %s, num_ag = %s, senha = %s
                                    WHERE num_conta = %s
                                """
                                cursor.execute(sql_cta_up, (e_tipo_conta, e_taxa_juros, e_limite_credito, e_num_ag, hash_senha(e_senha_conta), c_detalhes['num_conta']))
                            else:
                                sql_cta_up = """
                                    UPDATE Conta SET
                                        tipo_conta = %s, taxa_juros = %s, limite_credito = %s, num_ag = %s
                                    WHERE num_conta = %s
                                """
                                cursor.execute(sql_cta_up, (e_tipo_conta, e_taxa_juros, e_limite_credito, e_num_ag, c_detalhes['num_conta']))

                            # 4. Atualizar Nome de Usuário se necessário
                            cursor.execute("UPDATE Usuario SET nome = %s WHERE cpf = %s", (e_nome, cl_detalhes['cpf']))
                            if e_senha_conta:
                                cursor.execute("UPDATE Usuario SET senha = %s WHERE cpf = %s", (hash_senha(e_senha_conta), cl_detalhes['cpf']))

                            conexao.commit()
                            st.success("🎉 Alterações salvas com sucesso!")
                            st.rerun()
                        except mysql.connector.Error as err:
                            conexao.rollback()
                            st.error(f"Erro ao salvar alterações: {err}")
                        finally:
                            cursor.close()
                            conexao.close()
        else:
            st.info("Nenhuma conta sob sua gerência encontrada para alteração.")

    # ==================== TAB 4: GERENCIAR FUNCIONÁRIOS ====================
    with tab_funcionario:
        st.subheader("Cadastro e Edição de Funcionários")
        
        fluxo_func = st.radio(
            "Ação de Funcionário:",
            ["Cadastrar Novo Funcionário", "Editar Funcionário Existente"],
            key="fluxo_funcionario"
        )

        val_nome = ""
        val_genero = "masculino"
        val_nasc = date(1990, 1, 1)
        val_cargo = "atendente"
        val_salario = 3000.00
        val_tipo_log = "Rua"
        val_nome_log = ""
        val_numero = ""
        val_complemento = ""
        val_bairro = ""
        val_cidade = ""
        val_estado = "CE"
        val_cep = ""
        val_num_ag = 1
        func_selecionado = None

        if fluxo_func == "Editar Funcionário Existente":
            funcionarios_edicao = []
            conexao = conectar_banco()
            if conexao:
                cursor = conexao.cursor(dictionary=True)
                try:
                    cursor.execute("SELECT * FROM Funcionario ORDER BY nome_completo")
                    funcionarios_edicao = cursor.fetchall()
                except mysql.connector.Error:
                    pass
                finally:
                    cursor.close()
                    conexao.close()

            if funcionarios_edicao:
                func_selecionado = st.selectbox(
                    "Selecione o Funcionário para Editar:",
                    funcionarios_edicao,
                    format_func=lambda f: f"{f['nome_completo']} ({f['matricula']})",
                    key="func_edit_select_box"
                )
                if func_selecionado:
                    val_nome = func_selecionado['nome_completo']
                    val_genero = func_selecionado['genero']
                    val_nasc = func_selecionado['data_nascimento']
                    val_cargo = func_selecionado['cargo']
                    val_salario = func_selecionado['salario']
                    val_tipo_log = func_selecionado['tipo_logradouro']
                    val_nome_log = func_selecionado['nome_logradouro']
                    val_numero = func_selecionado['numero']
                    val_complemento = func_selecionado['complemento']
                    val_bairro = func_selecionado['bairro']
                    val_cidade = func_selecionado['cidade']
                    val_estado = func_selecionado['estado']
                    val_cep = func_selecionado['cep']
                    val_num_ag = func_selecionado['num_ag']
            else:
                st.warning("Nenhum funcionário cadastrado para edição.")
                st.stop()

        suffix = "_edit" if fluxo_func == "Editar Funcionário Existente" else "_cad"

        st.markdown("#### Dados Pessoais do Funcionário")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            f_nome = st.text_input("Nome Completo:", value=val_nome, key=f"func_nome{suffix}")
            generos = ["masculino", "feminino", "não-binário"]
            f_genero = st.selectbox("Gênero:", generos, index=generos.index(val_genero) if val_genero in generos else 0, key=f"func_genero{suffix}")
            f_nasc = st.date_input("Data de Nascimento:", value=val_nasc, min_value=date(1900, 1, 1), max_value=date.today(), key=f"func_nasc{suffix}")
            cargos = ["gerente", "atendente", "caixa"]
            f_cargo = st.selectbox("Cargo:", cargos, index=cargos.index(val_cargo) if val_cargo in cargos else 0, key=f"func_cargo{suffix}")
            f_salario = st.number_input("Salário (R$):", min_value=2286.00, value=float(val_salario), step=100.0, key=f"func_salario{suffix}")
        with col_f2:
            f_tipo_log = st.selectbox("Tipo Logradouro:", ["Rua", "Avenida", "Praça", "Travessa", "Rodovia"], index=["Rua", "Avenida", "Praça", "Travessa", "Rodovia"].index(val_tipo_log) if val_tipo_log in ["Rua", "Avenida", "Praça", "Travessa", "Rodovia"] else 0, key=f"func_tipo_log{suffix}")
            f_nome_log = st.text_input("Nome Logradouro:", value=val_nome_log, key=f"func_nome_log{suffix}")
            f_numero = st.text_input("Número:", value=val_numero, key=f"func_numero{suffix}")
            f_complemento = st.text_input("Complemento:", value=val_complemento, key=f"func_comp{suffix}")
            f_bairro = st.text_input("Bairro:", value=val_bairro, key=f"func_bairro{suffix}")
            f_cidade = st.text_input("Cidade:", value=val_cidade, key=f"func_cidade{suffix}")
            list_uf = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
            f_estado = st.selectbox("Estado (UF):", list_uf, index=list_uf.index(val_estado) if val_estado in list_uf else 5, key=f"func_estado{suffix}")
            f_cep = st.text_input("CEP:", max_chars=8, value=val_cep, key=f"func_cep{suffix}")

        if fluxo_func == "Editar Funcionário Existente":
            f_senha = st.text_input("Nova Senha do Funcionário (deixe em branco para manter a atual):", type="password", key=f"func_senha{suffix}")
        else:
            f_senha = st.text_input("Senha do Funcionário (será hasheada):", type="password", key=f"func_senha{suffix}")

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
            idx_f_ag = 0
            for i, ag in enumerate(f_agencias):
                if ag[0] == val_num_ag:
                    idx_f_ag = i
                    break
            f_num_ag = st.selectbox(
                "Agência do Funcionário:",
                [ag[0] for ag in f_agencias],
                index=idx_f_ag,
                format_func=lambda x: next(f"Ag. {ag[0]} - {ag[1]}" for ag in f_agencias if ag[0] == x),
                key=f"func_agencia{suffix}"
            )
        else:
            f_num_ag = st.number_input("Número da Agência:", min_value=1, value=int(val_num_ag), key=f"func_ag_manual{suffix}")

        btn_label = "Salvar Alterações" if fluxo_func == "Editar Funcionário Existente" else "Cadastrar Funcionário"
        if st.button(btn_label, key=f"btn_func_submit{suffix}"):
            if not f_nome or not f_cep or len(f_cep) != 8:
                st.error("Por favor, preencha todos os campos obrigatórios (Nome e CEP com 8 dígitos).")
                return
            if fluxo_func == "Cadastrar Novo Funcionário" and not f_senha:
                st.error("A senha é obrigatória para o cadastro de novos funcionários.")
                return

            conexao = conectar_banco()
            if conexao:
                cursor = conexao.cursor()
                try:
                    if fluxo_func == "Cadastrar Novo Funcionário":
                        # Gerar matrícula
                        cursor.execute("SELECT IFNULL(MAX(CAST(SUBSTRING(matricula, 4) AS UNSIGNED)), 1000) + 1 FROM Funcionario")
                        max_num = cursor.fetchone()[0]
                        f_matricula = f"MAT{max_num}"

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

                        # Inserir no Usuario
                        sql_usr = """
                            INSERT INTO Usuario (username, nome, senha, role, matricula)
                            VALUES (%s, %s, %s, %s, %s)
                        """
                        cursor.execute(sql_usr, (f_matricula, f_nome, senha_criptografada, f_cargo, f_matricula))
                        conexao.commit()
                        st.success(f"🎉 Funcionário cadastrado com sucesso! Matrícula gerada: **{f_matricula}**")
                        st.rerun()
                    else:
                        # Editar existente
                        f_matricula = func_selecionado['matricula']
                        
                        if f_senha:
                            senha_criptografada = hash_senha(f_senha)
                            sql_func_up = """
                                UPDATE Funcionario SET
                                    nome_completo = %s, senha = %s, tipo_logradouro = %s, nome_logradouro = %s,
                                    numero = %s, complemento = %s, bairro = %s, cidade = %s, estado = %s,
                                    cep = %s, cargo = %s, genero = %s, data_nascimento = %s, salario = %s, num_ag = %s
                                WHERE matricula = %s
                            """
                            cursor.execute(sql_func_up, (
                                f_nome, senha_criptografada, f_tipo_log, f_nome_log, f_numero, f_complemento,
                                f_bairro, f_cidade, f_estado, f_cep, f_cargo, f_genero, f_nasc.strftime('%Y-%m-%d'),
                                f_salario, f_num_ag, f_matricula
                            ))
                            sql_usr_up = """
                                UPDATE Usuario SET nome = %s, senha = %s, role = %s WHERE matricula = %s
                            """
                            cursor.execute(sql_usr_up, (f_nome, senha_criptografada, f_cargo, f_matricula))
                        else:
                            sql_func_up = """
                                UPDATE Funcionario SET
                                    nome_completo = %s, tipo_logradouro = %s, nome_logradouro = %s,
                                    numero = %s, complemento = %s, bairro = %s, cidade = %s, estado = %s,
                                    cep = %s, cargo = %s, genero = %s, data_nascimento = %s, salario = %s, num_ag = %s
                                WHERE matricula = %s
                            """
                            cursor.execute(sql_func_up, (
                                f_nome, f_tipo_log, f_nome_log, f_numero, f_complemento,
                                f_bairro, f_cidade, f_estado, f_cep, f_cargo, f_genero, f_nasc.strftime('%Y-%m-%d'),
                                f_salario, f_num_ag, f_matricula
                            ))
                            sql_usr_up = """
                                UPDATE Usuario SET nome = %s, role = %s WHERE matricula = %s
                            """
                            cursor.execute(sql_usr_up, (f_nome, f_cargo, f_matricula))

                        conexao.commit()
                        st.success(f"🎉 Dados do funcionário **{f_matricula}** atualizados com sucesso!")
                        st.rerun()
                except mysql.connector.Error as err:
                    conexao.rollback()
                    st.error(f"Erro ao salvar funcionário: {err}")
                finally:
                    cursor.close()
                    conexao.close()

    # ==================== TAB 5: GERENCIAR DEPENDENTES ====================
    with tab_dependente:
        st.subheader("Gerenciamento de Dependentes de Funcionários")
        
        # Buscar lista de funcionários para vincular/gerenciar dependentes
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
                "Selecione o Funcionário Titular:",
                [f[0] for f in funcionarios_lista],
                format_func=lambda x: next(f"{f[1]} ({f[0]})" for f in funcionarios_lista if f[0] == x),
                key="dep_mat_func_select"
            )
        else:
            dep_matricula = st.text_input("Matrícula do Funcionário:", key="dep_mat_func_manual")

        if dep_matricula:
            # 1. Carregar e exibir dependentes atuais deste funcionário
            conexao = conectar_banco()
            deps = []
            if conexao:
                cursor = conexao.cursor(dictionary=True)
                try:
                    cursor.execute("SELECT * FROM Dependente WHERE matricula_func = %s", (dep_matricula,))
                    deps = cursor.fetchall()
                except mysql.connector.Error as err:
                    st.error(f"Erro ao buscar dependentes: {err}")
                finally:
                    cursor.close()
                    conexao.close()

            if deps:
                st.markdown("##### Dependentes Atuais")
                for d in deps:
                    col_d1, col_d2, col_d3 = st.columns([3, 2, 2])
                    with col_d1:
                        st.markdown(f"👶 **{d['nome_completo']}** ({d['parentesco']})")
                        st.caption(f"Nascimento: {d['data_nascimento'].strftime('%d/%m/%Y')} | Idade: {d['idade']} anos")
                    with col_d2:
                        if st.button("Editar", key=f"btn_edit_dep_{d['nome_completo']}"):
                            st.session_state['editando_dep'] = {
                                'matricula_func': dep_matricula,
                                'nome_completo_antigo': d['nome_completo'],
                                'nome_completo': d['nome_completo'],
                                'data_nascimento': d['data_nascimento'],
                                'parentesco': d['parentesco']
                            }
                    with col_d3:
                        if st.button("Excluir", key=f"btn_del_dep_{d['nome_completo']}"):
                            conexao_del = conectar_banco()
                            if conexao_del:
                                cursor_del = conexao_del.cursor()
                                try:
                                    cursor_del.execute(
                                        "DELETE FROM Dependente WHERE matricula_func = %s AND nome_completo = %s",
                                        (dep_matricula, d['nome_completo'])
                                    )
                                    conexao_del.commit()
                                    st.success(f"Dependente {d['nome_completo']} excluído com sucesso!")
                                    st.rerun()
                                except mysql.connector.Error as err:
                                    st.error(f"Erro ao excluir dependente: {err}")
                                finally:
                                    cursor_del.close()
                                    conexao_del.close()

            # Formulário de edição se selecionado
            if 'editando_dep' in st.session_state and st.session_state['editando_dep']['matricula_func'] == dep_matricula:
                st.markdown("---")
                st.write(f"### ✏️ Editar Dependente: {st.session_state['editando_dep']['nome_completo_antigo']}")
                ed = st.session_state['editando_dep']
                
                ed_nome = st.text_input("Nome Completo:", value=ed['nome_completo'], key="ed_dep_nome_input")
                ed_nasc = st.date_input("Data de Nascimento:", value=ed['data_nascimento'], min_value=date(1900, 1, 1), max_value=date.today(), key="ed_dep_nasc_input")
                parentesco_opcoes = ["filho(a)", "cônjuge", "genitor(a)"]
                ed_parentesco = st.selectbox("Parentesco:", parentesco_opcoes, index=parentesco_opcoes.index(ed['parentesco']) if ed['parentesco'] in parentesco_opcoes else 0, key="ed_dep_parentesco_input")
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("Salvar Alterações", key="btn_save_dep_changes"):
                        hoje = date.today()
                        ed_idade = hoje.year - ed_nasc.year - ((hoje.month, hoje.day) < (ed_nasc.month, ed_nasc.day))
                        
                        conexao_ed = conectar_banco()
                        if conexao_ed:
                            cursor_ed = conexao_ed.cursor()
                            try:
                                cursor_ed.execute(
                                    """
                                    UPDATE Dependente 
                                    SET nome_completo = %s, data_nascimento = %s, parentesco = %s, idade = %s
                                    WHERE matricula_func = %s AND nome_completo = %s
                                    """,
                                    (ed_nome, ed_nasc.strftime('%Y-%m-%d'), ed_parentesco, ed_idade, dep_matricula, ed['nome_completo_antigo'])
                                )
                                conexao_ed.commit()
                                if 'editando_dep' in st.session_state:
                                    del st.session_state['editando_dep']
                                st.success("Dependente atualizado com sucesso!")
                                st.rerun()
                            except mysql.connector.Error as err:
                                st.error(f"Erro ao atualizar dependente: {err}")
                            finally:
                                cursor_ed.close()
                                conexao_ed.close()
                with col_b2:
                    if st.button("Cancelar", key="btn_cancel_dep_edit"):
                        if 'editando_dep' in st.session_state:
                            del st.session_state['editando_dep']
                        st.rerun()

            st.markdown("---")
            st.markdown("##### 🆕 Adicionar Novo Dependente")
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
                        st.rerun()
                    except mysql.connector.Error as err:
                        conexao.rollback()
                        st.error(f"Erro ao cadastrar dependente: {err}")
                    finally:
                        cursor.close()
                        conexao.close()

    # ==================== TAB 6: COBRANÇA DE TAXA ====================
    with tab_taxa:
        st.subheader("Cobrança de Taxa com Autorização de outro Funcionário")
        st.write("Debite taxas (ex: serviços extras, manutenção) da conta de um cliente. Requer credenciais de outro funcionário.")

        c_conta = st.text_input("Número da Conta do Cliente:", key="taxa_conta_input")
        c_valor = st.number_input("Valor da Taxa (R$):", min_value=0.01, step=1.0, key="taxa_valor_input")
        c_desc = st.selectbox(
            "Descrição/Motivo da Taxa:",
            ["Taxa de Manutenção de Conta", "Taxa de Emissão de Cartão", "Taxa de Emissão de Extrato Físico", "Outras Taxas"],
            key="taxa_descricao_select"
        )
        if c_desc == "Outras Taxas":
            c_desc_outro = st.text_input("Descreva a Taxa:", key="taxa_desc_outro_input")
            descricao_final = c_desc_outro if c_desc_outro else "Cobrança de Taxa"
        else:
            descricao_final = c_desc

        st.markdown("#### 🔑 Credenciais do Funcionário Autorizador")
        st.caption("A cobrança deve ser autorizada por outro funcionário ativo logado no sistema.")
        
        auth_user = st.text_input("Matrícula ou Username do Autorizador:", key="taxa_auth_user_input")
        auth_pass = st.text_input("Senha do Autorizador:", type="password", key="taxa_auth_pass_input")

        if st.button("Confirmar Débito de Taxa", key="btn_confirmar_taxa_submit"):
            if not c_conta or not auth_user or not auth_pass or c_valor <= 0:
                st.error("Por favor, preencha todos os campos do formulário.")
                return

            try:
                num_conta = int(c_conta)
            except ValueError:
                st.error("O número da conta deve ser um valor numérico.")
                return

            # Autenticar o autorizador
            autorizador = autenticar(auth_user, auth_pass)
            if not autorizador:
                st.error("Falha na autorização: Credenciais inválidas do funcionário autorizador.")
                return

            # Garantir que é um funcionário
            if not autorizador['matricula']:
                st.error("Falha na autorização: O autorizador deve ser um funcionário (cargo cadastrado).")
                return

            # Garantir que não seja o mesmo usuário logado
            if autorizador['matricula'] == user['matricula']:
                st.error("Falha na autorização: A cobrança de taxa não pode ser autorizada pelo mesmo gerente que a executa.")
                return

            # Executar a transação (tipo 'pagamento' que debita do saldo da conta)
            conexao = conectar_banco()
            if conexao:
                cursor = conexao.cursor()
                try:
                    # Validar existência da conta
                    cursor.execute("SELECT 1 FROM Conta WHERE num_conta = %s", (num_conta,))
                    if not cursor.fetchone():
                        st.error(f"Erro: A conta {num_conta} não existe no banco de dados.")
                        return

                    # Obter próximo número de transação para a conta
                    cursor.execute("SELECT IFNULL(MAX(num_transacao), 0) + 1 FROM Transacao WHERE num_conta = %s", (num_conta,))
                    prox_trans = cursor.fetchone()[0]

                    # Gravar transação como tipo 'pagamento' (reduz o saldo via trigger)
                    cursor.execute(
                        """
                        INSERT INTO Transacao (num_transacao, num_conta, tipo, data_hora, valor)
                        VALUES (%s, %s, 'pagamento', NOW(), %s)
                        """,
                        (prox_trans, num_conta, c_valor)
                    )
                    conexao.commit()
                    st.success(f"✅ Cobrança de R$ {c_valor:.2f} ({descricao_final}) efetuada com sucesso! Autorizado por: {autorizador['nome']} ({autorizador['matricula']})")
                except mysql.connector.Error as err:
                    conexao.rollback()
                    st.error(f"❌ Transação Rejeitada: {err.msg}")
                finally:
                    cursor.close()
                    conexao.close()