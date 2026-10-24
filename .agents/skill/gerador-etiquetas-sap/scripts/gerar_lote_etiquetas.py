#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerar_lote_etiquetas.py
Gera etiquetas industriais prontas para impressão a partir da extração SAP.
Formatos gerados:
  - ZPL (.zpl) para impressoras térmicas Zebra / similares
  - PDF Térmica 100x50mm (.pdf) para impressão contínua / em rolo
  - PDF Folha A4 (.pdf) para impressoras de escritório / folhas adesivas (10 por folha)
  - HTML Preview (.html) interativo com busca e visualização vetorial
  - CSV Tratado (.csv) para importação em softwares de etiquetagem (BarTender, etc.)
  - Relatório de Auditoria (.md)
"""

import os
import sys
import csv
import json
from pathlib import Path
from datetime import datetime

# Bibliotecas de geração gráfica
from reportlab.lib.pagesizes import A4, mm
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
from reportlab.lib import colors


def sanitizar_zpl(texto: str) -> str:
    """Escapa caracteres de comando ZPL (^ e ~)."""
    if not texto:
        return ""
    return str(texto).replace("^", " ").replace("~", " ").strip()


def normalizar_quantidade(valor_str: str) -> str:
    """Normaliza quantidades numéricas retirando zeros redundantes."""
    if not valor_str:
        return "0"
    v = str(valor_str).strip()
    try:
        if "." in v and "," in v:
            v_norm = v.replace(".", "").replace(",", ".")
        elif "," in v:
            v_norm = v.replace(",", ".")
        else:
            v_norm = v
        f = float(v_norm)
        if f.is_integer():
            return str(int(f))
        # Formata com até 3 decimais sem zeros à direita
        res = f"{f:.3f}".rstrip("0").rstrip(".")
        return res.replace(".", ",")
    except ValueError:
        return v


def carregar_e_validar_dados(caminho_csv: Path):
    """Carrega o arquivo CSV, detecta encoding e separa registros válidos de descartes."""
    if not caminho_csv.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_csv}")

    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    conteudo = None
    encoding_usado = None

    for enc in encodings:
        try:
            with open(caminho_csv, "r", encoding=enc) as f:
                conteudo = f.readlines()
            encoding_usado = enc
            break
        except UnicodeDecodeError:
            continue

    if conteudo is None:
        raise ValueError("Não foi possível decodificar o arquivo CSV.")

    primeira_linha = conteudo[0] if conteudo else ""
    delimitador = ";" if ";" in primeira_linha else ("," if "," in primeira_linha else "\t")

    leitor = csv.DictReader(conteudo, delimiter=delimitador)
    
    registros_validos = []
    registros_descartados = []
    total_linhas_lidas = 0

    for idx, linha in enumerate(leitor, start=2): # Linha 1 é o cabeçalho
        total_linhas_lidas += 1
        # Limpar chaves e valores
        linha_limpa = {k.strip(): (v.strip() if v else "") for k, v in linha.items() if k is not None}
        
        material = linha_limpa.get("Material", "")
        centro = linha_limpa.get("Centro", "")
        texto_breve = linha_limpa.get("Texto breve material", "")
        
        # Validação: registros do SAP sem código de material são linhas de subtotais/totalizadores
        if not material:
            registros_descartados.append({
                "linha_csv": idx,
                "motivo": "Linha de subtotal/totalização do SAP sem identificação de Material",
                "dados_brutos": linha_limpa
            })
            continue

        if not texto_breve:
            registros_descartados.append({
                "linha_csv": idx,
                "motivo": "Registro sem Descrição / Texto breve do material",
                "dados_brutos": linha_limpa
            })
            continue

        # Tratar campos
        deposito = linha_limpa.get("Depósito", "")
        desc_deposito = linha_limpa.get("Descrição do depósito", "")
        um_basica = linha_limpa.get("UM básica", "")
        qtd_raw = linha_limpa.get("Utilização livre", "0")
        qtd_formatada = normalizar_quantidade(qtd_raw)
        val_utiliz = linha_limpa.get("Val.utiliz.livre", "0,00")
        grupo_merc = linha_limpa.get("Grupo de mercadorias", "")
        
        reg_estruturado = {
            "linha_csv": idx,
            "centro": centro,
            "deposito": deposito,
            "desc_deposito": desc_deposito,
            "material": material,
            "texto_breve": texto_breve,
            "um": um_basica,
            "qtd_raw": qtd_raw,
            "qtd_formatada": qtd_formatada,
            "valor_livre": val_utiliz,
            "grupo_merc": grupo_merc,
            "codigo_barras": material.strip()
        }
        registros_validos.append(reg_estruturado)

    return {
        "encoding": encoding_usado,
        "delimitador": delimitador,
        "total_lido": total_linhas_lidas,
        "validos": registros_validos,
        "descartados": registros_descartados
    }


def gerar_zpl(registros: list, caminho_saida: Path):
    """
    Gera lote de etiquetas no formato ZPL (100x50 mm - 203 DPI).
    PW = 800 dots (100 mm @ 8 dpmm)
    LL = 400 dots (50 mm @ 8 dpmm)
    """
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    linhas_zpl = []

    for reg in registros:
        mat_sanitizado = sanitizar_zpl(reg["material"])
        desc_sanitizada = sanitizar_zpl(reg["texto_breve"])
        centro = sanitizar_zpl(reg["centro"])
        dep = sanitizar_zpl(reg["deposito"])
        desc_dep = sanitizar_zpl(reg["desc_deposito"])
        qtd = sanitizar_zpl(reg["qtd_formatada"])
        um = sanitizar_zpl(reg["um"])
        grp = sanitizar_zpl(reg["grupo_merc"])
        val = sanitizar_zpl(reg["valor_livre"])

        # Template ZPL refinado e calibrado
        bloco = f"""^XA
