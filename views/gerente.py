"""Aba: Área do Gerente."""
import mysql.connector
import streamlit as st

from database import conectar_banco
from utils import formatar_datas_dataframe


def render():
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
                    resultados = formatar_datas_dataframe(resultados)
                    st.dataframe(resultados, use_container_width=True)
                else:
                    st.info("Nenhuma conta encontrada.")
            except mysql.connector.Error as err:
                st.error(f"Erro ao carregar relatório: {err}")
            finally:
                cursor.close()
                conexao.close()