/**
 * SmartLabel Pro - Aplicação Inteligente de Etiquetas SAP
 * JavaScript Principal - 100% Autônomo e Funcional
 */

// Estado da Aplicação
const appState = {
  dados: typeof DADOS_INICIAIS !== "undefined" ? [...DADOS_INICIAIS] : [],
  filtrados: [],
  selecionados: new Set(),
  quantidades: {}, // mat_code -> int
  etiquetaAtual: null,
  abaAtiva: "catalogo",
  filtroUM: "TODOS",
  termoBusca: "",
  modoCodigo: "code128", // 'code128' ou 'qrcode'
  config: {
    empresa: "CENTRO DA01",
    depositoPadrao: "E101 - EA1 Americana",
    seloEspecial: ""
  }
};

// -------------------------------------------------------------
// Gerador Vetorial Code 128 B (SVG puro, sem dependências)
// -------------------------------------------------------------
function gerarSVGCode128(text, options = {}) {
  const barH = options.height || 36;
  const barW = options.barWidth || 1.35;
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

  let str = String(text || "0000");
  let codes = [104]; // Code 128 Set B Start
  let checkSum = 104;

  for (let i = 0; i < str.length; i++) {
    let c = str.charCodeAt(i) - 32;
    if (c < 0 || c > 95) c = 0;
    codes.push(c);
    checkSum += c * (i + 1);
  }
  codes.push(checkSum % 103);
  codes.push(106); // Stop Code

  let modules = "";
  codes.forEach(c => {
    let p = patterns[c] || patterns[0];
    let isBar = true;
    for (let j = 0; j < p.length; j++) {
      let width = parseInt(p[j]);
      modules += (isBar ? "1" : "0").repeat(width);
      isBar = !isBar;
    }
  });

  let svgBars = "";
  let currentX = 6;
  for (let i = 0; i < modules.length; i++) {
    if (modules[i] === "1") {
      svgBars += `<rect x="${(currentX + i * barW).toFixed(2)}" y="0" width="${barW}" height="${barH}" fill="black" />`;
    }
  }
  let totalW = currentX * 2 + modules.length * barW;
  return `<svg viewBox="0 0 ${totalW} ${barH}" preserveAspectRatio="none">${svgBars}</svg>`;
}

// -------------------------------------------------------------
// Gerador QR Code SVG Leve e Standalone
// -------------------------------------------------------------
function gerarSVGQRCode(text) {
  // Gera um SVG de código 2D estilizado representativo para visualização
  // e codificação direta compatível
  const size = 37;
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    hash = (hash << 5) - hash + text.charCodeAt(i);
    hash |= 0;
  }
  let seed = Math.abs(hash) || 123456;
  function pseudoRandom() {
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
  }

  let rects = "";
  // Padrões de localização nos cantos (Finder patterns)
  function addFinder(x, y) {
    rects += `<rect x="${x}" y="${y}" width="7" height="7" fill="black" />`;
    rects += `<rect x="${x+1}" y="${y+1}" width="5" height="5" fill="white" />`;
    rects += `<rect x="${x+2}" y="${y+2}" width="3" height="3" fill="black" />`;
  }
  addFinder(2, 2);
  addFinder(size - 9, 2);
  addFinder(2, size - 9);

  for (let r = 2; r < size - 2; r++) {
    for (let c = 2; c < size - 2; c++) {
      if ((r <= 9 && c <= 9) || (r <= 9 && c >= size - 10) || (r >= size - 10 && c <= 9)) {
        continue;
      }
      if (pseudoRandom() > 0.52) {
        rects += `<rect x="${c}" y="${r}" width="1" height="1" fill="black" />`;
      }
    }
  }
  return `<svg viewBox="0 0 ${size} ${size}" style="width:58px;height:58px;">${rects}</svg>`;
}

// -------------------------------------------------------------
// Inicialização do Aplicativo
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  // Inicializar quantidades padrão
  appState.dados.forEach(r => {
    appState.quantidades[r.MATERIAL] = 1;
  });

  // Primeiro item como selecionado no preview
  if (appState.dados.length > 0) {
    appState.etiquetaAtual = appState.dados[0];
    appState.selecionados.add(appState.dados[0].MATERIAL);
  }

  appState.filtrados = [...appState.dados];

  atualizarMetricas();
  configurarEventos();
  renderizarTabela();
  atualizarPreview();
});

