"""Telas de Login e Criação de Conta (fluxo de usuário deslogado)."""
from datetime import date

import streamlit as st

from auth import autenticar, cadastrar_cliente
from utils import formatar_cpf, limpar_cpf


def _aplicar_mascara_cpf():
    digitos = limpar_cpf(st.session_state["cad_cpf"])[:11]
    st.session_state["cad_cpf"] = formatar_cpf(digitos) if len(digitos) == 11 else digitos


def render():
    tab_login, tab_cadastro = st.tabs(["🔑 Login", "📝 Criar Conta"])

    with tab_login:
        st.markdown("<h3 style='text-align: center; color: #FF7676;'>🔑 Entrar no NullBank</h3>", unsafe_allow_html=True)
        username = st.text_input("Usuário (CPF ou Matrícula ou Username)", key="login_user")
        senha = st.text_input("Senha", type="password", key="login_pass")

        if st.button("Acessar Conta", width="stretch"):
            if not username or not senha:
                st.error("Por favor, preencha todos os campos.")
            else:
                usuario = autenticar(username, senha)
                if usuario:
                    st.session_state['usuario'] = usuario
                    st.success(f"Login realizado com sucesso! Bem-vindo(a), {usuario['nome']}.")
                    st.rerun()
                else:
                    st.error("Usuário não encontrado ou senha incorreta.")

    with tab_cadastro:
        st.markdown("<h3 style='text-align: center; color: #FF7676;'>📝 Cadastre-se como Cliente</h3>", unsafe_allow_html=True)
        nome = st.text_input("Nome Completo *", key="cad_name")
        cad_user = st.text_input("Nome de Usuário (login) *", key="cad_username")

        cpf_input = st.text_input(
            "CPF *",
            max_chars=14,
            key="cad_cpf",
            placeholder="000.000.000-00",
            on_change=_aplicar_mascara_cpf,
        )
        cpf = limpar_cpf(cpf_input)  # CPF "limpo" (só números) para salvar no banco
        cad_pass = st.text_input("Senha *", type="password", key="cad_password")
        data_nasc = st.date_input(
            "Data de Nascimento *",
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            value=None,
            format="DD/MM/YYYY",
            key="cad_birth",
        )

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

        if st.button("Criar Minha Conta", width="stretch"):
            if not nome or not cad_user or not cpf or not cad_pass or not data_nasc:
                st.error("Por favor, preencha todos os campos obrigatórios (*).")
            elif len(cpf) != 11 or not cpf.isdigit():
                st.error("O CPF deve conter exatamente 11 dígitos numéricos.")
            else:
                sucesso, mensagem, num_conta = cadastrar_cliente({
                    "cpf": cpf,
                    "nome": nome,
                    "cad_user": cad_user,
                    "cad_pass": cad_pass,
                    "data_nasc": data_nasc,
                    "email": email,
                    "telefone": telefone,
                    "rg_num": rg_num,
                    "rg_orgao": rg_orgao,
                    "rg_uf": rg_uf,
                    "tipo_log": tipo_log,
                    "nome_log": nome_log,
                    "numero": numero,
                    "complemento": complemento,
                    "bairro": bairro,
                    "cep": cep,
                    "cidade": cidade,
                    "estado": estado,
                })
                if sucesso:
                    st.success(f"🎉 {mensagem}")
                    st.info("Utilize a aba 'Login' para acessar.")
                else:
                    st.error(mensagem)