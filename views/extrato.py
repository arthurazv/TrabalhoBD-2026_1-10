"""Aba: Consultar Extrato."""
import mysql.connector
import streamlit as st

from database import conectar_banco
from auth import obter_contas_usuario
from utils import formatar_datas_dataframe


def render(user):
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
                        resultados = formatar_datas_dataframe(resultados)
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