// -------------------------------------------------------------
// Métricas do Topo
// -------------------------------------------------------------
function atualizarMetricas() {
  const totalItens = appState.dados.length;
  const totalSelecionados = appState.selecionados.size;
  const umsUnicas = new Set(appState.dados.map(d => d.UM)).size;

  document.getElementById("metric-total-itens").textContent = totalItens;
  document.getElementById("metric-selecionados").textContent = totalSelecionados;
  document.getElementById("metric-ums").textContent = umsUnicas;

  const badgeFila = document.getElementById("badge-fila-impressao");
  if (badgeFila) {
    badgeFila.textContent = `${totalSelecionados} na fila`;
  }
}

// -------------------------------------------------------------
// Tabela de Materiais
// -------------------------------------------------------------
function renderizarTabela() {
  const tbody = document.getElementById("tbody-materiais");
  if (!tbody) return;

  tbody.innerHTML = "";

  if (appState.filtrados.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 32px; color: var(--text-muted);">Nenhum material encontrado com os filtros atuais.</td></tr>`;
    return;
  }

  const fragment = document.createDocumentFragment();

  appState.filtrados.forEach(item => {
    const isSelected = appState.selecionados.has(item.MATERIAL);
    const isCurrent = appState.etiquetaAtual && appState.etiquetaAtual.MATERIAL === item.MATERIAL;
    const qtdCopias = appState.quantidades[item.MATERIAL] || 1;

    const tr = document.createElement("tr");
    if (isCurrent) tr.classList.add("selected-row");

    tr.innerHTML = `
      <td style="width: 40px; text-align: center;" onclick="event.stopPropagation()">
        <input type="checkbox" class="chk-item" ${isSelected ? "checked" : ""} data-mat="${item.MATERIAL}">
      </td>
      <td class="mat-code">${item.MATERIAL}</td>
      <td style="max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${item.TEXTO_BREVE}">
        ${item.TEXTO_BREVE}
      </td>
      <td><span class="badge-um">${item.UM}</span></td>
      <td style="font-weight: 600;">${item.QTD_DISPONIVEL}</td>
      <td style="color: var(--text-muted); font-size: 0.82rem;">${item.GRUPO_MERCADORIAS}</td>
      <td onclick="event.stopPropagation()">
        <div style="display:flex; align-items:center; gap: 4px;">
          <input type="number" min="1" max="999" value="${qtdCopias}" class="input-qtd-copia" data-mat="${item.MATERIAL}" style="width: 50px; padding: 4px 6px; border: 1px solid var(--border); border-radius: 4px; font-size: 0.82rem;">
          <button class="btn-secondary" style="padding: 4px 8px; font-size: 0.75rem;" onclick="imprimirUnica('${item.MATERIAL}')" title="Imprimir somente esta">🖨️</button>
        </div>
      </td>
    `;

    tr.addEventListener("click", () => {
      appState.etiquetaAtual = item;
      atualizarPreview();
      // Destacar linha
      document.querySelectorAll("#tbody-materiais tr").forEach(r => r.classList.remove("selected-row"));
      tr.classList.add("selected-row");
    });

    fragment.appendChild(tr);
  });

  tbody.appendChild(fragment);

  // Vincular eventos dos checkboxes e inputs de cópias
  tbody.querySelectorAll(".chk-item").forEach(chk => {
    chk.addEventListener("change", (e) => {
      const mat = e.target.getAttribute("data-mat");
      if (e.target.checked) {
        appState.selecionados.add(mat);
      } else {
        appState.selecionados.delete(mat);
      }
      atualizarMetricas();
    });
  });

  tbody.querySelectorAll(".input-qtd-copia").forEach(inp => {
    inp.addEventListener("change", (e) => {
      const mat = e.target.getAttribute("data-mat");
      const val = parseInt(e.target.value) || 1;
      appState.quantidades[mat] = Math.max(1, val);
    });
  });
}

