# Exemplo Prático: Mapeamento de Template ZPL e Base SAP

Este exemplo demonstra como estruturar um template ZPL com marcadores de posição (placeholders) e como os dados extraídos do SAP preenchem cada campo.

---

## 1. Dados de Exemplo do SAP (CSV)

```csv
MATNR;MAKTX;CHARG;MENGE;MEINS;VFDAT;WERKS
000000000010045678;CABO DE COBRE ISOLADO 10MM 750V AZUL;LT2026A;50.000;M;20281231;1001
000000000010045679;CONECTOR METALICO TERMINAL OLHAL 10MM;LT2026B;100.000;ST;20290630;1001
```

---

## 2. Template ZPL Base (100x50 mm - 203 DPI)

Template com placeholders entre chaves `{...}`:

```zpl
^XA
^CI28
^PW800
^LL400

;; Borda da Etiqueta
^FO20,20^GB760,360,3^FS

;; Cabecalho da Empresa / Planta
^FO40,40^A0N,28,28^FDPLANTA: {WERKS}^FS

;; Codigo do Material (Formatado sem zeros)
^FO40,80^A0N,32,32^FDCOD: {MATNR_FORMATADO}^FS

;; Descricao do Material (com quebra automatica em bloco)
^FO40,120^FB720,2,0,L,0^A0N,26,26^FDDESC: {MAKTX}^FS

;; Codigo de Barras Code 128 (Material)
^FO40,180^BY2,3,60^BCN,60,Y,N,N^FD{MATNR_FORMATADO}^FS

;; Lote e Validade
^FO40,280^A0N,28,28^FDLOTE: {CHARG}^FS
^FO400,280^A0N,28,28^FDVAL: {VFDAT_FORMATADO}^FS

;; Quantidade e Unidade Comercial
^FO40,320^A0N,28,28^FDQTD: {MENGE_FORMATADO} {MEINS_COMERCIAL}^FS

^XZ
```

---

## 3. Tabela de Mapeamento e Transformação

| Placeholder | Campo SAP | Regra de Transformação | Exemplo Registro 1 |
| :--- | :--- | :--- | :--- |
| `{WERKS}` | `WERKS` | Nenhuma (Manter original) | `1001` |
| `{MATNR_FORMATADO}` | `MATNR` | Remover zeros à esquerda (`lstrip('0')`) | `10045678` |
| `{MAKTX}` | `MAKTX` | Tratar caracteres de escape (`^` e `~`) | `CABO DE COBRE ISOLADO 10MM 750V AZUL` |
| `{CHARG}` | `CHARG` | Nenhuma | `LT2026A` |
| `{VFDAT_FORMATADO}` | `VFDAT` | `YYYYMMDD` $\rightarrow$ `DD/MM/AAAA` | `31/12/2028` |
| `{MENGE_FORMATADO}` | `MENGE` | `50.000` $\rightarrow$ `50` | `50` |
| `{MEINS_COMERCIAL}` | `MEINS` | `M` $\rightarrow$ `M` (se `ST` $\rightarrow$ `UN`) | `M` |

