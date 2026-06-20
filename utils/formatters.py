"""Funções utilitárias de formatação: CPF e datas em padrão brasileiro."""
import re
from datetime import date, datetime


def formatar_cpf(cpf):
    """Recebe um CPF (com ou sem máscara) e retorna no padrão 000.000.000-00."""
    if not cpf:
        return ""
    digitos = re.sub(r"\D", "", str(cpf))
    if len(digitos) != 11:
        return cpf  # devolve como veio se não tiver 11 dígitos (evita quebrar exibição)
    return f"{digitos[0:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:11]}"


def limpar_cpf(cpf):
    """Remove qualquer máscara e devolve só os números do CPF."""
    return re.sub(r"\D", "", str(cpf)) if cpf else ""


def formatar_data_br(valor):
    """Formata date/datetime/string (YYYY-MM-DD) para o padrão dd/mm/aaaa."""
    if valor is None or valor == "":
        return ""
    if isinstance(valor, (date, datetime)):
        return valor.strftime("%d/%m/%Y")
    # Tenta interpretar string vinda do banco (formato ISO)
    texto = str(valor)
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(texto, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return texto  # se não reconhecer o formato, devolve como veio


def formatar_datas_dataframe(resultados, colunas_data=None):
    """
    Recebe uma lista de dicts (resultado de cursor.execute com dictionary=True)
    e formata em padrão brasileiro as colunas de data informadas.
    Se colunas_data não for informado, detecta automaticamente colunas
    cujo nome contenha 'data' e cujo valor seja date/datetime.
    """
    if not resultados:
        return resultados

    if colunas_data is None:
        primeira_linha = resultados[0]
        colunas_data = [
            chave for chave, val in primeira_linha.items()
            if isinstance(val, (date, datetime)) or "data" in chave.lower()
        ]

    for linha in resultados:
        for col in colunas_data:
            if col in linha and linha[col] is not None:
                linha[col] = formatar_data_br(linha[col])
    return resultados