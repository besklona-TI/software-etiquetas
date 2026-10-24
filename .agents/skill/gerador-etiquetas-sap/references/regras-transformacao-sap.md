# Guia de Transformações e Tratamento de Campos SAP

Este documento reúne os padrões mais frequentes de campos SAP encontrados em extrações de dados e suas regras recomendadas de transformação para etiquetas físicas.

---

## 1. Campos Numéricos com Zeros à Esquerda (Rotina ALPHA_OUTPUT)

No banco de dados do SAP, muitos campos de chave numérica são gravados com comprimento fixo e preenchidos com zeros à esquerda.

| Campo SAP Técnico | Descrição Típica | Valor no SAP (Raw) | Valor Transformado para Etiqueta | Regra Aplicada |
| :--- | :--- | :--- | :--- | :--- |
| `MATNR` | Código do Material | `000000000010023456` | `10023456` | `valor.lstrip('0')` |
| `KUNNR` | Código do Cliente | `0000109988` | `109988` | `valor.lstrip('0')` |
| `LIFNR` | Código do Fornecedor | `0000054321` | `54321` | `valor.lstrip('0')` |
| `VBELN` | Documento de Vendas / Remessa | `0080012345` | `80012345` | `valor.lstrip('0')` |

> [!NOTE]
> Se o código for alfanumérico (ex: `PECA-00123`), a remoção de zeros não deve ser aplicada. Verifique se o conteúdo contém apenas dígitos antes de aplicar o `lstrip`.

---

## 2. Datas e Horários

No SAP, datas costumam ser armazenadas internamente no formato `YYYYMMDD` (formato ABAP `DATUM`), ou formatadas de acordo com as configurações do usuário (`DD.MM.YYYY`, `MM/DD/YYYY`, etc.).

| Campo SAP | Formato Origem | Formato Destino | Exemplo Entrada | Exemplo Saída |
| :--- | :--- | :--- | :--- | :--- |
| `VFDAT` (Data de Validade) | `YYYYMMDD` | `DD/MM/AAAA` | `20270515` | `15/05/2027` |
| `HSDAT` (Data de Fabricação) | `YYYYMMDD` | `DD/MM/AAAA` | `20261024` | `24/10/2026` |
| `ERDAT` (Data de Criação) | `YYYY-MM-DD` | `DD/MM/AAAA` | `2026-10-24` | `24/10/2026` |

---

## 3. Unidades de Medida (Conversão de ISO/SAP para Comercial)

O SAP frequentemente utiliza chaves internas para unidades de medida (tabela `T006`):

| Unidade SAP | Descrição | Sigla Comercial Sugerida |
| :--- | :--- | :--- |
| `ST` | Stück (Unidade / Peça) | `UN` ou `PC` |
| `KG` | Quilograma | `KG` |
| `M` | Metro | `M` |
| `L` | Litro | `L` |
| `PAK` | Pacote | `PCT` ou `CX` |

> [!IMPORTANT]
> A conversão de unidades deve ser validada com o usuário antes de ser fixada no modelo final.

---

## 4. Quantidades e Casas Decimais

- **Remoção de zeros decimais redundantes**: `10.000` $\rightarrow$ `10` se a unidade for inteira (`UN`).
- **Separador decimal**: No Brasil, comumente utiliza-se a vírgula para impressão legível (`12,5 kg`), enquanto em códigos de barras de padrão GS1 utiliza-se notação específica.

---

## 5. Limites de Texto e Quebras de Linha

- **Descrição de Material (`MAKTX` / `ARKTX`)**:
  - Máximo de 40 caracteres no SAP standard.
  - Para caixas de texto com largura limitada na etiqueta:
    1. Utilizar comando `^FB` (Field Block) no ZPL para quebra automática de linha sem cortar palavras ao meio.
    2. Se o texto ultrapassar o número máximo de linhas reservado no layout, propor truncamento com reticências (`...`) ou redução de fonte, sem alterar informações vitais (como dimensões, voltagem ou especificações).

---

## 6. Cuidados Específicos com Sintaxe ZPL (Zebra)

1. **Caracteres de Controle**:
   - `^` (Carets) e `~` (Tildes) são interpretados pelo motor ZPL como comandos.
   - Caso o dado do SAP contenha esses caracteres, ative o modo hexadecimal com `^FH\` e envie o código correspondente (`_5E` para `^`, `_7E` para `~`).
2. **Acentuação e Caracteres Especiais (`UTF-8` vs `CP850`)**:
   - Para etiquetas com acentos em português (ex: `ç`, `ã`, `é`), inclua o comando `^CI28` no início do cabeçalho da etiqueta para garantir interpretação correta de caracteres UTF-8 pela impressora.
3. **Códigos de Barras**:
   - Code 128: Usar comando `^BC` (pode exigir formato de invocação de subsets `>:` ou `>;`).
   - QR Code: Usar `^BQ,2,10`.

