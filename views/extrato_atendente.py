"""Aba: Consulta de Contas (Atendente).

Conforme o enunciado: atendentes têm acesso de LEITURA aos números e saldos
das contas de sua mesma agência — nada de movimentações financeiras.
"""
import mysql.connector
import streamlit as st

from database import conectar_banco


def render(user):
    st.header("📋 Consulta de Contas da Agência")
    st.caption("Acesso de leitura: números e saldos das contas da sua agência.")

    conexao = conectar_banco()
    if conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            # user['matricula'] identifica o funcionário; pegamos a agência dele
            cursor.execute("SELECT num_ag FROM Funcionario WHERE matricula = %s", (user['matricula'],))
            res = cursor.fetchone()

            if not res:
                st.warning("Não foi possível identificar sua agência.")
                return

            num_ag = res['num_ag']

            cursor.execute(
                "SELECT num_conta, tipo_conta, saldo FROM Conta WHERE num_ag = %s ORDER BY num_conta",
                (num_ag,)
            )
            contas = cursor.fetchall()

            if contas:
                st.dataframe(contas, width="stretch")
            else:
                st.info("Nenhuma conta encontrada nesta agência.")
        except mysql.connector.Error as err:
            st.error(f"Erro ao consultar contas: {err}")
        finally:
            cursor.close()
            conexao.close()