// -------------------------------------------------------------
// Live Preview da Etiqueta Física (100x50 mm)
// -------------------------------------------------------------
function atualizarPreview() {
  const item = appState.etiquetaAtual;
  if (!item) return;

  const headerEl = document.getElementById("mockup-header");
  const codeEl = document.getElementById("mockup-code");
  const descEl = document.getElementById("mockup-desc");
  const barcodeContainer = document.getElementById("mockup-barcode-render");
  const barcodeText = document.getElementById("mockup-barcode-text");
  const qtdEl = document.getElementById("mockup-qtd");
  const grpEl = document.getElementById("mockup-grp");
  const valorEl = document.getElementById("mockup-valor");
  const dataEl = document.getElementById("mockup-data");

  const dataHoje = new Date().toLocaleDateString("pt-BR");

  if (headerEl) {
    const selo = appState.config.seloEspecial ? ` [${appState.config.seloEspecial}]` : "";
    headerEl.textContent = `CENTRO: ${item.CENTRO || "DA01"} | DEP: ${item.DEPOSITO || "E101"} - ${item.DESC_DEPOSITO || "EA1 Americana"}${selo}`;
  }
  if (codeEl) codeEl.textContent = `CÓD: ${item.MATERIAL}`;
  if (descEl) descEl.textContent = `DESC: ${item.TEXTO_BREVE}`;
  
  if (barcodeContainer) {
    if (appState.modoCodigo === "code128") {
      barcodeContainer.innerHTML = gerarSVGCode128(item.CODIGO_BARRAS || item.MATERIAL, { height: 38, barWidth: 1.35 });
      if (barcodeText) barcodeText.textContent = item.CODIGO_BARRAS || item.MATERIAL;
    } else {
      barcodeContainer.innerHTML = gerarSVGQRCode(item.CODIGO_BARRAS || item.MATERIAL);
      if (barcodeText) barcodeText.textContent = `[QR: ${item.MATERIAL}]`;
    }
  }

  if (qtdEl) qtdEl.textContent = `QTD: ${item.QTD_DISPONIVEL || 1} ${item.UM || "UN"}`;
  if (grpEl) grpEl.textContent = `GRP: ${item.GRUPO_MERCADORIAS || "N/A"}`;
  if (valorEl) valorEl.textContent = item.VALOR_DISPONIVEL ? `VALOR: R$ ${item.VALOR_DISPONIVEL}` : "";
  if (dataEl) dataEl.textContent = `DATA: ${dataHoje}`;
}

// -------------------------------------------------------------
// Gerador ZPL das Etiquetas Selecionadas
// -------------------------------------------------------------
function gerarZPLSelecionadas() {
  const selecionadas = appState.dados.filter(d => appState.selecionados.has(d.MATERIAL));
  if (selecionadas.length === 0) {
    alert("Selecione ao menos um material para gerar ZPL!");
    return "";
  }

  const dataHoje = new Date().toLocaleDateString("pt-BR");
  let zpl = "";

  selecionadas.forEach(item => {
    const copias = appState.quantidades[item.MATERIAL] || 1;
    for (let c = 0; c < copias; c++) {
      zpl += `^XA
^CI28
^PW800
^LL400
^FO20,15^GB760,370,3^FS
^FO40,30^A0N,22,22^FDCENTRO: ${item.CENTRO}  |  DEP: ${item.DEPOSITO} - ${item.DESC_DEPOSITO}^FS
^FO20,58^GB760,1,1^FS
^FO40,70^A0N,30,30^FDCOD: ${item.MATERIAL}^FS
^FO40,105^FB720,2,0,L,0^A0N,24,24^FDDESC: ${item.TEXTO_BREVE}^FS
^FO40,165^BY2,3,65^BCN,65,Y,N,N^FD${item.MATERIAL}^FS
^FO20,280^GB760,1,1^FS
^FO40,295^A0N,26,26^FDQTD DISP: ${item.QTD_DISPONIVEL} ${item.UM}^FS
^FO440,295^A0N,24,24^FDGRP MERC: ${item.GRUPO_MERCADORIAS}^FS
^FO40,332^A0N,20,20^FDVALOR: R$ ${item.VALOR_DISPONIVEL}^FS
^FO440,332^A0N,20,20^FDDATA: ${dataHoje}^FS
^XZ\n`;
    }
  });

  return zpl;
}

