"""Aba: Gerenciar Usuários (promoção de cargos)."""
import mysql.connector
import streamlit as st

from database import conectar_banco
from auth import promover_usuario
from utils import formatar_cpf


def render(user):
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
                        st.markdown(
                            f"<small style='color: #8A8AAB;'>CPF: {formatar_cpf(u['cpf']) if u['cpf'] else 'N/A'} | "
                            f"Matrícula: {u['matricula'] or 'N/A'}</small>",
                            unsafe_allow_html=True
                        )
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