#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validador_etiquetas.py
Script auxiliar para carregar arquivos de dados exportados do SAP,
validar campos contra um modelo de etiqueta, aplicar transformações padronizadas
e gerar o arquivo final pronto para impressão ou uso.
"""

import os
import sys
import csv
import re
from datetime import datetime
from pathlib import Path


def formatar_material_sap(valor: str) -> str:
    """Remove zeros à esquerda de códigos numéricos (equivalente a ALPHA_OUTPUT)."""
    if not valor:
        return ""
    v = str(valor).strip()
    if v.isdigit():
        return v.lstrip("0") or "0"
    return v


def formatar_data_sap(valor: str) -> str:
    """Converte datas padrão SAP (YYYYMMDD ou YYYY-MM-DD) para DD/MM/AAAA."""
    if not valor:
        return ""
    v = str(valor).strip()
    # Padrão YYYYMMDD
    if re.match(r"^\d{8}$", v):
        try:
            dt = datetime.strptime(v, "%Y%m%d")
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            return v
    # Padrão YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", v):
        try:
            dt = datetime.strptime(v, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            return v
    return v


def formatar_quantidade_sap(valor: str) -> str:
    """Remove zeros decimais redundantes de quantidades (ex: 50.000 -> 50)."""
    if not valor:
        return ""
    v = str(valor).strip()
    try:
        # Se contiver virgula e ponto, normalizar
        if "." in v and "," in v:
            # Ex: 1.250,50
            v_norm = v.replace(".", "").replace(",", ".")
        elif "," in v:
            v_norm = v.replace(",", ".")
        else:
            v_norm = v
        f = float(v_norm)
        if f.is_integer():
            return str(int(f))
        return f"{f:g}".replace(".", ",")
    except ValueError:
        return v


def sanitizar_zpl(texto: str) -> str:
    """Escapa caracteres que afetam comandos ZPL (^ e ~)."""
    if not texto:
        return ""
    # Evita quebra de comandos no motor Zebra
    return texto.replace("^", " ").replace("~", " ")


def carregar_dados_sap(caminho_arquivo: str) -> list[dict]:
    """Lê arquivo CSV ou TXT delimitado exportado do SAP."""
    caminho = Path(caminho_arquivo)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

    # Detecção de encoding
    encodings = ["utf-8", "latin-1", "cp1252"]
    conteudo = None
    for enc in encodings:
        try:
            with open(caminho, "r", encoding=enc) as f:
                linhas = f.readlines()
            conteudo = linhas
            break
        except UnicodeDecodeError:
            continue

    if conteudo is None:
        raise ValueError("Não foi possível decodificar o arquivo com UTF-8 ou Latin-1.")

    # Detecção de delimitador
    primeira_linha = conteudo[0] if conteudo else ""
    delimitador = ";" if ";" in primeira_linha else ("," if "," in primeira_linha else "\t")

    leitor = csv.DictReader(conteudo, delimiter=delimitador)
    registros = []
    for linha in leitor:
        # Limpar espacos nos nomes das chaves e valores
        linha_limpa = {k.strip(): v.strip() for k, v in linha.items() if k is not None}
        registros.append(linha_limpa)

    return registros


def main():
    print("Script de validação e transformação de etiquetas SAP iniciado.")
    # Exemplo de chamada e interface
    if len(sys.argv) > 1:
        caminho = sys.argv[1]
        try:
            dados = carregar_dados_sap(caminho)
            print(f"Total de registros carregados: {len(dados)}")
            if dados:
                print(f"Campos identificados: {list(dados[0].keys())}")
        except Exception as e:
            print(f"Erro ao processar arquivo: {e}")
    else:
        print("Uso: python validador_etiquetas.py <caminho_base_sap.csv>")


if __name__ == "__main__":
    main()

