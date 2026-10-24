# Relatório de Auditoria e Geração de Etiquetas SAP

**Data de Execução**: 24/10/2026 às 15:25:15  
**Base de Dados de Origem**: `etiquetas.csv`  
**Pasta de Saída dos Artefatos**: `resultados/`  
**Encoding Detectado**: `utf-8-sig` | **Delimitador**: `;`  

---

## 1. Sumário Executivo de Processamento

- **Total de linhas lidas da base SAP**: **448**
- **Total de etiquetas geradas com sucesso**: **440**
- **Total de registros descartados**: **8**

### Distribuição por Unidade de Medida (UM):

| Unidade de Medida (UM) | Quantidade de Itens / Etiquetas |
| :--- | :---: |
| `CDA` | 1 |
| `CJ` | 1 |
| `JG` | 13 |
| `KG` | 23 |
| `M` | 9 |
| `PAR` | 23 |
| `PC` | 366 |
| `UN` | 4 |

---

## 2. Matriz de Mapeamento de Campos

| Campo no Modelo | Obrigatório? | Campo Correspondente no SAP | Transformação Aplicada | Status |
| :--- | :---: | :--- | :--- | :---: |
| `CENTRO` | Sim | `Centro` | Nenhuma (`DA01`) | ✅ Mapeado |
| `DEPÓSITO` | Sim | `Depósito` + `Descrição do depósito` | Concatenação de código e descrição | ✅ Mapeado |
| `MATERIAL` | Sim | `Material` | Mantido formato alfanumérico com hífen | ✅ Mapeado |
| `DESCRIÇÃO` | Sim | `Texto breve material` | Quebra de linha inteligente / escape ZPL | ✅ Mapeado |
| `QTD_DISPONÍVEL`| Sim | `Utilização livre` | Normalização de zeros redundantes | ✅ Mapeado |
| `UNIDADE_MEDIDA`| Sim | `UM básica` | Validação de sigla padrão SAP/comercial | ✅ Mapeado |
| `VALOR` | Não | `Val.utiliz.livre` | Formatação com prefixo monetário `R$` | ✅ Mapeado |
| `GRUPO_MERC` | Não | `Grupo de mercadorias` | Preservação da classificação mercadológica | ✅ Mapeado |
| `CÓDIGO_BARRAS`| Sim | `Material` | Simbologia Code 128 com interpretação | ✅ Mapeado |

---

## 3. Justificativa de Registros Descartados

Durante a validação pré-impressão (Passo 4 da Skill), 8 linhas foram descartadas porque correspondem a subtotais e somatórios do relatório standard do SAP (ex: MB52/ALV), sem código de material ou descrição válida.

| Linha no CSV | Motivo do Descarte | Conteúdo Detectado |
| :---: | :--- | :--- |
| 442 | Linha de subtotal/totalização do SAP sem identificação de Material | `UM: CJ, Qtd: 176,0, Valor: 894.620,59` |
| 443 | Linha de subtotal/totalização do SAP sem identificação de Material | `UM: EA, Qtd: 99,00, Valor: ` |
| 444 | Linha de subtotal/totalização do SAP sem identificação de Material | `UM: JG, Qtd: 85, Valor: ` |
| 445 | Linha de subtotal/totalização do SAP sem identificação de Material | `UM: KG, Qtd: 466,500, Valor: ` |
| 446 | Linha de subtotal/totalização do SAP sem identificação de Material | `UM: M, Qtd: 12.039,500, Valor: ` |
| 447 | Linha de subtotal/totalização do SAP sem identificação de Material | `UM: PAA, Qtd: 99, Valor: ` |
| 448 | Linha de subtotal/totalização do SAP sem identificação de Material | `UM: ST, Qtd: 19.534, Valor: ` |
| 449 | Linha de subtotal/totalização do SAP sem identificação de Material | `UM: UN, Qtd: 6, Valor: ` |

---

## 4. Arquivos Gerados na Pasta `resultados/`

1. **`etiquetas.zpl`**:
   - Arquivo pronto para envio direto a impressoras térmicas industriais Zebra (porta 9100, USB ou fila RAW do Windows).
   - Resolução: 203 DPI (8 dots/mm) | Dimensão: 100x50 mm (`^PW800`, `^LL400`, `^CI28`).

2. **`etiquetas_termica_100x50.pdf`**:
   - Documento PDF com 440 páginas (1 etiqueta de 100x50 mm por página).
   - Ideal para drivers de impressoras térmicas (Zebra, Elgin, Argox, Datamax).

3. **`etiquetas_folha_a4.pdf`**:
   - Documento PDF diagramado em folhas A4 com 10 etiquetas por folha (2 colunas x 5 linhas).
   - Ideal para impressão em folhas de etiquetas adesivas comuns em impressoras laser ou jato de tinta.

4. **`etiquetas_preview.html`**:
   - Visualizador interativo autônomo com busca em tempo real, visualização das etiquetas com código de barras Code 128 vetorial e atalho para impressão.

5. **`etiquetas_tratadas.csv`**:
   - Base de dados limpa (sem linhas de totais) e padronizada em UTF-8 com delimitador ponto e vírgula, pronta para importação direta no BarTender, ZebraDesigner ou NiceLabel.

---

## 5. Instruções de Impressão e Disparo

### Opção A: Impressão ZPL via Rede (Porta 9100)
```powershell
# Exemplo de envio direto para a impressora Zebra no IP da fábrica
$ip = '192.168.1.100'
$client = New-Object System.Net.Sockets.TcpClient($ip, 9100)
$stream = $client.GetStream()
$bytes = [System.IO.File]::ReadAllBytes('resultados/etiquetas.zpl')
$stream.Write($bytes, 0, $bytes.Length)
$stream.Close()
$client.Close()
```

### Opção B: Impressão ZPL via Windows Spooler / Compartilhamento
```cmd
:: Envio direto para porta compartilhada da Zebra
copy /b resultados\etiquetas.zpl \\localhost\NomeImpressoraZebra
```

### Opção C: Impressão Gráfica via PDF
- Abrir `resultados/etiquetas_termica_100x50.pdf` e selecionar a impressora térmica com tamanho de papel configurado para `100 mm x 50 mm`, escala 100% (sem ajuste de página).
- Ou abrir `resultados/etiquetas_folha_a4.pdf` em qualquer impressora de escritório em folhas adesivas formato A4.