"""Carregamento de variáveis de ambiente e configuração de conexão com o banco."""
import os
import streamlit as st

REQUIRED_ENV_VARS = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]


def carregar_env():
    """Carrega o arquivo .env manualmente, se existir (uso em desenvolvimento local)."""
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        val = val.strip().strip("'\"")
                        os.environ[key.strip()] = val


def carregar_config_banco():
    """Valida e retorna o dicionário de configuração de conexão com o MySQL."""
    faltando = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if faltando:
        st.error(
            "Configuração incompleta: variáveis de ambiente ausentes: "
            f"{', '.join(faltando)}. Verifique o arquivo .env do stack e reinicie o container."
        )
        st.stop()

    return {
        "host": os.environ["DB_HOST"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
        "database": os.environ["DB_NAME"],
        "port": int(os.environ.get("DB_PORT", 3306)),
    }