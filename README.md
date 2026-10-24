# 🏷️ SmartLabel Pro - Studio de Etiquetas Industriais SAP

[![Render](https://img.shields.io/badge/Render-Deploy%20Ready-46E3B7?style=flat-square&logo=render&logoColor=white)](https://render.com)
[![Static Site](https://img.shields.io/badge/Tipo-Static%20Site-blue?style=flat-square)](https://render.com)
[![HTML5 / Vanilla JS](https://img.shields.io/badge/Stack-HTML5%20%2F%20JS%20%2F%20CSS-orange?style=flat-square)](https://developer.mozilla.org)
[![Licença](https://img.shields.io/badge/Licen%C3%A7a-Propriet%C3%A1ria-green?style=flat-square)](#)

Aplicativo web autônomo e intuitivo para geração, pré-visualização física, personalização e impressão de etiquetas industriais e logísticas a partir de dados exportados do SAP.

---

## 🚀 Como Fazer o Deploy no Render (Static Site)

O software já está preparado para deploy imediato no **Render**:

1. Acesse o seu painel no [Render Dashboard](https://dashboard.render.com).
2. Clique em **New +** e selecione **Static Site**.
3. Conecte o repositório: `https://github.com/besklona-TI/software-etiquetas.git`.
4. Preencha as configurações:
   - **Name**: `software-etiquetas` (ou o nome que preferir)
   - **Branch**: `main`
   - **Build Command**: *(deixe vazio)*
   - **Publish Directory**: `./` *(ou `./app`)*
5. Clique em **Create Static Site**.
6. Em poucos segundos o Render publicará a sua URL (ex: `https://software-etiquetas.onrender.com`).

> *Nota: O repositório já inclui o arquivo `render.yaml` configurado, permitindo também o deploy automático via Blueprint.*

---

## 💻 Como Usar Localmente (Na Empresa)

### Opção 1: Atalho em 1 Clique (Windows)
Basta dar um duplo clique no arquivo:
👉 **`INICIAR_APLICATIVO.bat`**

O script detecta automaticamente se há Python no computador para iniciar o servidor local de rede ou abre diretamente no navegador padrão em modo autônomo.

### Opção 2: Servidor Python
```bash
python servidor.py
```
Acesse `http://localhost:8080` no navegador.

### Opção 3: Modo 100% Offline
Basta abrir o arquivo `index.html` em qualquer navegador (Chrome, Edge, Firefox, Safari). Não requer conexão com a internet nem instalação de dependências.

---

## ✨ Principais Funcionalidades

- **📦 Catálogo SAP com Busca Instantânea**: 440 materiais pré-carregados da base `etiquetas.csv`, com filtros inteligentes por Unidade de Medida (`PC`, `KG`, `PAR`, `JG`, `M`, `UN`).
- **👁️ Live Preview Físico (100x50 mm - 203 DPI)**: Simulação visual de alta fidelidade da etiqueta com moldura, cabeçalho da planta, descrição em bloco e código de barras nítido.
- **🔄 Alternador de Simbologia**: Alterne entre **Código 128 (barras 1D)** e **QR Code (2D)** com apenas 1 clique.
- **🖨️ Impressão Multiformato**:
  - **Térmica Direta (100x50 mm)**: Bobinas térmicas contínuas para impressoras Zebra, Elgin, Argox e Datamax.
  - **Folha Adesiva A4**: Grade com 10 etiquetas por folha (2 colunas x 5 linhas) para impressoras laser/jato de tinta comuns de escritório.
  - **Exportação ZPL**: Geração de comandos originais Zebra (`.zpl`) para importação em ZebraDesigner ou envio via RAW spooler.
- **✍️ Criador de Etiquetas Avulsas**: Permite criar e imprimir etiquetas na hora para peças de reposição ou novos itens recebidos.
- **📡 Disparo Direto para Impressora Zebra na Rede**: Envio direto de comandos ZPL para o IP da impressora via socket TCP na porta 9100.
- **📤 Importação Drag & Drop**: Arraste e solte novos arquivos CSV exportados do SAP para atualizar os dados a qualquer momento.

---

## 📁 Estrutura do Repositório

```text
├── index.html                # Aplicação web principal (ponto de entrada Render)
├── styles.css                # Estilos modernos e regras de impressão (@media print)
├── app.js                    # Motor JavaScript, geradores SVG de código e lógica ZPL
├── dados_padrao.js           # Base de dados pré-carregada (440 itens SAP)
├── INICIAR_APLICATIVO.bat    # Executável de inicialização rápida no Windows
├── servidor.py               # Servidor local leve com socket TCP para Zebra IP
├── render.yaml               # Arquivo de configuração de infraestrutura do Render
├── app/                      # Cópia modular da aplicação
├── resultados/               # Lote gerado anteriormente (ZPL, PDFs, CSV tratado)
└── .agents/                  # Skill original do gerador de etiquetas SAP
```

---

Desenvolvido para máxima facilidade de uso em ambientes corporativos e industriais.