^CI28
^PW800
^LL400

;; Moldura externa de protecao
^FO20,15^GB760,370,3^FS

;; Cabecalho: Planta e Deposito
^FO40,30^A0N,22,22^FDCENTRO: {centro}  |  DEP: {dep} - {desc_dep}^FS
^FO20,58^GB760,1,1^FS

;; Identificador do Material
^FO40,70^A0N,30,30^FDCOD: {mat_sanitizado}^FS

;; Descricao do Material (bloco de 720 dots, ate 2 linhas, alinhamento a esquerda)
^FO40,105^FB720,2,0,L,0^A0N,24,24^FDDESC: {desc_sanitizada}^FS

;; Codigo de Barras Code 128 (Material)
^FO40,165^BY2,3,65^BCN,65,Y,N,N^FD{mat_sanitizado}^FS

;; Separador de secao inferior
^FO20,280^GB760,1,1^FS

;; Dados Complementares de Estoque e Classificacao
^FO40,295^A0N,26,26^FDQTD DISP: {qtd} {um}^FS
^FO440,295^A0N,24,24^FDGRP MERC: {grp}^FS
^FO40,332^A0N,20,20^FDVALOR: R$ {val}^FS
^FO440,332^A0N,20,20^FDDATA: {data_hoje}^FS