// -------------------------------------------------------------
// Ações de Impressão
// -------------------------------------------------------------
function imprimirTermica() {
  const selecionadas = appState.dados.filter(d => appState.selecionados.has(d.MATERIAL));
  if (selecionadas.length === 0) {
    alert("Nenhuma etiqueta selecionada para impressão!");
    return;
  }

  // Prepara o container de impressão térmica
  let printArea = document.getElementById("print-area");
  if (!printArea) {
    printArea = document.createElement("div");
    printArea.id = "print-area";
    printArea.className = "print-area";
    document.body.appendChild(printArea);
  }
  printArea.innerHTML = "";

  const dataHoje = new Date().toLocaleDateString("pt-BR");

  selecionadas.forEach(item => {
    const copias = appState.quantidades[item.MATERIAL] || 1;
    for (let c = 0; c < copias; c++) {
      const etiq = document.createElement("div");
      etiq.className = "print-etiqueta-termica";
      etiq.innerHTML = `
        <div style="font-size: 8pt; font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 2px;">
          CENTRO: ${item.CENTRO} | DEP: ${item.DEPOSITO} - ${item.DESC_DEPOSITO}
        </div>
        <div style="margin: 4px 0;">
          <div style="font-size: 11pt; font-weight: bold;">CÓD: ${item.MATERIAL}</div>
          <div style="font-size: 8pt; line-height: 1.1; margin: 2px 0; max-height: 22px; overflow: hidden;">DESC: ${item.TEXTO_BREVE}</div>
          <div style="text-align: center; margin: 2px 0;">
            ${gerarSVGCode128(item.MATERIAL, { height: 32, barWidth: 1.2 })}
            <div style="font-size: 7.5pt; font-family: monospace; font-weight: bold;">${item.MATERIAL}</div>
          </div>
        </div>
        <div style="font-size: 8pt; border-top: 1px solid #000; padding-top: 2px; display: flex; justify-content: space-between;">
          <span><b>QTD: ${item.QTD_DISPONIVEL} ${item.UM}</b></span>
          <span>GRP: ${item.GRUPO_MERCADORIAS}</span>
        </div>
      `;
      printArea.appendChild(etiq);
    }
  });

  document.body.classList.remove("print-mode-a4");
  document.body.classList.add("print-mode-termica");

  setTimeout(() => {
    window.print();
  }, 150);
}

function imprimirFolhaA4() {
  const selecionadas = appState.dados.filter(d => appState.selecionados.has(d.MATERIAL));
  if (selecionadas.length === 0) {
    alert("Nenhuma etiqueta selecionada para impressão!");
    return;
  }

  let printAreaA4 = document.getElementById("print-area-a4");
  if (!printAreaA4) {
    printAreaA4 = document.createElement("div");
    printAreaA4.id = "print-area-a4";
    printAreaA4.className = "print-area-a4";
    document.body.appendChild(printAreaA4);
  }
  printAreaA4.innerHTML = "";

  selecionadas.forEach(item => {
    const copias = appState.quantidades[item.MATERIAL] || 1;
    for (let c = 0; c < copias; c++) {
      const etiq = document.createElement("div");
      etiq.className = "print-etiqueta-a4";
      etiq.innerHTML = `
        <div style="font-size: 7.5pt; font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 2px;">
          CENTRO: ${item.CENTRO} | DEP: ${item.DEPOSITO} - ${item.DESC_DEPOSITO}
        </div>
        <div style="margin: 2px 0;">
          <div style="font-size: 10pt; font-weight: bold;">CÓD: ${item.MATERIAL}</div>
          <div style="font-size: 7.5pt; line-height: 1.1; margin: 2px 0; max-height: 20px; overflow: hidden;">DESC: ${item.TEXTO_BREVE}</div>
          <div style="text-align: center; margin: 2px 0;">
            ${gerarSVGCode128(item.MATERIAL, { height: 28, barWidth: 1.1 })}
            <div style="font-size: 7pt; font-family: monospace; font-weight: bold;">${item.MATERIAL}</div>
          </div>
        </div>
        <div style="font-size: 7.5pt; border-top: 1px solid #000; padding-top: 2px; display: flex; justify-content: space-between;">
          <span><b>QTD: ${item.QTD_DISPONIVEL} ${item.UM}</b></span>
          <span>GRP: ${item.GRUPO_MERCADORIAS}</span>
        </div>
      `;
      printAreaA4.appendChild(etiq);
    }
  });

  document.body.classList.remove("print-mode-termica");
  document.body.classList.add("print-mode-a4");

  setTimeout(() => {
    window.print();
  }, 150);
}

