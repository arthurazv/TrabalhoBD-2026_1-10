"""NullBank — ponto de entrada da aplicação Streamlit.

Este arquivo só monta a página e roteia entre as views.
A lógica de negócio fica em config.py, database.py, auth.py, utils/ e views/.
"""
import streamlit as st

from config import carregar_env
from database import conectar_banco
from auth import inicializar_autenticacao
from styles import CSS
from views import login, extrato, transferencia, gerente, usuarios, extrato_atendente, operacoes

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

    # Monta a lista de (rótulo, função_de_render) conforme o role do usuário,
    # seguindo as regras do enunciado:
    #   - client: extrato (próprias contas) + transferência (própria conta)
    #   - atendente: só leitura de número/saldo das contas da própria agência
    #   - caixa: extrato + transferência + saque/depósito, restritos à própria agência
    #   - gerente: área do gerente (contas que gerencia, cadastro de funcionários/contas) + gerenciar usuários
    #     (não movimenta dinheiro)
    #   - admin: acesso total e irrestrito a todas as telas
    abas = []

    if user['role'] == 'client':
        abas.append(("📊 Consultar Extrato", lambda: extrato.render(user)))
        abas.append(("💸 Fazer Transferência", lambda: transferencia.render(user)))

    elif user['role'] == 'atendente':
        abas.append(("📋 Consultar Contas", lambda: extrato_atendente.render(user)))

    elif user['role'] == 'caixa':
        abas.append(("📊 Consultar Extrato", lambda: extrato.render(user)))
        abas.append(("💸 Fazer Transferência", lambda: transferencia.render(user)))
        abas.append(("💵 Saque / Depósito", lambda: operacoes.render(user)))

    elif user['role'] == 'gerente':
        abas.append(("💼 Área do Gerente", lambda: gerente.render(user)))
        abas.append(("⚙️ Gerenciar Usuários", lambda: usuarios.render(user)))

    elif user['role'] == 'admin':
        # Admin tem acesso total e irrestrito (conforme o enunciado)
        abas.append(("📊 Consultar Extrato", lambda: extrato.render(user)))
        abas.append(("💸 Fazer Transferência", lambda: transferencia.render(user)))
        abas.append(("💵 Saque / Depósito", lambda: operacoes.render(user)))
        abas.append(("💼 Área do Gerente", lambda: gerente.render(user)))
        abas.append(("⚙️ Gerenciar Usuários", lambda: usuarios.render(user)))

    if abas:
        tabs = st.tabs([rotulo for rotulo, _ in abas])
        for tab, (_, render_fn) in zip(tabs, abas):
            with tab:
                render_fn()
    else:
        st.info("Não há telas disponíveis para o seu perfil de acesso.")