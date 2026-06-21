"""Aba: Operações Financeiras (Saque e Depósito).

Conforme o enunciado: apenas os caixas (ou administrador) podem efetuar
operações financeiras como saques e depósitos, e somente em contas de sua
própria agência (no caso de caixas).
"""
import mysql.connector
import streamlit as st

from database import conectar_banco
from auth import obter_agencia_funcionario, conta_pertence_a_agencia


def render(user):
    st.header("💵 Saques e Depósitos")
    st.write("Realize depósitos ou saques em dinheiro diretamente na conta do cliente.")

    # 1. Selecionar o tipo de operação
    operacao = st.selectbox(
        "Tipo de Operação:",
        ["depósito", "saque"],
        format_func=lambda x: x.capitalize(),
        key="op_tipo"
    )

    # 2. Entrada da conta
    if user['role'] == 'caixa':
        st.caption("Nota: Você só pode movimentar contas da sua própria agência.")
    
    conta_input = st.text_input("Número da Conta:", key="op_conta")
    valor = st.number_input("Valor da Operação (R$):", min_value=0.01, step=10.0, key="op_valor")

    if st.button("Confirmar Operação", key="btn_confirmar_op"):
        if not conta_input:
            st.error("Por favor, digite o número da conta.")
            return

        try:
            num_conta = int(conta_input)
        except ValueError:
            st.error("O número da conta deve ser um valor numérico.")
            return

        if valor <= 0:
            st.error("O valor da operação deve ser maior que zero.")
            return

        # Validação de Agência para Caixas
        if user['role'] == 'caixa':
            num_ag = obter_agencia_funcionario(user['matricula'])
            if num_ag is None:
                st.error("Não foi possível identificar a agência vinculada ao seu cadastro.")
                return
            if not conta_pertence_a_agencia(num_conta, num_ag):
                st.error("Erro: Esta conta não pertence à sua agência.")
                return

        # Realizar transação no Banco de Dados
        conexao = conectar_banco()
        if conexao:
            cursor = conexao.cursor()
            try:
                # 1. Obter o próximo num_transacao para a conta
                cursor.execute(
                    "SELECT IFNULL(MAX(num_transacao), 0) + 1 FROM Transacao WHERE num_conta = %s",
                    (num_conta,)
                )
                prox_num_trans = cursor.fetchone()[0]

                # 2. Inserir a transação (o trigger tg_atualizar_saldo_transacao cuidará da atualização do saldo e da validação de limite)
                cursor.execute(
                    """
                    INSERT INTO Transacao (num_transacao, num_conta, tipo, data_hora, valor)
                    VALUES (%s, %s, %s, NOW(), %s)
                    """,
                    (prox_num_trans, num_conta, operacao, valor)
                )
                conexao.commit()

                st.success(f"✅ Operação de {operacao.capitalize()} de R$ {valor:.2f} na conta {num_conta} realizada com sucesso!")
            except mysql.connector.Error as err:
                conexao.rollback()
                # O trigger lança mensagens de erro amigáveis usando SIGNAL SQLSTATE '45000'
                st.error(f"❌ Operação Rejeitada: {err.msg}")
            finally:
                cursor.close()
                conexao.close()