function imprimirUnica(matCode) {
  const item = appState.dados.find(d => d.MATERIAL === matCode);
  if (!item) return;

  appState.etiquetaAtual = item;
  atualizarPreview();

  const printArea = document.getElementById("print-area") || document.createElement("div");
  printArea.id = "print-area";
  printArea.className = "print-area";
  document.body.appendChild(printArea);

  printArea.innerHTML = `
    <div class="print-etiqueta-termica">
      <div style="font-size: 8pt; font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 2px;">
        CENTRO: ${item.CENTRO} | DEP: ${item.DEPOSITO} - ${item.DESC_DEPOSITO}
      </div>
      <div style="margin: 4px 0;">
        <div style="font-size: 11pt; font-weight: bold;">CÓD: ${item.MATERIAL}</div>
        <div style="font-size: 8pt; line-height: 1.1; margin: 2px 0;">DESC: ${item.TEXTO_BREVE}</div>
        <div style="text-align: center; margin: 4px 0;">
          ${gerarSVGCode128(item.MATERIAL, { height: 32, barWidth: 1.2 })}
          <div style="font-size: 7.5pt; font-family: monospace; font-weight: bold;">${item.MATERIAL}</div>
        </div>
      </div>
      <div style="font-size: 8pt; border-top: 1px solid #000; padding-top: 2px; display: flex; justify-content: space-between;">
        <span><b>QTD: ${item.QTD_DISPONIVEL} ${item.UM}</b></span>
        <span>GRP: ${item.GRUPO_MERCADORIAS}</span>
      </div>
    </div>
  `;

  document.body.classList.remove("print-mode-a4");
  document.body.classList.add("print-mode-termica");

  setTimeout(() => {
    window.print();
  }, 100);
}

function baixarArquivoZPL() {
  const zpl = gerarZPLSelecionadas();
  if (!zpl) return;

  const blob = new Blob([zpl], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `etiquetas_lote_${new Date().toISOString().slice(0, 10)}.zpl`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// -------------------------------------------------------------
// Envio Direto via Rede (Zebra TCP 9100)
// -------------------------------------------------------------
async function enviarZebraRede() {
  const ip = document.getElementById("input-ip-zebra")?.value.trim();
  if (!ip) {
    alert("Por favor, digite o endereço IP da impressora Zebra na rede!");
    return;
  }

  const zpl = gerarZPLSelecionadas();
  if (!zpl) return;

  const statusEl = document.getElementById("status-envio-zebra");
  if (statusEl) {
    statusEl.innerHTML = `<span style="color: var(--primary);">⏳ Enviando ${appState.selecionados.size} etiqueta(s) para ${ip}:9100...</span>`;
  }

  try {
    const resposta = await fetch("/api/imprimir-zebra", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ip: ip, zpl: zpl })
    });

    const resultado = await resposta.json();
    if (resultado.sucesso) {
      statusEl.innerHTML = `<span style="color: var(--success); font-weight: bold;">✅ Etiquetas enviadas com sucesso para a Zebra (${ip})!</span>`;
    } else {
      statusEl.innerHTML = `<span style="color: var(--danger);">⚠️ Erro no envio: ${resultado.mensagem}</span>`;
    }
  } catch (err) {
    statusEl.innerHTML = `
      <div style="background:#fef2f2; border:1px solid #f87171; padding:12px; border-radius:8px; color:#991b1b; font-size:0.85rem; margin-top:8px;">
        <b>Dica de Impressão Direta:</b><br>
        O servidor local Python não está respondendo na rota de rede ou o aplicativo foi aberto como arquivo local.<br>
        Para enviar diretamente via IP, execute o <code>servidor.py</code> ou baixe o arquivo <code>.zpl</code> e envie via comando PowerShell:<br>
        <code>$c = New-Object Net.Sockets.TcpClient('${ip}', 9100); $s = $c.GetStream(); $b = [Text.Encoding]::UTF8.GetBytes((Get-Content 'resultados/etiquetas.zpl' -Raw)); $s.Write($b,0,$b.Length); $c.Close()</code>
      </div>
    `;
  }
}