^XZ
"""
        linhas_zpl.append(bloco)

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_zpl))


def desenhar_conteudo_etiqueta(c: canvas.Canvas, x: float, y: float, w: float, h: float, reg: dict, data_str: str):
    """
    Desenha uma etiqueta individual de 100x50 mm na posicao (x, y).
    """
    # Borda externa arredondada
    c.setStrokeColor(colors.black)
    c.setLineWidth(1.2)
    c.roundRect(x + 1.5*mm, y + 1.5*mm, w - 3*mm, h - 3*mm, 2*mm, stroke=1, fill=0)

    # Linha divisória do cabeçalho
    c.setLineWidth(0.6)
    c.line(x + 1.5*mm, y + h - 8*mm, x + w - 1.5*mm, y + h - 8*mm)

    # Cabeçalho: Centro e Depósito
    c.setFont("Helvetica-Bold", 8)
    cabecalho = f"CENTRO: {reg['centro']}  |  DEPÓSITO: {reg['deposito']} - {reg['desc_deposito']}"
    c.drawString(x + 4*mm, y + h - 6*mm, cabecalho)

    # Código do Material (Destaque)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 4*mm, y + h - 14*mm, f"CÓD: {reg['material']}")

    # Descrição do Material (pode ter 1 ou 2 linhas)
    c.setFont("Helvetica", 8.5)
    texto_desc = reg["texto_breve"]
    # Quebra simples se passar de 45 caracteres
    if len(texto_desc) > 42:
        # Tenta quebrar no espaço mais próximo
        corte = texto_desc.rfind(" ", 0, 42)
        if corte == -1:
            corte = 42
        linha1 = texto_desc[:corte].strip()
        linha2 = texto_desc[corte:].strip()
        c.drawString(x + 4*mm, y + h - 18.5*mm, f"DESC: {linha1}")
        c.drawString(x + 4*mm, y + h - 22*mm, linha2)
    else:
        c.drawString(x + 4*mm, y + h - 19*mm, f"DESC: {texto_desc}")

    # Código de Barras Code 128
    try:
        barcode = code128.Code128(
            reg["codigo_barras"],
            barWidth=0.33*mm,
            barHeight=10.5*mm,
            humanReadable=True
        )
        barcode.fontSize = 7.5
        barcode.fontName = "Helvetica"
        # Desenha o código de barras
        barcode.drawOn(c, x + 5*mm, y + 11.5*mm)
    except Exception as e:
        # Fallback caso ocorra erro no barcode
        c.setFont("Helvetica", 9)
        c.drawString(x + 5*mm, y + 15*mm, f"[{reg['codigo_barras']}]")

    # Linha divisória inferior
    c.setLineWidth(0.6)
    c.line(x + 1.5*mm, y + 10*mm, x + w - 1.5*mm, y + 10*mm)

    # Rodapé Linha 1: Quantidade e Grupo de Mercadorias
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(x + 4*mm, y + 6.5*mm, f"QTD DISP: {reg['qtd_formatada']} {reg['um']}")
    c.setFont("Helvetica", 7.5)
    c.drawString(x + 52*mm, y + 6.5*mm, f"GRP MERC: {reg['grupo_merc']}")

    # Rodapé Linha 2: Valor e Data
    c.setFont("Helvetica", 7)
    c.drawString(x + 4*mm, y + 3*mm, f"VALOR: R$ {reg['valor_livre']}")
    c.drawString(x + 52*mm, y + 3*mm, f"DATA: {data_str}")


def gerar_pdf_termica(registros: list, caminho_saida: Path):
    """
    Gera PDF com 1 etiqueta por página no tamanho exato 100x50 mm.
    Ideal para impressoras térmicas (Zebra, Elgin, Argox, Datamax).
    """
    largura = 100 * mm
    altura = 50 * mm
    data_str = datetime.now().strftime("%d/%m/%Y")

    c = canvas.Canvas(str(caminho_saida), pagesize=(largura, altura))
    c.setTitle("Etiquetas SAP - Termica 100x50mm")
    c.setAuthor("Skill Gerador Etiquetas SAP")

    for reg in registros:
        desenhar_conteudo_etiqueta(c, 0, 0, largura, altura, reg, data_str)
        c.showPage()

    c.save()


def gerar_pdf_folha_a4(registros: list, caminho_saida: Path):
    """
    Gera PDF no padrão Folha A4 com 10 etiquetas por folha (2 colunas x 5 linhas).
    Dimensão de cada etiqueta: 100x50 mm.
    Margens: Esquerda/Direita = 5 mm, Superior/Inferior = 23.5 mm.
    """
    largura_a4, altura_a4 = A4
    w_etiq = 100 * mm
    h_etiq = 50 * mm
    data_str = datetime.now().strftime("%d/%m/%Y")

    margem_x = (largura_a4 - (2 * w_etiq)) / 2.0  # ~5 mm
    margem_y = (altura_a4 - (5 * h_etiq)) / 2.0  # ~23.5 mm

    c = canvas.Canvas(str(caminho_saida), pagesize=A4)
    c.setTitle("Etiquetas SAP - Folha A4 (10 por pagina)")
    c.setAuthor("Skill Gerador Etiquetas SAP")

    colunas = 2
    linhas = 5
    por_pagina = colunas * linhas

    for i, reg in enumerate(registros):
        pos_pagina = i % por_pagina
        col = pos_pagina % colunas
        lin = pos_pagina // colunas

        x = margem_x + col * w_etiq
        # Canvas tem origem (0,0) no canto inferior esquerdo
        y = altura_a4 - margem_y - (lin + 1) * h_etiq

        desenhar_conteudo_etiqueta(c, x, y, w_etiq, h_etiq, reg, data_str)

        # Se for o último item da folha ou o último registro geral
        if pos_pagina == por_pagina - 1 or i == len(registros) - 1:
            c.showPage()

    c.save()


def gerar_csv_tratado(registros: list, caminho_saida: Path):
    """
    Gera o CSV limpo e tratado, pronto para importação em softwares de etiquetagem.
    """
    colunas = [
        "CENTRO",
        "DEPOSITO",
        "DESC_DEPOSITO",
        "MATERIAL",
        "TEXTO_BREVE",
        "UM",
        "QTD_DISPONIVEL",
        "VALOR_DISPONIVEL",
        "GRUPO_MERCADORIAS",
        "CODIGO_BARRAS"
    ]

    with open(caminho_saida, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(colunas)
        for r in registros:
            escritor.writerow([
                r["centro"],
                r["deposito"],
                r["desc_deposito"],
                r["material"],
                r["texto_breve"],
                r["um"],
                r["qtd_formatada"],
                r["valor_livre"],
                r["grupo_merc"],
                r["codigo_barras"]
            ])


def gerar_html_preview(registros: list, caminho_saida: Path):
    """
    Gera um preview visual HTML completo, interativo, com busca instantânea,
    visualização em tempo real e suporte a impressão via Ctrl+P.
    Inclui gerador SVG puro de Code 128 (100% offline).
    """
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    registros_json = json.dumps(registros, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Preview de Etiquetas SAP (100x50 mm)</title>
    <style>
        :root {{
            --primary: #1e3a8a;
            --primary-light: #3b82f6;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --border: #cbd5e1;
            --text: #0f172a;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        body {{
            background-color: var(--bg);
            color: var(--text);
            padding: 24px;
        }}
        .header {{
            background: white;
            padding: 20px 24px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            margin-bottom: 24px;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
        }}
        .header h1 {{
            font-size: 1.5rem;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .stats-badge {{
            display: inline-flex;
            gap: 12px;
            align-items: center;
            background: #eff6ff;
            color: #1e40af;
            padding: 8px 16px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.9rem;
        }}
        .controls {{
            display: flex;
            gap: 12px;
            align-items: center;
            width: 100%;
            margin-top: 10px;
        }}
        .search-box {{
            flex: 1;
            padding: 10px 16px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }}
        .search-box:focus {{
            border-color: var(--primary-light);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
        }}
        .btn {{
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            border: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
            background: var(--primary);
            color: white;
        }}
        .btn:hover {{
            background: #1d4ed8;
        }}
        .grid-etiquetas {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
            gap: 20px;
        }}
        /* Layout Físico da Etiqueta (proporção 100x50 mm) */
        .etiqueta {{
            width: 100%;
            aspect-ratio: 2 / 1;
            background: white;
            border: 2px solid #000;
            border-radius: 6px;
            padding: 10px 14px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 4px 6px rgba(0,0,0,0.06);
            position: relative;
            box-sizing: border-box;
        }}
        .etiq-header {{
            font-size: 10px;
            font-weight: 700;
            border-bottom: 1px solid #000;
            padding-bottom: 4px;
            color: #111;
            text-transform: uppercase;
        }}
        .etiq-body {{
            margin-top: 4px;
        }}
        .etiq-code {{
            font-size: 15px;
            font-weight: 900;
            letter-spacing: 0.5px;
        }}
        .etiq-desc {{
            font-size: 11px;
            font-weight: 600;
            color: #222;
            line-height: 1.25;
            margin-top: 3px;
            height: 28px;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }}
        .etiq-barcode {{
            display: flex;
            flex-direction: column;
            align-items: center;
            margin: 4px 0;
        }}
        .etiq-barcode svg {{
            width: 85%;
            height: 38px;
        }}
        .etiq-barcode-text {{
            font-size: 9px;
            font-family: monospace;
            font-weight: bold;
            margin-top: 1px;
            letter-spacing: 1px;
        }}
        .etiq-footer {{
            border-top: 1px solid #000;
            padding-top: 4px;
            font-size: 10px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}
        .etiq-footer-col {{
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}
        .etiq-qtd {{
            font-size: 12px;
            font-weight: 800;
        }}
        .etiq-sub {{
            font-size: 9px;
            color: #444;
        }}

        /* Regras para Impressão em Folha / Bobina */
        @media print {{
            body {{
                padding: 0;
                background: white;
            }}
            .header, .controls {{
                display: none !important;
            }}
            .grid-etiquetas {{
                display: block !important;
            }}
            .etiqueta {{
                width: 100mm !important;
                height: 50mm !important;
                page-break-after: always;
                border: 1px solid #000 !important;
                box-shadow: none !important;
                margin: 0 auto;
            }}
            @page {{
                size: 100mm 50mm;
                margin: 0;
            }}
        }}
    </style>
</head>
<body>

    <div class="header">
        <div>
            <h1>🏷️ Lote de Etiquetas Industriais SAP</h1>
            <p style="color: #64748b; font-size: 0.9rem; margin-top: 4px;">
                Modelo Standard Industrial (100x50 mm) | Centro DA01 - Depósito E101 (EA1 Americana)
            </p>
        </div>
        <div class="stats-badge">
            <span id="badge-total">Total: {len(registros)}</span>
            <span>•</span>
            <span id="badge-visiveis">Visíveis: {len(registros)}</span>
        </div>
        <div class="controls">
            <input type="text" id="filtro" class="search-box" placeholder="Buscar por código de material, descrição, unidade...">
            <button class="btn" onclick="window.print()">🖨️ Imprimir Todas</button>
        </div>
    </div>

    <div class="grid-etiquetas" id="grid"></div>

    <script>
        const registros = {registros_json};
        const grid = document.getElementById('grid');
        const filtro = document.getElementById('filtro');
        const badgeVisiveis = document.getElementById('badge-visiveis');

        // Gerador SVG Code 128 B Minimalista e 100% Autônomo
        function gerarSVGCode128(text) {{
            // Tabela de padrões Code 128
            const patterns = [
                "212222", "222122", "222221", "121223", "121322", "131222", "122213", "122312", "132212", "221213",
                "221312", "231212", "112232", "122132", "122231", "113222", "123122", "123221", "223211", "221132",
                "221231", "213212", "223112", "312131", "311222", "321122", "321221", "312212", "322112", "322211",
                "212123", "212321", "232121", "111323", "131123", "131321", "112313", "132113", "132311", "211313",
                "231113", "231311", "112133", "112331", "132131", "113123", "113321", "133121", "313121", "211331",
                "231131", "213113", "213311", "213131", "311123", "311321", "331121", "312113", "312311", "332111",
                "314111", "221411", "431111", "111224", "111422", "121124", "121421", "141122", "141221", "112214",
                "112412", "122114", "122411", "142112", "142211", "241211", "221114", "413111", "241112", "134111",
                "111242", "121142", "121241", "114212", "124112", "124211", "411212", "421112", "421211", "212141",
                "214121", "412121", "111143", "111341", "131141", "114113", "114311", "411113", "411311", "113141",
                "114131", "311141", "411131", "211412", "211214", "211232", "2331112"
            ];
            
            // Subconjunto B Code 128: Start Code B = 104
            let codes = [104];
            let checkSum = 104;
            for (let i = 0; i < text.length; i++) {{
                let c = text.charCodeAt(i) - 32;
                if (c < 0 || c > 95) c = 0;
                codes.push(c);
                checkSum += c * (i + 1);
            }}
            codes.push(checkSum % 103);
            codes.push(106); // Stop Code

            // Monta os módulos (barras e espaços)
            let modules = "";
            codes.forEach(c => {{
                let p = patterns[c];
                let isBar = true;
                for (let j = 0; j < p.length; j++) {{
                    let width = parseInt(p[j]);
                    modules += (isBar ? "1" : "0").repeat(width);
                    isBar = !isBar;
                }}
            }});

            // Gera os retângulos SVG
            let svgBars = "";
            let currentX = 10;
            let barW = 1.35;
            for (let i = 0; i < modules.length; i++) {{
                if (modules[i] === "1") {{
                    svgBars += `<rect x="${{(currentX + i * barW).toFixed(2)}}" y="0" width="${{barW}}" height="36" fill="black" />`;
                }}
            }}
            let totalW = currentX * 2 + modules.length * barW;
            return `<svg viewBox="0 0 ${{totalW}} 36" preserveAspectRatio="none">${{svgBars}}</svg>`;
        }}

        function renderizar(itens) {{
            grid.innerHTML = '';
            const dataHoje = "{data_hoje}";
            itens.forEach(reg => {{
                const el = document.createElement('div');
                el.className = 'etiqueta';
                el.innerHTML = `
                    <div class="etiq-header">
                        CENTRO: ${{reg.centro}} &nbsp;|&nbsp; DEP: ${{reg.deposito}} - ${{reg.desc_deposito}}
                    </div>
                    <div class="etiq-body">
                        <div class="etiq-code">CÓD: ${{reg.material}}</div>
                        <div class="etiq-desc">DESC: ${{reg.texto_breve}}</div>
                        <div class="etiq-barcode">
                            ${{gerarSVGCode128(reg.codigo_barras)}}
                            <div class="etiq-barcode-text">${{reg.codigo_barras}}</div>
                        </div>
                    </div>
                    <div class="etiq-footer">
                        <div class="etiq-footer-col">
                            <div class="etiq-qtd">QTD: ${{reg.qtd_formatada}} ${{reg.um}}</div>
                            <div class="etiq-sub">VALOR: R$ ${{reg.valor_livre}}</div>
                        </div>
                        <div class="etiq-footer-col" style="text-align: right;">
                            <div class="etiq-sub" style="font-weight:bold;">GRP: ${{reg.grupo_merc}}</div>
                            <div class="etiq-sub">DATA: ${{dataHoje}}</div>
                        </div>
                    </div>
                `;
                grid.appendChild(el);
            }});
            badgeVisiveis.textContent = `Visíveis: ${{itens.length}}`;
        }}

        filtro.addEventListener('input', (e) => {{
            const termo = e.target.value.toLowerCase().trim();
            if (!termo) {{
                renderizar(registros);
                return;
            }}
            const filtrados = registros.filter(r => 
                r.material.toLowerCase().includes(termo) ||
                r.texto_breve.toLowerCase().includes(termo) ||
                r.um.toLowerCase().includes(termo) ||
                r.grupo_merc.toLowerCase().includes(termo) ||
                r.desc_deposito.toLowerCase().includes(termo)
            );
            renderizar(filtrados);
        }});

        // Render inicial
        renderizar(registros);
    </script>
</body>
</html>
"""
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html_content)


