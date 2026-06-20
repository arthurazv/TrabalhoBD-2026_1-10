"""Conexão com o banco de dados MySQL."""
import mysql.connector
import streamlit as st

from config import carregar_config_banco


def conectar_banco():
    """Abre e retorna uma conexão com o MySQL, ou None em caso de erro."""
    config = carregar_config_banco()
    try:
        conexao = mysql.connector.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            port=config["port"],
            auth_plugin='mysql_native_password',
            connection_timeout=5,
            use_pure=True
        )
        return conexao
    except mysql.connector.Error as err:
        st.error(f"Erro ao conectar ao banco de dados: {err}")
        return None