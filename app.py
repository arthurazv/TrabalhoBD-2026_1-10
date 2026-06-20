import os
import random
import hashlib
import streamlit as st
import mysql.connector

# CARREGAR ARQUIVO .ENV MANUALMENTE SE EXISTIR (Para Desenvolvimento Local)
def carregar_env():
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        val = val.strip().strip("'\"")
                        os.environ[key.strip()] = val

carregar_env()

REQUIRED_ENV_VARS = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]


def carregar_config_banco():
    faltando = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if faltando:
        st.error(
            "Configuração incompleta: variáveis de ambiente ausentes: "
            f"{', '.join(faltando)}. Verifique o arquivo .env do stack e reinicie o container."
        )
        st.stop()

    return {
        "host": os.environ["DB_HOST"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
        "database": os.environ["DB_NAME"],
        "port": int(os.environ.get("DB_PORT", 3306)),
    }


def conectar_banco():
    config = carregar_config_banco()
    try:
        conexao = mysql.connector.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            port=config["port"],
            auth_plugin='mysql_native_password',
            connection_timeout=5,
            use_pure=True
        )
        return conexao
    except mysql.connector.Error as err:
        st.error(f"Erro ao conectar ao banco de dados: {err}")
        return None


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def inicializar_autenticacao(conexao):
    if not conexao:
        return
    cursor = conexao.cursor()
    # Verificar se a tabela Usuario existe
    try:
        cursor.execute("SELECT 1 FROM Usuario LIMIT 1")
        cursor.fetchall()
    except mysql.connector.Error:
        # Tabela não existe, criar
        try:
            cursor.execute("""
                CREATE TABLE Usuario (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    nome VARCHAR(150) NOT NULL,
                    senha VARCHAR(255) NOT NULL,
                    role ENUM('client', 'gerente', 'admin') NOT NULL DEFAULT 'client',
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
                # Gerente é admin, outros cargos são gerentes
                role = 'admin' if cargo == 'gerente' else 'gerente'
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
                
            conexao.commit()
        except mysql.connector.Error as err:
            st.error(f"Erro ao inicializar banco de dados de autenticação: {err}")
    finally:
        cursor.close()


def obter_contas_usuario(cpf):
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


def promover_usuario(id_usuario, novo_cargo):
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
                        sql_func = """
                            INSERT INTO Funcionario (
                                matricula, nome_completo, senha, tipo_logradouro, nome_logradouro, numero, complemento, bairro, cidade, estado, cep,
                                cargo, genero, data_nascimento, salario, num_ag
                            ) VALUES (%s, %s, 'hashsenha123', %s, %s, %s, %s, %s, %s, %s, %s, %s, 'não-binário', %s, 3000.00, 1)
                        """
                        cursor.execute(sql_func, (
                            matricula, nome, c_data[6], c_data[7], c_data[8], c_data[9], c_data[10], c_data[12], c_data[13], c_data[11],
                            'gerente' if novo_cargo == 'admin' else novo_cargo, c_data[5]
                        ))
                        
                        cursor.execute("UPDATE Usuario SET matricula = %s WHERE id = %s", (matricula, id_usuario))
                else:
                    # Se já tem matrícula, apenas atualizar o cargo
                    cursor.execute("UPDATE Funcionario SET cargo = %s WHERE matricula = %s", (
                        'gerente' if novo_cargo in ['gerente', 'admin'] else 'caixa', matricula
                    ))
            conexao.commit()
        except mysql.connector.Error as err:
            conexao.rollback()
            st.error(f"Erro ao promover usuário: {err}")
        finally:
            cursor.close()
            conexao.close()


# CONFIGURAÇÕES DA TELA E ESTILO
st.set_page_config(page_title="NullBank", page_icon="🏦", layout="centered")

# CSS customizado para visual premium
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background-color: #0F0F1A;
        color: #E0E0FF;
    }
    
    .main-title {
        background: linear-gradient(90deg, #FF4B4B 0%, #FF7676 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0px;
        font-size: 2.5rem;
    }
    
    .subtitle {
        text-align: center;
        color: #8A8AAB;
        font-family: 'Inter', sans-serif;
        margin-bottom: 2rem;
    }
    
    .user-badge {
        background-color: #1A1A2E;
        border: 1px solid #3F3F5F;
        padding: 10px 15px;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Customizar abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #141424;
        padding: 8px;
        border-radius: 12px;
        border: 1px solid #252538;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #8A8AAB;
        font-weight: 600;
        border: none;
        transition: all 0.3s;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #FF7676;
        background-color: #1E1E32;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #FF4B4B !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Título da Aplicação
st.markdown("<h1 class='main-title'>🏦 NullBank</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Sistema de Autoatendimento Bancário Premium</p>", unsafe_allow_html=True)

# Inicializar tabela e banco se necessário
conn = conectar_banco()
if conn:
    inicializar_autenticacao(conn)
    conn.close()

# Controle de sessão
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = None

# Fluxo se NÃO estiver logado
if st.session_state['usuario'] is None:
    tab_login, tab_cadastro = st.tabs(["🔑 Login", "📝 Criar Conta"])
    
    with tab_login:
        st.markdown("<h3 style='text-align: center; color: #FF7676;'>🔑 Entrar no NullBank</h3>", unsafe_allow_html=True)
        username = st.text_input("Usuário (CPF ou Matrícula ou Username)", key="login_user")
        senha = st.text_input("Senha", type="password", key="login_pass")
        
        if st.button("Acessar Conta", use_container_width=True):
            if not username or not senha:
                st.error("Por favor, preencha todos os campos.")
            else:
                conexao = conectar_banco()
                if conexao:
                    cursor = conexao.cursor(dictionary=True)
                    cursor.execute(
                        "SELECT * FROM Usuario WHERE username = %s OR cpf = %s OR matricula = %s",
                        (username, username, username)
                    )
                    usuario = cursor.fetchone()
                    cursor.close()
                    conexao.close()
                    
                    if usuario:
                        db_pass = usuario['senha']
                        hashed_input = hash_senha(senha)
                        if db_pass == senha or db_pass == hashed_input:
                            st.session_state['usuario'] = usuario
                            st.success(f"Login realizado com sucesso! Bem-vindo(a), {usuario['nome']}.")
                            st.rerun()
                        else:
                            st.error("Senha incorreta.")
                    else:
                        st.error("Usuário não encontrado.")
                        
    with tab_cadastro:
        st.markdown("<h3 style='text-align: center; color: #FF7676;'>📝 Cadastre-se como Cliente</h3>", unsafe_allow_html=True)
        nome = st.text_input("Nome Completo *", key="cad_name")
        cad_user = st.text_input("Nome de Usuário (login) *", key="cad_username")
        cpf = st.text_input("CPF (apenas 11 números) *", max_chars=11, key="cad_cpf")
        cad_pass = st.text_input("Senha *", type="password", key="cad_password")
        data_nasc = st.date_input("Data de Nascimento *", min_value=None, max_value=None, key="cad_birth")
        
        with st.expander("Informações Adicionais (Endereço e Contato)"):
            email = st.text_input("E-mail", placeholder="seuemail@exemplo.com", key="cad_email")
            telefone = st.text_input("Telefone", placeholder="88991234567", key="cad_phone")
            rg_num = st.text_input("Número do RG", value="1234567", key="cad_rg")
            rg_orgao = st.text_input("Órgão Emissor", value="SSP", key="cad_rg_org")
            rg_uf = st.text_input("UF do RG", value="CE", max_chars=2, key="cad_rg_uf")
            
            tipo_log = st.selectbox("Tipo de Logradouro", ["Rua", "Avenida", "Travessa", "Praça"], key="cad_log_type")
            nome_log = st.text_input("Nome do Logradouro", value="Rua das Palmeiras", key="cad_log_name")
            numero = st.text_input("Número", value="100", key="cad_num")
            complemento = st.text_input("Complemento", value="Apto 1", key="cad_comp")
            bairro = st.text_input("Bairro", value="Centro", key="cad_bairro")
            cep = st.text_input("CEP (apenas 8 números)", value="62010000", max_chars=8, key="cad_cep")
            cidade = st.text_input("Cidade", value="Sobral", key="cad_city")
            estado = st.text_input("Estado (UF)", value="CE", max_chars=2, key="cad_state")
            
        if st.button("Criar Minha Conta", use_container_width=True):
            if not nome or not cad_user or not cpf or not cad_pass or not data_nasc:
                st.error("Por favor, preencha todos os campos obrigatórios (*).")
            elif len(cpf) != 11 or not cpf.isdigit():
                st.error("O CPF deve conter exatamente 11 dígitos numéricos.")
            else:
                conexao = conectar_banco()
                if conexao:
                    cursor = conexao.cursor()
                    try:
                        # Validar duplicidade
                        cursor.execute("SELECT 1 FROM Usuario WHERE username = %s OR cpf = %s", (cad_user, cpf))
                        if cursor.fetchone():
                            st.error("O nome de usuário ou CPF já está cadastrado.")
                        else:
                            # 1. Inserir Cliente
                            sql_cliente = """
                                INSERT INTO Cliente (
                                    cpf, nome_completo, rg_numero, rg_orgao, rg_uf, data_nascimento,
                                    tipo_logradouro, nome_logradouro, numero, complemento, bairro, cep, cidade, estado
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            cursor.execute(sql_cliente, (
                                cpf, nome, rg_num, rg_orgao, rg_uf, data_nasc.strftime('%Y-%m-%d'),
                                tipo_log, nome_log, numero, complemento, bairro, cep, cidade, estado
                            ))
                            
                            # 2. Contato
                            if email:
                                cursor.execute("INSERT INTO Email_Cliente (cpf_cliente, email, descricao) VALUES (%s, %s, 'pessoal')", (cpf, email))
                            if telefone:
                                cursor.execute("INSERT INTO Telefone_Cliente (cpf_cliente, telefone, descricao) VALUES (%s, %s, 'celular')", (cpf, telefone))
                                
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
                            st.success(f"🎉 Conta criada! Sua conta é {num_conta} com saldo inicial de R$ 1.000,00.")
                            st.info("Utilize a aba 'Login' para acessar.")
                    except mysql.connector.Error as err:
                        conexao.rollback()
                        st.error(f"Erro ao registrar: {err}")
                    finally:
                        cursor.close()
                        conexao.close()
else:
    # FLUXO SE LOGADO
    user = st.session_state['usuario']
    
    # Barra de Usuário Logado
    st.markdown(f"""
        <div class="user-badge">
            <div>
                👤 <b>{user['nome']}</b> ({user['username']}) | Cargo: <code>{user['role'].upper()}</code>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("Sair (Logout)", type="secondary"):
        st.session_state['usuario'] = None
        st.rerun()
        
    st.write("Escolha uma opção no menu abaixo:")
    
    # Renderizar abas dinâmicas
    if user['role'] in ['gerente', 'admin']:
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Consultar Extrato", "💸 Fazer Transferência", "💼 Área do Gerente", "⚙️ Gerenciar Usuários"])
    else:
        tab1, tab2 = st.tabs(["📊 Consultar Extrato", "💸 Fazer Transferência"])
        tab3 = None
        tab4 = None

    # ABA 1: EXTRATO
    with tab1:
        st.header("Consulta de Extrato")
        
        # Obter e filtrar contas se for cliente
        if user['role'] == 'client':
            contas_usuario = obter_contas_usuario(user['cpf'])
            if contas_usuario:
                conta = st.selectbox("Selecione sua conta:", contas_usuario, key="extrato_conta_select")
            else:
                st.warning("Você não tem nenhuma conta vinculada.")
                conta = None
        else:
            conta = st.text_input("Digite o número da conta:", key="extrato_conta_input")

        if st.button("Buscar Extrato", key="btn_extrato"):
            if conta:
                conexao = conectar_banco()
                if conexao:
                    cursor = conexao.cursor(dictionary=True)
                    try:
                        cursor.execute("SELECT * FROM v_extrato_completo WHERE num_conta = %s ORDER BY data_hora DESC", (conta,))
                        resultados = cursor.fetchall()

                        if resultados:
                            st.success(f"Extrato da conta {conta} carregado!")
                            st.dataframe(resultados, use_container_width=True)
                        else:
                            st.warning("Nenhuma transação encontrada para esta conta.")
                    except mysql.connector.Error as err:
                        st.error(f"Erro ao carregar extrato: {err}")
                    finally:
                        cursor.close()
                        conexao.close()
            else:
                st.warning("Por favor, digite ou selecione um número de conta válido.")

    # ABA 2: TRANSFERÊNCIA
    with tab2:
        st.header("Transferência Bancária")

        if user['role'] == 'client':
            contas_usuario = obter_contas_usuario(user['cpf'])
            if contas_usuario:
                conta_origem = st.selectbox("Sua Conta (Origem):", contas_usuario, key="trans_origem_select")
            else:
                st.warning("Você não tem nenhuma conta vinculada.")
                conta_origem = None
        else:
            conta_origem = st.text_input("Sua Conta (Origem):", key="trans_origem_input")
            
        conta_destino = st.text_input("Conta de Destino:", key="trans_destino")
        valor = st.number_input("Valor da Transferência (R$):", min_value=0.01, key="trans_valor")

        if st.button("Confirmar Transferência", key="btn_transferencia"):
            if conta_origem and conta_destino and valor > 0:
                conexao = conectar_banco()

                if conexao:
                    cursor = conexao.cursor()
                    try:
                        c_origem = int(conta_origem)
                        c_destino = int(conta_destino)
                        v_transf = float(valor)

                        num_t_origem = random.randint(10000, 99999)
                        num_t_destino = random.randint(10000, 99999)

                        cursor.callproc('sp_executar_transferencia', [c_origem, c_destino, v_transf, num_t_origem, num_t_destino])
                        conexao.commit()

                        st.success(f"✅ Transferência de R$ {valor:.2f} realizada com sucesso!")
                    except mysql.connector.Error as erro:
                        st.error(f"❌ Transferência Negada: {erro.msg}")
                    except ValueError:
                        st.error("Por favor, digite apenas números nas contas.")
                    finally:
                        cursor.close()
                        conexao.close()
            else:
                st.error("Preencha todos os campos corretamente.")

    # ABA 3: GERENTE (Apenas Gerentes/Admins)
    if tab3 is not None:
        with tab3:
            st.header("Painel do Gerente")
            st.write("Visão geral de todas as contas e titulares cadastrados.")

            if st.button("Carregar Relatório de Contas", key="btn_relatorio"):
                conexao = conectar_banco()

                if conexao:
                    cursor = conexao.cursor(dictionary=True)
                    try:
                        cursor.execute("SELECT * FROM v_contas_gerente")
                        resultados = cursor.fetchall()

                        if resultados:
                            st.dataframe(resultados, use_container_width=True)
                        else:
                            st.info("Nenhuma conta encontrada.")
                    except mysql.connector.Error as err:
                        st.error(f"Erro ao carregar relatório: {err}")
                    finally:
                        cursor.close()
                        conexao.close()

    # ABA 4: GERENCIAR USUÁRIOS (Apenas Gerentes/Admins)
    if tab4 is not None:
        with tab4:
            st.header("⚙️ Gerenciamento de Usuários")
            st.write("Promova clientes para cargos com maiores permissões administrativas.")
            
            conexao = conectar_banco()
            if conexao:
                cursor = conexao.cursor(dictionary=True)
                try:
                    cursor.execute("SELECT id, username, nome, role, cpf, matricula FROM Usuario ORDER BY role DESC, nome ASC")
                    usuarios = cursor.fetchall()
                    
                    if usuarios:
                        for u in usuarios:
                            # Ignorar a si mesmo nas ações
                            if u['id'] == user['id']:
                                continue
                                
                            col1, col2, col3 = st.columns([3, 2, 2])
                            with col1:
                                st.markdown(f"👤 **{u['nome']}** (`{u['username']}`)")
                                st.markdown(f"<small style='color: #8A8AAB;'>CPF: {u['cpf'] or 'N/A'} | Matrícula: {u['matricula'] or 'N/A'}</small>", unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"Nível de Permissão: `{u['role'].upper()}`")
                            with col3:
                                # Apenas clientes podem ser promovidos a gerentes
                                if u['role'] == 'client':
                                    if st.button("Promover a Gerente", key=f"btn_prom_ger_{u['id']}", use_container_width=True):
                                        promover_usuario(u['id'], 'gerente')
                                        st.success(f"Usuário {u['nome']} promovido para Gerente!")
                                        st.rerun()
                                # Gerentes podem ser promovidos a admins por admins
                                elif u['role'] == 'gerente' and user['role'] == 'admin':
                                    if st.button("Promover a Admin", key=f"btn_prom_adm_{u['id']}", use_container_width=True):
                                        promover_usuario(u['id'], 'admin')
                                        st.success(f"Usuário {u['nome']} promovido para Admin!")
                                        st.rerun()
                                else:
                                    st.write("Sem ações disponíveis")
                            st.markdown("---")
                    else:
                        st.info("Nenhum usuário cadastrado além do atual.")
                except mysql.connector.Error as err:
                    st.error(f"Erro ao listar usuários: {err}")
                finally:
                    cursor.close()
                    conexao.close()