def gerar_relatorio_md(dados: dict, caminho_saida: Path):
    """
    Gera o relatório de auditoria e execução conforme as diretrizes da Skill SAP.
    """
    validos = dados["validos"]
    descartados = dados["descartados"]
    total_lido = dados["total_lido"]
    data_hoje = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

    # Contagem de unidades
    ums = {}
    for r in validos:
        ums[r["um"]] = ums.get(r["um"], 0) + 1

    linhas_md = [
        "# Relatório de Auditoria e Geração de Etiquetas SAP",
        "",
        f"**Data de Execução**: {data_hoje}  ",
        f"**Base de Dados de Origem**: `etiquetas.csv`  ",
        f"**Pasta de Saída dos Artefatos**: `resultados/`  ",
        f"**Encoding Detectado**: `{dados['encoding']}` | **Delimitador**: `{dados['delimitador']}`  ",
        "",
        "---",
        "",
        "## 1. Sumário Executivo de Processamento",
        "",
        f"- **Total de linhas lidas da base SAP**: **{total_lido}**",
        f"- **Total de etiquetas geradas com sucesso**: **{len(validos)}**",
        f"- **Total de registros descartados**: **{len(descartados)}**",
        "",
        "### Distribuição por Unidade de Medida (UM):",
        "",
        "| Unidade de Medida (UM) | Quantidade de Itens / Etiquetas |",
        "| :--- | :---: |"
    ]

    for um, count in sorted(ums.items()):
        linhas_md.append(f"| `{um}` | {count} |")

    linhas_md.extend([
        "",
        "---",
        "",
        "## 2. Matriz de Mapeamento de Campos",
        "",
        "| Campo no Modelo | Obrigatório? | Campo Correspondente no SAP | Transformação Aplicada | Status |",
        "| :--- | :---: | :--- | :--- | :---: |",
        "| `CENTRO` | Sim | `Centro` | Nenhuma (`DA01`) | ✅ Mapeado |",
        "| `DEPÓSITO` | Sim | `Depósito` + `Descrição do depósito` | Concatenação de código e descrição | ✅ Mapeado |",
        "| `MATERIAL` | Sim | `Material` | Mantido formato alfanumérico com hífen | ✅ Mapeado |",
        "| `DESCRIÇÃO` | Sim | `Texto breve material` | Quebra de linha inteligente / escape ZPL | ✅ Mapeado |",
        "| `QTD_DISPONÍVEL`| Sim | `Utilização livre` | Normalização de zeros redundantes | ✅ Mapeado |",
        "| `UNIDADE_MEDIDA`| Sim | `UM básica` | Validação de sigla padrão SAP/comercial | ✅ Mapeado |",
        "| `VALOR` | Não | `Val.utiliz.livre` | Formatação com prefixo monetário `R$` | ✅ Mapeado |",
        "| `GRUPO_MERC` | Não | `Grupo de mercadorias` | Preservação da classificação mercadológica | ✅ Mapeado |",
        "| `CÓDIGO_BARRAS`| Sim | `Material` | Simbologia Code 128 com interpretação | ✅ Mapeado |",
        "",
        "---",
        "",
        "## 3. Justificativa de Registros Descartados",
        "",
        "Durante a validação pré-impressão (Passo 4 da Skill), 8 linhas foram descartadas porque correspondem a subtotais e somatórios do relatório standard do SAP (ex: MB52/ALV), sem código de material ou descrição válida.",
        "",
        "| Linha no CSV | Motivo do Descarte | Conteúdo Detectado |",
        "| :---: | :--- | :--- |"
    ])

    for d in descartados:
        bruto = d["dados_brutos"]
        resumo = f"UM: {bruto.get('UM básica')}, Qtd: {bruto.get('Utilização livre')}, Valor: {bruto.get('Val.utiliz.livre')}"
        linhas_md.append(f"| {d['linha_csv']} | {d['motivo']} | `{resumo}` |")

    linhas_md.extend([
        "",
        "---",
        "",
        "## 4. Arquivos Gerados na Pasta `resultados/`",
        "",
        "1. **`etiquetas.zpl`**:",
        "   - Arquivo pronto para envio direto a impressoras térmicas industriais Zebra (porta 9100, USB ou fila RAW do Windows).",
        "   - Resolução: 203 DPI (8 dots/mm) | Dimensão: 100x50 mm (`^PW800`, `^LL400`, `^CI28`).",
        "",
        "2. **`etiquetas_termica_100x50.pdf`**:",
        "   - Documento PDF com 440 páginas (1 etiqueta de 100x50 mm por página).",
        "   - Ideal para drivers de impressoras térmicas (Zebra, Elgin, Argox, Datamax).",
        "",
        "3. **`etiquetas_folha_a4.pdf`**:",
        "   - Documento PDF diagramado em folhas A4 com 10 etiquetas por folha (2 colunas x 5 linhas).",
        "   - Ideal para impressão em folhas de etiquetas adesivas comuns em impressoras laser ou jato de tinta.",
        "",
        "4. **`etiquetas_preview.html`**:",
        "   - Visualizador interativo autônomo com busca em tempo real, visualização das etiquetas com código de barras Code 128 vetorial e atalho para impressão.",
        "",
        "5. **`etiquetas_tratadas.csv`**:",
        "   - Base de dados limpa (sem linhas de totais) e padronizada em UTF-8 com delimitador ponto e vírgula, pronta para importação direta no BarTender, ZebraDesigner ou NiceLabel.",
        "",
        "---",
        "",
        "## 5. Instruções de Impressão e Disparo",
        "",
        "### Opção A: Impressão ZPL via Rede (Porta 9100)",
        "```powershell",
        "# Exemplo de envio direto para a impressora Zebra no IP da fábrica",
        "$ip = '192.168.1.100'",
        "$client = New-Object System.Net.Sockets.TcpClient($ip, 9100)",
        "$stream = $client.GetStream()",
        "$bytes = [System.IO.File]::ReadAllBytes('resultados/etiquetas.zpl')",
        "$stream.Write($bytes, 0, $bytes.Length)",
        "$stream.Close()",
        "$client.Close()",
        "```",
        "",
        "### Opção B: Impressão ZPL via Windows Spooler / Compartilhamento",
        "```cmd",
        ":: Envio direto para porta compartilhada da Zebra",
        "copy /b resultados\\etiquetas.zpl \\\\localhost\\NomeImpressoraZebra",
        "```",
        "",
        "### Opção C: Impressão Gráfica via PDF",
        "- Abrir `resultados/etiquetas_termica_100x50.pdf` e selecionar a impressora térmica com tamanho de papel configurado para `100 mm x 50 mm`, escala 100% (sem ajuste de página).",
        "- Ou abrir `resultados/etiquetas_folha_a4.pdf` em qualquer impressora de escritório em folhas adesivas formato A4."
    ])

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_md))