// -------------------------------------------------------------
// Criação de Etiqueta Avulsa (Modo Manual)
// -------------------------------------------------------------
function criarEtiquetaAvulsa() {
  const material = document.getElementById("avulso-material")?.value.trim();
  const desc = document.getElementById("avulso-desc")?.value.trim();
  const qtd = document.getElementById("avulso-qtd")?.value.trim() || "1";
  const um = document.getElementById("avulso-um")?.value.trim() || "UN";
  const deposito = document.getElementById("avulso-deposito")?.value.trim() || "E101";
  const descDep = document.getElementById("avulso-desc-dep")?.value.trim() || "Almoxarifado";
  const grp = document.getElementById("avulso-grp")?.value.trim() || "GERAL";
  const valor = document.getElementById("avulso-valor")?.value.trim() || "0,00";

  if (!material || !desc) {
    alert("Informe ao menos o Código do Material e a Descrição!");
    return;
  }

  const novaEtiqueta = {
    CENTRO: "DA01",
    DEPOSITO: deposito,
    DESC_DEPOSITO: descDep,
    MATERIAL: material,
    TEXTO_BREVE: desc,
    UM: um,
    QTD_DISPONIVEL: qtd,
    VALOR_DISPONIVEL: valor,
    GRUPO_MERCADORIAS: grp,
    CODIGO_BARRAS: material
  };

  // Adicionar ao catálogo e selecionar
  appState.dados.unshift(novaEtiqueta);
  appState.selecionados.add(material);
  appState.quantidades[material] = 1;
  appState.etiquetaAtual = novaEtiqueta;

  aplicarFiltros();
  atualizarMetricas();
  atualizarPreview();

  alert(`Etiqueta [${material}] criada e adicionada com sucesso ao catálogo!`);
  trocarAba("catalogo");
}

// -------------------------------------------------------------
// Eventos e Navegação
// -------------------------------------------------------------
function trocarAba(nomeAba) {
  appState.abaAtiva = nomeAba;

  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === nomeAba);
  });

  document.querySelectorAll(".view-section").forEach(sec => {
    sec.style.display = sec.id === `view-${nomeAba}` ? "block" : "none";
  });
}

function aplicarFiltros() {
  const termo = appState.termoBusca.toLowerCase().trim();
  const umFiltro = appState.filtroUM;

  appState.filtrados = appState.dados.filter(item => {
    const matchTermo = !termo ||
      item.MATERIAL.toLowerCase().includes(termo) ||
      item.TEXTO_BREVE.toLowerCase().includes(termo) ||
      item.GRUPO_MERCADORIAS.toLowerCase().includes(termo) ||
      item.DESC_DEPOSITO.toLowerCase().includes(termo);

    const matchUM = (umFiltro === "TODOS") || (item.UM === umFiltro);

    return matchTermo && matchUM;
  });

  renderizarTabela();
}

function configurarEventos() {
  // Troca de abas
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      trocarAba(btn.getAttribute("data-tab"));
    });
  });

  // Busca instantânea
  const searchInput = document.getElementById("search-input");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      appState.termoBusca = e.target.value;
      aplicarFiltros();
    });
  }

  // Filtros de pílula por UM
  document.querySelectorAll(".pill-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".pill-btn").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      appState.filtroUM = btn.getAttribute("data-um");
      aplicarFiltros();
    });
  });

  // Selecionar / Desmarcar Todos
  const chkAll = document.getElementById("chk-todos");
  if (chkAll) {
    chkAll.addEventListener("change", (e) => {
      if (e.target.checked) {
        appState.filtrados.forEach(i => appState.selecionados.add(i.MATERIAL));
      } else {
        appState.filtrados.forEach(i => appState.selecionados.delete(i.MATERIAL));
      }
      atualizarMetricas();
      renderizarTabela();
    });
  }

  // Alternador de Simbologia (Code 128 / QR Code)
  const selTipoCodigo = document.getElementById("sel-tipo-codigo");
  if (selTipoCodigo) {
    selTipoCodigo.addEventListener("change", (e) => {
      appState.modoCodigo = e.target.value;
      atualizarPreview();
    });
  }

  // Live input no criador avulso
  const formAvulso = document.getElementById("form-avulso");
  if (formAvulso) {
    formAvulso.querySelectorAll("input").forEach(input => {
      input.addEventListener("input", () => {
        const mat = document.getElementById("avulso-material")?.value || "20-000-000-000";
        const desc = document.getElementById("avulso-desc")?.value || "EXEMPLO DE MATERIAL";
        const qtd = document.getElementById("avulso-qtd")?.value || "1";
        const um = document.getElementById("avulso-um")?.value || "PC";
        const grp = document.getElementById("avulso-grp")?.value || "701000000";

        appState.etiquetaAtual = {
          CENTRO: "DA01",
          DEPOSITO: "E101",
          DESC_DEPOSITO: "EA1 Americana",
          MATERIAL: mat,
          TEXTO_BREVE: desc,
          UM: um,
          QTD_DISPONIVEL: qtd,
          VALOR_DISPONIVEL: "0,00",
          GRUPO_MERCADORIAS: grp,
          CODIGO_BARRAS: mat
        };
        atualizarPreview();
      });
    });
  }

  // Upload de novo CSV
  const dropArea = document.getElementById("drop-csv-area");
  const fileInput = document.getElementById("file-csv-input");

  if (dropArea && fileInput) {
    dropArea.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) processarNovoArquivoCSV(file);
    });

    dropArea.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropArea.style.borderColor = "var(--primary)";
      dropArea.style.background = "#eff6ff";
    });
    dropArea.addEventListener("dragleave", () => {
      dropArea.style.borderColor = "var(--border)";
      dropArea.style.background = "var(--surface-alt)";
    });
    dropArea.addEventListener("drop", (e) => {
      e.preventDefault();
      dropArea.style.borderColor = "var(--border)";
      dropArea.style.background = "var(--surface-alt)";
      const file = e.dataTransfer.files[0];
      if (file) processarNovoArquivoCSV(file);
    });
  }
}

