import streamlit as st
import mysql.connector

# FUNÇÃO PARA CONECTAR AO BANCO DE DADOS

def conectar_banco():
    try:
        conexao = mysql.connector.connect(
            host="100.99.168.13",  
            user="root",  
            password="Root",
            database="Equipe567258",
            port=3306,
            auth_plugin='mysql_native_password',
            connection_timeout=5,
            use_pure=True
        )
        return conexao
    except mysql.connector.Error as err:
        st.error(f"Erro ao conectar ao banco de dados: {err}")
        return None


# CONFIGURAÇÕES DA TELA E ESTILO

st.set_page_config(page_title="NullBank", page_icon="🏦", layout="centered")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 NullBank - Sistema Bancário")
st.write("Bem-vindo ao sistema de autoatendimento.")


# MENU SUPERIOR (TABS)

# Isso cria as 3 abas lado a lado no topo da tela
tab1, tab2, tab3 = st.tabs(["📊 Consultar Extrato", "💸 Fazer Transferência", "💼 Área do Gerente"])


# ABA 1: EXTRATO

with tab1:
    st.header("Consulta de Extrato")
    conta = st.text_input("Digite o número da sua conta:")
    
    if st.button("Buscar Extrato"):
        if conta:
            conexao = conectar_banco()
            if conexao:
                cursor = conexao.cursor(dictionary=True) 
                cursor.execute("SELECT * FROM v_extrato_completo WHERE num_conta = %s ORDER BY data_hora DESC", (conta,))
                resultados = cursor.fetchall()
                
                if resultados:
                    st.success(f"Extrato da conta {conta} carregado!")
                    st.dataframe(resultados, use_container_width=True) 
                else:
                    st.warning("Nenhuma transação encontrada para esta conta.")
                
                cursor.close()
                conexao.close()
        else:
            st.warning("Por favor, digite o número da conta.")


# ABA 2: TRANSFERÊNCIA

with tab2:
    st.header("Transferência Bancária")
    
    conta_origem = st.text_input("Sua Conta (Origem):")
    conta_destino = st.text_input("Conta de Destino:")
    valor = st.number_input("Valor da Transferência (R$):", min_value=0.01)
    
    if st.button("Confirmar Transferência"):
        if conta_origem and conta_destino and valor > 0:
            conexao = conectar_banco()
            
            if conexao:
                cursor = conexao.cursor()
                try:
                    c_origem = int(conta_origem)
                    c_destino = int(conta_destino)
                    v_transf = float(valor)
                    
                    import random
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


# ABA 3: GERENTE

with tab3:
    st.header("Painel do Gerente")
    st.write("Visão geral de todas as contas e titulares cadastrados.")
    
    if st.button("Carregar Relatório de Contas"):
        conexao = conectar_banco()
        
        if conexao:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT * FROM v_contas_gerente")
            resultados = cursor.fetchall()
            
            if resultados:
                st.dataframe(resultados, use_container_width=True)
            else:
                st.info("Nenhuma conta encontrada.")
                
            cursor.close()
            conexao.close()