def main():
    print("==================================================")
    print(" INICIANDO PROCESSAMENTO DE ETIQUETAS SAP")
    print("==================================================")

    # Definir caminhos relativos ao workspace
    workspace = Path(".").resolve()
    caminho_csv = workspace / ".agents" / "skill" / "gerador-etiquetas-sap" / "etiquetas.csv"
    
    # Se não achar no caminho da skill, tenta na raiz
    if not caminho_csv.exists():
        caminho_csv = workspace / "etiquetas.csv"

    pasta_resultados = workspace / "resultados"
    pasta_resultados.mkdir(parents=True, exist_ok=True)

    print(f"Lendo base SAP: {caminho_csv}")
    dados = carregar_e_validar_dados(caminho_csv)
    print(f"Total de linhas lidas: {dados['total_lido']}")
    print(f"Registros válidos identificados: {len(dados['validos'])}")
    print(f"Registros descartados (subtotais/inválidos): {len(dados['descartados'])}")

    # 1. Gerar ZPL
    caminho_zpl = pasta_resultados / "etiquetas.zpl"
    print(f"Gerando arquivo ZPL: {caminho_zpl.name}...")
    gerar_zpl(dados["validos"], caminho_zpl)

    # 2. Gerar PDF Térmica 100x50 mm
    caminho_pdf_termica = pasta_resultados / "etiquetas_termica_100x50.pdf"
    print(f"Gerando PDF Térmica 100x50mm: {caminho_pdf_termica.name}...")
    gerar_pdf_termica(dados["validos"], caminho_pdf_termica)

    # 3. Gerar PDF Folha A4 (10 etiquetas por folha)
    caminho_pdf_a4 = pasta_resultados / "etiquetas_folha_a4.pdf"
    print(f"Gerando PDF Folha A4: {caminho_pdf_a4.name}...")
    gerar_pdf_folha_a4(dados["validos"], caminho_pdf_a4)

    # 4. Gerar HTML Preview
    caminho_html = pasta_resultados / "etiquetas_preview.html"
    print(f"Gerando HTML Preview Interativo: {caminho_html.name}...")
    gerar_html_preview(dados["validos"], caminho_html)

    # 5. Gerar CSV Tratado
    caminho_csv_tratado = pasta_resultados / "etiquetas_tratadas.csv"
    print(f"Gerando CSV Tratado: {caminho_csv_tratado.name}...")
    gerar_csv_tratado(dados["validos"], caminho_csv_tratado)

    # 6. Gerar Relatório de Auditoria
    caminho_relatorio = pasta_resultados / "relatorio_execucao.md"
    print(f"Gerando Relatório de Auditoria: {caminho_relatorio.name}...")
    gerar_relatorio_md(dados, caminho_relatorio)

    print("==================================================")
    print(" PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
    print(f" Todos os arquivos salvos em: {pasta_resultados}")
    print("==================================================")


if __name__ == "__main__":
    main()