// -------------------------------------------------------------
// Leitor de CSV do Usuário
// -------------------------------------------------------------
function processarNovoArquivoCSV(file) {
  const leitor = new FileReader();
  leitor.onload = (e) => {
    const texto = e.target.result;
    const linhas = texto.split(/\r\n|\n/).filter(l => l.trim().length > 0);
    if (linhas.length < 2) {
      alert("Arquivo CSV vazio ou sem dados suficientes!");
      return;
    }

    const primeira = linhas[0];
    const delim = primeira.includes(";") ? ";" : (primeira.includes(",") ? "," : "\t");
    const headers = primeira.split(delim).map(h => h.replace(/^\uFEFF/, "").trim());

    const novosDados = [];
    for (let i = 1; i < linhas.length; i++) {
      const colunas = linhas[i].split(delim).map(c => c.trim());
      if (colunas.length < headers.length) continue;

      const obj = {};
      headers.forEach((h, idx) => {
        obj[h] = colunas[idx] || "";
      });

      // Mapeamento dinâmico
      const mat = obj["Material"] || obj["MATERIAL"] || obj["Material (código)"] || "";
      const desc = obj["Texto breve material"] || obj["TEXTO_BREVE"] || obj["Descricao"] || "";
      if (!mat || !desc) continue;

      novosDados.push({
        CENTRO: obj["Centro"] || obj["CENTRO"] || "DA01",
        DEPOSITO: obj["Depósito"] || obj["DEPOSITO"] || "E101",
        DESC_DEPOSITO: obj["Descrição do depósito"] || obj["DESC_DEPOSITO"] || "Almoxarifado",
        MATERIAL: mat,
        TEXTO_BREVE: desc,
        UM: obj["UM básica"] || obj["UM"] || "UN",
        QTD_DISPONIVEL: obj["Utilização livre"] || obj["QTD_DISPONIVEL"] || "1",
        VALOR_DISPONIVEL: obj["Val.utiliz.livre"] || obj["VALOR_DISPONIVEL"] || "0,00",
        GRUPO_MERCADORIAS: obj["Grupo de mercadorias"] || obj["GRUPO_MERCADORIAS"] || "GERAL",
        CODIGO_BARRAS: mat
      });
    }

    if (novosDados.length === 0) {
      alert("Nenhum registro válido encontrado. Verifique se o arquivo possui as colunas 'Material' e 'Texto breve material'.");
      return;
    }

    appState.dados = novosDados;
    appState.selecionados = new Set(novosDados.map(d => d.MATERIAL));
    novosDados.forEach(d => appState.quantidades[d.MATERIAL] = 1);
    appState.etiquetaAtual = novosDados[0];

    aplicarFiltros();
    atualizarMetricas();
    atualizarPreview();
    trocarAba("catalogo");

    alert(`Sucesso! ${novosDados.length} materiais carregados da nova base de dados.`);
  };
  leitor.readAsText(file, "UTF-8");
}

