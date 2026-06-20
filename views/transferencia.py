"""Aba: Fazer Transferência."""
import random

import mysql.connector
import streamlit as st

from database import conectar_banco
from auth import obter_contas_usuario


def render(user):
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