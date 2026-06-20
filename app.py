"""NullBank — ponto de entrada da aplicação Streamlit.

Este arquivo só monta a página e roteia entre as views.
A lógica de negócio fica em config.py, database.py, auth.py, utils/ e views/.
"""
import streamlit as st

from config import carregar_env
from database import conectar_banco
from auth import inicializar_autenticacao
from styles import CSS
from views import login, extrato, transferencia, gerente, usuarios

carregar_env()

# CONFIGURAÇÕES DA TELA E ESTILO
st.set_page_config(page_title="NullBank", page_icon="🏦", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)

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
    login.render()

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

    with tab1:
        extrato.render(user)

    with tab2:
        transferencia.render(user)

    if tab3 is not None:
        with tab3:
            gerente.render()

    if tab4 is not None:
        with tab4:
            usuarios.render(user)