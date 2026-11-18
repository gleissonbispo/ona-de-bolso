/* ona-ui.js — interface da ONA de bolso.
 * https://github.com/gleissonbispo/ona-de-bolso · licença MIT
 *
 * Monta a página dentro de um elemento: OnaUI.montar(el, { exemplo: {pessoas, ligacoes} }).
 * Usa o motor (window.ONA). Sem dependências e sem requisições: os arquivos são lidos no navegador.
 * As cores vêm de variáveis CSS (--background, --foreground, --surface, --secondary, --muted,
 * --accent, --accent-subtle, --border-clr), as mesmas do site gleissonbispo.com.br.
 */
(function (raiz) {
  "use strict";

  var LIMITE_DESENHO = 500;
  var CORES_CLARO = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"];
  var CORES_ESCURO = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"];
  var COR_OUTRAS = { claro: "#8f8a85", escuro: "#77726d" };
  var PAPEL_TXT = {
    coordenador: "coordenador (liga colegas da própria área)",
    consultor: "consultor (liga colegas de outra área entre si)",
    representante: "representante (leva informação da área para fora)",
    porteiro: "porteiro (traz informação de fora para a área)",
    ligacao: "ligação (conecta duas outras áreas)"
  };
  var PAPEL_CURTO = { coordenador: "Coordenador", consultor: "Consultor", representante: "Representante", porteiro: "Porteiro", ligacao: "Ligação" };

  var CSS = [
    ".ona{--ona-bg:var(--background,#fff);--ona-fg:var(--foreground,#0a0a0a);--ona-surface:var(--surface,#fafafa);--ona-sec:var(--secondary,#525252);--ona-muted:var(--muted,#a3a3a3);--ona-accent:var(--accent,#8b5e3c);--ona-accent-h:var(--accent-hover,#73492e);--ona-accent-s:var(--accent-subtle,#faf3ee);--ona-border:var(--border-clr,#eaeaea);--ona-mono:var(--site-font-mono,'JetBrains Mono',ui-monospace,Consolas,monospace);color:var(--ona-fg);font-size:15px;line-height:1.55}",
    ".ona *{box-sizing:border-box}",
    ".ona h2{font-size:22px;font-weight:500;letter-spacing:-.01em;margin:56px 0 6px;color:var(--ona-fg)}",
    ".ona h3{font-size:16px;font-weight:500;margin:0 0 6px}",
    ".ona .ona-lead{color:var(--ona-sec);margin:0 0 20px;max-width:46rem}",
    ".ona .ona-eyebrow{font-family:var(--ona-mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--ona-muted)}",
    ".ona .ona-drops{display:grid;grid-template-columns:1fr 1fr;gap:12px}",
    ".ona .ona-drop{position:relative;border:1.5px dashed var(--ona-border);border-radius:14px;padding:22px 20px;background:var(--ona-surface);cursor:pointer;transition:border-color .15s,background .15s;min-height:132px;display:flex;flex-direction:column;justify-content:center;gap:4px}",
    ".ona .ona-drop:hover,.ona .ona-drop:focus-visible{border-color:var(--ona-accent);outline:none}",
    ".ona .ona-drop.arrastando{border-color:var(--ona-accent);background:var(--ona-accent-s)}",
    ".ona .ona-drop.pronto{border-style:solid;border-color:var(--ona-accent)}",
    ".ona .ona-drop b{font-weight:500;font-size:16px;display:flex;align-items:center;gap:8px}",
    ".ona .ona-drop small{color:var(--ona-sec);font-family:var(--ona-mono);font-size:12px}",
    ".ona .ona-drop .ona-st{font-size:13px;color:var(--ona-muted);margin-top:6px}",
    ".ona .ona-drop.pronto .ona-st{color:var(--ona-fg)}",
    ".ona .ona-drop input{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}",
    ".ona .ona-ico{width:28px;height:28px;border-radius:8px;background:var(--ona-bg);border:1px solid var(--ona-border);display:inline-flex;align-items:center;justify-content:center;color:var(--ona-accent);flex:none}",
    ".ona .ona-acoes{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:16px}",
    ".ona button{font:inherit}",
    ".ona .ona-bt{height:42px;padding:0 20px;border-radius:999px;border:1px solid transparent;background:var(--ona-accent);color:#fff;font-size:14px;font-weight:500;cursor:pointer;transition:background .15s}",
    ".ona .ona-bt:hover{background:var(--ona-accent-h)}",
    ".ona .ona-bt:disabled{opacity:.45;cursor:not-allowed}",
    ".ona .ona-bt.sec{background:transparent;color:var(--ona-fg);border-color:var(--ona-border)}",
    ".ona .ona-bt.sec:hover{border-color:var(--ona-accent);color:var(--ona-accent)}",
    ".ona .ona-bt.peq{height:34px;padding:0 14px;font-size:13px}",
    ".ona .ona-link{background:none;border:0;padding:0;color:var(--ona-accent);cursor:pointer;font-size:13px;text-decoration:underline;text-underline-offset:3px}",
    ".ona .ona-modelos{font-size:13px;color:var(--ona-sec);display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;margin-top:14px}",
    ".ona .ona-msg{font-size:14px;margin:12px 0 0;min-height:1em}",
    ".ona .ona-msg .erro{color:#c0392b}.ona .ona-msg .aviso{color:var(--ona-sec)}",
    ".ona .ona-priv{display:flex;gap:10px;align-items:flex-start;font-size:13.5px;color:var(--ona-sec);border-left:2px solid var(--ona-accent);padding:2px 0 2px 12px;margin:0 0 24px;max-width:46rem}",
    ".ona .ona-barra{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;padding:12px 0;border-bottom:1px solid var(--ona-border);margin-top:40px}",
    ".ona select,.ona input[type=search]{height:36px;border-radius:10px;border:1px solid var(--ona-border);background:var(--ona-bg);color:var(--ona-fg);font:inherit;font-size:14px;padding:0 10px}",
    ".ona label.ona-campo{display:inline-flex;align-items:center;gap:8px;font-size:13px;color:var(--ona-sec)}",
    ".ona .ona-conf{border-radius:12px;padding:14px 16px;margin:20px 0 0;font-size:14px;border:1px solid var(--ona-border);background:var(--ona-surface)}",
    ".ona .ona-conf b{font-weight:500}",
    ".ona .ona-conf.insuficiente{border-color:#c0392b;background:rgba(192,57,43,.06)}",
    ".ona .ona-conf.cautela{border-color:var(--ona-accent);background:var(--ona-accent-s)}",
    ".ona .ona-cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--ona-border);border:1px solid var(--ona-border);border-radius:14px;overflow:hidden;margin-top:16px}",
    ".ona .ona-card{background:var(--ona-bg);padding:18px 18px 16px}",
    ".ona .ona-card .n{font-size:30px;font-weight:500;letter-spacing:-.02em;font-variant-numeric:tabular-nums;line-height:1.1}",
    ".ona .ona-card .r{font-size:13px;font-weight:500;margin-top:4px}",
    ".ona .ona-card .e{font-size:12.5px;color:var(--ona-sec);margin-top:4px;line-height:1.45}",
    ".ona .ona-ins{display:grid;gap:10px;margin-top:16px}",
    ".ona .ona-in{border:1px solid var(--ona-border);border-radius:12px;padding:16px 18px;background:var(--ona-bg)}",
    ".ona .ona-in .tag{font-family:var(--ona-mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--ona-muted);display:inline-flex;align-items:center;gap:6px}",
    ".ona .ona-in .tag i{width:7px;height:7px;border-radius:50%;background:var(--ona-muted);display:inline-block}",
    ".ona .ona-in.risco .tag,.ona .ona-in.alerta .tag{color:#c0392b}.ona .ona-in.risco .tag i,.ona .ona-in.alerta .tag i{background:#c0392b}",
    ".ona .ona-in.atencao .tag{color:var(--ona-accent)}.ona .ona-in.atencao .tag i{background:var(--ona-accent)}",
    ".ona .ona-in b{display:block;font-weight:500;font-size:16px;margin:6px 0 4px}",
    ".ona .ona-in p{margin:0;color:var(--ona-sec);font-size:14px}",
    ".ona .ona-chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}",
    ".ona .ona-chip{height:28px;padding:0 11px;border-radius:999px;border:1px solid var(--ona-border);background:var(--ona-bg);color:var(--ona-fg);font-size:12.5px;cursor:pointer;display:inline-flex;align-items:center;gap:6px;font-family:var(--ona-mono)}",
    ".ona .ona-chip:hover{border-color:var(--ona-accent)}",
    ".ona .ona-chip.ativo{background:var(--ona-fg);color:var(--ona-bg);border-color:var(--ona-fg)}",
    ".ona .ona-chip .bol{width:8px;height:8px;border-radius:50%;flex:none}",
    ".ona .ona-rede{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:16px;margin-top:14px}",
    ".ona .ona-tela{position:relative;border:1px solid var(--ona-border);border-radius:14px;background:var(--ona-bg);overflow:hidden;touch-action:manipulation}",
    ".ona canvas{display:block;width:100%;height:560px}",
    ".ona .ona-tip{position:absolute;pointer-events:none;background:var(--ona-fg);color:var(--ona-bg);border-radius:10px;padding:9px 11px;font-size:12.5px;line-height:1.45;max-width:240px;opacity:0;transition:opacity .1s;z-index:2}",
    ".ona .ona-tip b{font-family:var(--ona-mono);font-weight:500}",
    ".ona .ona-painel{border:1px solid var(--ona-border);border-radius:14px;padding:16px;background:var(--ona-surface);font-size:13.5px;align-self:start}",
    ".ona .ona-painel dl{display:grid;grid-template-columns:1fr auto;gap:4px 12px;margin:10px 0 14px}",
    ".ona .ona-painel dt{color:var(--ona-sec)}.ona .ona-painel dd{margin:0;text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}",
    ".ona .ona-aviso-sim{position:absolute;left:12px;top:12px;right:12px;max-width:340px;background:var(--ona-fg);color:var(--ona-bg);border-radius:10px;padding:9px 12px;font-size:13px;line-height:1.4;z-index:1}",
    ".ona .ona-aviso-sim b{font-weight:500}",
    ".ona .ona-painel .vazio{color:var(--ona-sec)}",
    ".ona .ona-sim{margin-top:12px;padding-top:12px;border-top:1px solid var(--ona-border)}",
    ".ona .ona-sim .big{font-size:26px;font-weight:500;letter-spacing:-.02em}",
    ".ona .ona-legenda{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:12.5px;color:var(--ona-sec);margin-top:10px}",
    ".ona .ona-legenda span{display:inline-flex;align-items:center;gap:6px}",
    ".ona .ona-legenda .bol{width:9px;height:9px;border-radius:50%}",
    ".ona .ona-legenda .vaz{width:9px;height:9px;border-radius:50%;border:1.5px solid var(--ona-sec)}",
    ".ona .ona-nota{font-size:13px;color:var(--ona-sec);max-width:46rem}",
    ".ona .ona-tab{overflow-x:auto;margin-top:12px;border:1px solid var(--ona-border);border-radius:12px}",
    ".ona table{border-collapse:collapse;width:100%;font-size:13.5px;font-variant-numeric:tabular-nums}",
    ".ona th,.ona td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--ona-border);white-space:nowrap}",
    ".ona tr:last-child td{border-bottom:0}",
    ".ona th{color:var(--ona-sec);font-weight:500;font-size:12px;background:var(--ona-surface)}",
    ".ona td.num,.ona th.num{text-align:right}",
    ".ona .ona-mono{font-family:var(--ona-mono);font-size:12.5px}",
    ".ona .selo{font-size:12px;padding:2px 8px;border-radius:999px;border:1px solid var(--ona-border);color:var(--ona-sec)}",
    ".ona .selo.silo{border-color:#c0392b;color:#c0392b}",
    ".ona .ona-papeis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-top:14px}",
    ".ona .ona-papel{border:1px solid var(--ona-border);border-radius:12px;padding:14px;font-size:13px}",
    ".ona .ona-papel svg{display:block;margin-bottom:8px;color:var(--ona-sec)}",
    ".ona .ona-papel b{font-weight:500;font-size:14px;display:block}",
    ".ona .ona-papel p{margin:4px 0 8px;color:var(--ona-sec)}",
    ".ona .ona-sens{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:14px}",
    ".ona .ona-sens div{border:1px solid var(--ona-border);border-radius:12px;padding:14px}",
    ".ona .ona-sens .n{font-size:24px;font-weight:500}",
    ".ona .ona-sens p{margin:4px 0 0;font-size:13px;color:var(--ona-sec)}",
    ".ona details summary{cursor:pointer;color:var(--ona-accent);font-size:14px;margin-top:12px}",
    ".ona .ona-metodo{columns:2;column-gap:32px;font-size:13.5px;color:var(--ona-sec);margin-top:12px}",
    ".ona .ona-metodo p{margin:0 0 10px;break-inside:avoid}",
    ".ona .ona-metodo b{color:var(--ona-fg);font-weight:500}",
    ".ona .oculto{display:none!important}",
    "@media (max-width:900px){.ona .ona-rede{grid-template-columns:1fr}.ona .ona-cards{grid-template-columns:repeat(2,minmax(0,1fr))}.ona .ona-papeis{grid-template-columns:repeat(2,minmax(0,1fr))}.ona .ona-metodo{columns:1}}",
    "@media (max-width:620px){.ona .ona-drops{grid-template-columns:1fr}.ona .ona-sens{grid-template-columns:1fr}.ona canvas{height:420px}.ona h2{font-size:20px;margin-top:44px}.ona .ona-card .n{font-size:24px}.ona .ona-card{padding:14px}}"
  ].join("\n");

  var ICO_PESSOAS = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="9" cy="8" r="3.2"/><path d="M3 20c.8-3.4 3.2-5 6-5s5.2 1.6 6 5"/><circle cx="17" cy="9" r="2.4"/><path d="M16.5 14.2c2.3.2 3.9 1.8 4.5 4.3"/></svg>';
  var ICO_LIG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="5" cy="12" r="2.4"/><circle cx="19" cy="6" r="2.4"/><circle cx="19" cy="18" r="2.4"/><path d="M7.2 11 16.8 7M7.2 13l9.6 4"/></svg>';

  function esc(s) { return String(s === null || s === undefined ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function pct(x) { return Math.round(x * 100) + "%"; }
  function num(x, d) { return (x === null || x === undefined || isNaN(x)) ? "–" : x.toFixed(d).replace(".", ","); }
  function inteiro(x) { return Math.round(x).toLocaleString("pt-BR"); }
  function mulberry32(a) { return function () { a = (a + 0x6D2B79F5) >>> 0; var t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

  // ---------- planilhas: ler XLSX (sem biblioteca, usa DecompressionStream) ----------
  function lerZip(buf) {
    var dv = new DataView(buf), u8 = new Uint8Array(buf), i, eocd = -1;
    for (i = buf.byteLength - 22; i >= Math.max(0, buf.byteLength - 66000); i--) if (dv.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
    if (eocd < 0) throw new Error("arquivo .xlsx inválido");
    var total = dv.getUint16(eocd + 10, true), p = dv.getUint32(eocd + 16, true), arquivos = {}, dec = new TextDecoder();
    for (i = 0; i < total; i++) {
      var metodo = dv.getUint16(p + 10, true), comp = dv.getUint32(p + 20, true);
      var ln = dv.getUint16(p + 28, true), le = dv.getUint16(p + 30, true), lc = dv.getUint16(p + 32, true), loc = dv.getUint32(p + 42, true);
      var nome = dec.decode(u8.subarray(p + 46, p + 46 + ln));
      var ini = loc + 30 + dv.getUint16(loc + 26, true) + dv.getUint16(loc + 28, true);
      arquivos[nome] = { metodo: metodo, dados: u8.subarray(ini, ini + comp) };
      p += 46 + ln + le + lc;
    }
    return arquivos;
  }
  function inflar(ent) {
    if (ent.metodo === 0) return Promise.resolve(new TextDecoder().decode(ent.dados));
    if (typeof DecompressionStream === "undefined") return Promise.reject(new Error("este navegador não lê .xlsx; salve como CSV"));
    var s = new Blob([ent.dados]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
    return new Response(s).text();
  }
  function porTag(doc, tag) { return Array.prototype.slice.call(doc.getElementsByTagNameNS("*", tag)); }
  function lerXLSX(buf) {
    var zip = lerZip(buf), xml = function (t) { return new DOMParser().parseFromString(t, "application/xml"); };
    var achar = function (nome) { var k = Object.keys(zip).filter(function (x) { return x.toLowerCase() === nome.toLowerCase(); })[0]; return k ? zip[k] : null; };
    return Promise.all([inflar(achar("xl/workbook.xml")), inflar(achar("xl/_rels/workbook.xml.rels")), achar("xl/sharedStrings.xml") ? inflar(achar("xl/sharedStrings.xml")) : Promise.resolve("")])
      .then(function (t) {
        var wb = xml(t[0]), rels = xml(t[1]), mapa = {}, comp = [];
        porTag(rels, "Relationship").forEach(function (r) { mapa[r.getAttribute("Id")] = r.getAttribute("Target"); });
        if (t[2]) porTag(xml(t[2]), "si").forEach(function (si) { comp.push(porTag(si, "t").map(function (x) { return x.textContent; }).join("")); });
        var abas = porTag(wb, "sheet").map(function (s) {
          var rid = s.getAttributeNS("http://schemas.openxmlformats.org/officeDocument/2006/relationships", "id") || s.getAttribute("r:id");
          var alvo = (mapa[rid] || "").replace(/^\/?xl\//, "").replace(/^\//, "");
          return { nome: s.getAttribute("name"), arquivo: "xl/" + alvo };
        });
        return Promise.all(abas.map(function (a) { var e = achar(a.arquivo); return e ? inflar(e) : Promise.resolve(""); })).then(function (txts) {
          return abas.map(function (a, k) {
            var linhas = [];
            if (txts[k]) porTag(xml(txts[k]), "row").forEach(function (row) {
              var l = [];
              porTag(row, "c").forEach(function (c) {
                var ref = c.getAttribute("r") || "", col = 0, m = ref.match(/^[A-Z]+/);
                if (m) for (var q = 0; q < m[0].length; q++) col = col * 26 + m[0].charCodeAt(q) - 64;
                col = col ? col - 1 : l.length;
                var tipo = c.getAttribute("t"), v = porTag(c, "v")[0], val;
                if (tipo === "s") val = comp[+(v ? v.textContent : 0)] || "";
                else if (tipo === "inlineStr") val = porTag(c, "t").map(function (x) { return x.textContent; }).join("");
                else val = v ? v.textContent : "";
                l[col] = val;
              });
              linhas.push(l);
            });
            return { nome: a.nome, linhas: linhas };
          });
        });
      });
  }

  // ---------- planilhas: gerar XLSX do modelo (zip sem compressão) ----------
  var CRC = (function () { var t = [], c, n, k; for (n = 0; n < 256; n++) { c = n; for (k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  function crc32(u8) { var c = 0xFFFFFFFF; for (var i = 0; i < u8.length; i++) c = CRC[(c ^ u8[i]) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
  function zipar(arquivos) {
    var enc = new TextEncoder(), partes = [], central = [], off = 0;
    arquivos.forEach(function (f) {
      var nome = enc.encode(f.nome), dados = enc.encode(f.texto), crc = crc32(dados);
      var h = new DataView(new ArrayBuffer(30));
      h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(6, 0x0800, true); h.setUint16(8, 0, true);
      h.setUint32(14, crc, true); h.setUint32(18, dados.length, true); h.setUint32(22, dados.length, true); h.setUint16(26, nome.length, true);
      partes.push(new Uint8Array(h.buffer), nome, dados);
      var c = new DataView(new ArrayBuffer(46));
      c.setUint32(0, 0x02014b50, true); c.setUint16(4, 20, true); c.setUint16(6, 20, true); c.setUint16(8, 0x0800, true);
      c.setUint32(16, crc, true); c.setUint32(20, dados.length, true); c.setUint32(24, dados.length, true); c.setUint16(28, nome.length, true); c.setUint32(42, off, true);
      central.push(new Uint8Array(c.buffer), nome);
      off += 30 + nome.length + dados.length;
    });
    var tamC = central.reduce(function (s, x) { return s + x.length; }, 0), e = new DataView(new ArrayBuffer(22));
    e.setUint32(0, 0x06054b50, true); e.setUint16(8, arquivos.length, true); e.setUint16(10, arquivos.length, true); e.setUint32(12, tamC, true); e.setUint32(16, off, true);
    return new Blob(partes.concat(central, [new Uint8Array(e.buffer)]), { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
  }
  function xmlEsc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function aba(linhas) {
    var col = function (i) { return String.fromCharCode(65 + i); };
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' +
      linhas.map(function (l, r) {
        return '<row r="' + (r + 1) + '">' + l.map(function (v, c) {
          var ref = col(c) + (r + 1);
          return typeof v === "number" ? '<c r="' + ref + '"' + (r === 0 ? ' s="1"' : "") + '><v>' + v + "</v></c>" :
            '<c r="' + ref + '" t="inlineStr"' + (r === 0 ? ' s="1"' : "") + '><is><t xml:space="preserve">' + xmlEsc(v) + "</t></is></c>";
        }).join("") + "</row>";
      }).join("") + "</sheetData></worksheet>";
  }
  var MODELO_PESSOAS = [["id", "area", "cargo", "gestor_id", "unidade", "respondeu"], ["A001", "Comercial", "Gestor", "", "São Paulo", "sim"], ["A002", "Comercial", "Analista", "A001", "São Paulo", "sim"], ["A003", "Comercial", "Analista", "A001", "Campinas", "nao"], ["B001", "Operações", "Gestor", "", "Campinas", "sim"], ["B002", "Operações", "Especialista", "B001", "Campinas", "sim"]];
  var MODELO_LIGACOES = [["origem_id", "destino_id", "tipo", "peso"], ["A002", "A001", "informacao", 4], ["A002", "B002", "informacao", 2], ["A002", "B002", "ajuda", 3], ["B002", "B001", "informacao", 5], ["A001", "B001", "informacao", 3]];
  var MODELO_INSTR = [["Como preencher"], ["Aba pessoas: uma linha por pessoa convidada, inclusive quem não respondeu. Use um código no lugar do nome."], ["respondeu: sim ou nao. gestor_id: id do gestor imediato (vazio no topo). unidade é opcional."], ["Aba ligacoes: uma linha por nome citado no questionário. origem_id = quem respondeu; destino_id = quem foi citado."], ["tipo: o nome da pergunta (informacao, ajuda, ideias...). peso: frequência de 1 a 5 (opcional)."], ["Solte este arquivo na ONA de bolso. Os dados não saem do seu navegador."]];
  function baixar(blob, nome) { var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = nome; document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500); }
  function baixarModeloXLSX() {
    var sheets = [["pessoas", MODELO_PESSOAS], ["ligacoes", MODELO_LIGACOES], ["instrucoes", MODELO_INSTR]];
    var arquivos = [
      { nome: "[Content_Types].xml", texto: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>' + sheets.map(function (s, i) { return '<Override PartName="/xl/worksheets/sheet' + (i + 1) + '.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'; }).join("") + "</Types>" },
      { nome: "_rels/.rels", texto: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>' },
      { nome: "xl/workbook.xml", texto: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' + sheets.map(function (s, i) { return '<sheet name="' + s[0] + '" sheetId="' + (i + 1) + '" r:id="rId' + (i + 1) + '"/>'; }).join("") + "</sheets></workbook>" },
      { nome: "xl/_rels/workbook.xml.rels", texto: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + sheets.map(function (s, i) { return '<Relationship Id="rId' + (i + 1) + '" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet' + (i + 1) + '.xml"/>'; }).join("") + '<Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>' },
      { nome: "xl/styles.xml", texto: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs></styleSheet>' }
    ].concat(sheets.map(function (s, i) { return { nome: "xl/worksheets/sheet" + (i + 1) + ".xml", texto: aba(s[1]) }; }));
    baixar(zipar(arquivos), "ona-modelo.xlsx");
  }
  function csvDe(linhas) { return "﻿" + linhas.map(function (l) { return l.map(function (v) { v = String(v); return /[;"\n,]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }).join(","); }).join("\n") + "\n"; }

  // ---------- montagem ----------
  function montar(el, opcoes) {
    opcoes = opcoes || {};
    if (!document.getElementById("ona-css")) { var st = document.createElement("style"); st.id = "ona-css"; st.textContent = CSS; document.head.appendChild(st); }
    var ONA = raiz.ONA;
    el.classList.add("ona");
    el.innerHTML = [
      '<p class="ona-priv"><span><b>Seus dados não saem deste navegador.</b> A página lê os arquivos e calcula tudo aqui, sem enviar nada para servidor. Mesmo assim, use códigos no lugar de nomes e trate o resultado como diagnóstico da rede, nunca como avaliação de pessoas.</span></p>',
      '<div class="ona-drops">',
      '<div class="ona-drop" tabindex="0" role="button" data-alvo="pessoas" aria-label="Escolher a tabela de pessoas"><b><span class="ona-ico">' + ICO_PESSOAS + '</span>Pessoas</b><small>id, area, cargo, gestor_id, unidade, respondeu</small><span class="ona-st">Arraste o CSV ou clique para escolher</span><input type="file" multiple accept=".csv,.txt,.xlsx,text/csv"></div>',
      '<div class="ona-drop" tabindex="0" role="button" data-alvo="ligacoes" aria-label="Escolher a tabela de ligações"><b><span class="ona-ico">' + ICO_LIG + '</span>Ligações</b><small>origem_id, destino_id, tipo, peso</small><span class="ona-st">Arraste o CSV ou clique para escolher</span><input type="file" multiple accept=".csv,.txt,.xlsx,text/csv"></div>',
      "</div>",
      '<div class="ona-acoes"><button class="ona-bt" data-a="analisar" disabled>Analisar</button><button class="ona-bt sec" data-a="exemplo">Usar a base de exemplo</button></div>',
      '<div class="ona-modelos"><span>Modelo de planilha:</span><button class="ona-link" data-a="xlsx">Excel (.xlsx, duas abas)</button><button class="ona-link" data-a="csvp">pessoas.csv</button><button class="ona-link" data-a="csvl">ligacoes.csv</button><span>· Um .xlsx com as abas pessoas e ligacoes também pode ser solto em qualquer uma das caixas.</span></div>',
      '<p class="ona-msg" role="status"></p>',
      '<section class="ona-res oculto">',
      '<div class="ona-barra"><span class="ona-eyebrow" data-r="fonte"></span><label class="ona-campo">Pergunta <select data-r="tipo"></select></label></div>',
      '<div class="ona-conf" data-r="conf"></div>',
      '<h2>Visão geral</h2><p class="ona-lead">Os números que resumem a rede. Cada um vem com o que significa.</p><div class="ona-cards" data-r="cards"></div>',
      '<h2>O que a rede está dizendo</h2><p class="ona-lead">Do mais importante para o menos. Clique num código para ver a pessoa na rede.</p><div class="ona-ins" data-r="ins"></div>',
      '<h2 data-r="ancora-rede">A rede</h2><p class="ona-lead" data-r="rede-lead">Cada ponto é uma pessoa; cada linha, uma ligação citada em qualquer sentido. Passe o mouse (ou toque) para ver o detalhe e clique para destacar a pessoa e os vizinhos.</p>',
      '<div class="ona-acoes" style="margin-top:4px"><label class="ona-campo">Cor por <select data-r="cor"><option value="area">área</option><option value="comunidade">grupo real (comunidade)</option><option value="papel">papel de corretagem</option></select></label><label class="ona-campo">Buscar <input type="search" data-r="busca" placeholder="código da pessoa" size="14"></label></div>',
      '<div class="ona-chips" data-r="filtro"></div>',
      '<div class="ona-rede" data-r="rede"><div class="ona-tela"><canvas aria-label="Rede de ligações entre as pessoas" role="img"></canvas><div class="ona-aviso-sim oculto"></div><div class="ona-tip"></div></div><aside class="ona-painel" data-r="painel"></aside></div>',
      '<div class="ona-legenda" data-r="legenda"></div>',
      '<p class="ona-nota" data-r="rede-nota"></p>',
      '<h2>Risco de dependência</h2><p class="ona-lead">O que acontece com a rede se cada uma das pessoas com maior intermediação sair. "Sem caminho" são pessoas que deixam de ter qualquer rota de conversa até a maior parte da organização. Eficiência é a média de 1/distância entre todos os pares.</p><div class="ona-tab"><table data-r="riscos"></table></div>',
      '<h2>Por área</h2><p class="ona-lead" data-r="areas-lead"></p><div class="ona-tab"><table data-r="areas"></table></div>',
      '<h2>Papéis de corretagem</h2><p class="ona-lead">Para cada caminho em que a informação vai de A para B e de B para C, sem ligação direta entre A e C, B faz a corretagem. O papel depende das áreas das três pessoas (Gould e Fernandez, 1989). A informação corre de quem é citado para quem cita.</p><div class="ona-papeis" data-r="papeis"></div>',
      '<h2>Sensibilidade à não resposta</h2><p class="ona-lead" data-r="sens-lead"></p><div class="ona-sens" data-r="sens"></div>',
      '<h2>Por pessoa</h2><p class="ona-lead">Escondido por padrão. Serve para entender a rede, não para ranquear gente.</p><div class="ona-acoes"><button class="ona-bt sec peq" data-a="tabpessoas">Mostrar a tabela por pessoa</button><button class="ona-bt sec peq" data-a="csv">Baixar métricas por pessoa (CSV)</button></div><div class="ona-tab oculto" data-r="tabpessoas-w"><table data-r="pessoas"></table></div>',
      '<h2>Como ler e de onde vêm os números</h2><div class="ona-metodo" data-r="metodo"></div>',
      "</section>"
    ].join("");

    var $ = function (s) { return el.querySelector(s); }, R = function (k) { return el.querySelector('[data-r="' + k + '"]'); };
    var estado = { textos: { pessoas: null, ligacoes: null }, nomes: {}, dados: null, res: null, layouts: {}, sel: -1, hover: -1, filtro: null, saida: null };

    // ----- entrada -----
    function classificar(linhas) {
      if (!linhas.length) return null;
      var k = Object.keys(linhas[0]);
      if (k.indexOf("origem_id") >= 0 && k.indexOf("destino_id") >= 0) return "ligacoes";
      if (k.indexOf("id") >= 0) return "pessoas";
      return null;
    }
    function receber(arquivos, alvo) {
      arquivos = Array.prototype.slice.call(arquivos || []);
      if (!arquivos.length) return;
      msg("");
      Promise.all(arquivos.map(function (f) {
        if (/\.xlsx$/i.test(f.name)) return f.arrayBuffer().then(lerXLSX).then(function (abas) {
          return abas.map(function (a) { return { nome: f.name + " · aba " + a.nome, linhas: ONA.deLinhas(a.linhas) }; });
        });
        return f.text().then(function (t) { return [{ nome: f.name, linhas: ONA.lerCSV(t) }]; });
      })).then(function (lst) {
        var achou = 0;
        [].concat.apply([], lst).forEach(function (x) {
          var tipo = classificar(x.linhas) || (arquivos.length === 1 && lst[0].length === 1 ? alvo : null);
          if (!tipo) return;
          estado.textos[tipo] = x.linhas; estado.nomes[tipo] = x.nome; achou++;
        });
        if (!achou) msg('<span class="erro">Não reconheci as colunas. A tabela de pessoas precisa de id e area; a de ligações, de origem_id e destino_id.</span>');
        atualizarCaixas();
        if (estado.textos.pessoas && estado.textos.ligacoes && achou >= 2) analisarArquivos();
      }).catch(function (e) { msg('<span class="erro">Não consegui ler o arquivo: ' + esc(e.message) + ".</span>"); });
    }
    function atualizarCaixas() {
      el.querySelectorAll(".ona-drop").forEach(function (d) {
        var t = d.getAttribute("data-alvo"), l = estado.textos[t];
        d.classList.toggle("pronto", !!l);
        d.querySelector(".ona-st").textContent = l ? estado.nomes[t] + " · " + inteiro(l.length) + " linhas" : "Arraste o CSV ou clique para escolher";
      });
      $('[data-a="analisar"]').disabled = !(estado.textos.pessoas && estado.textos.ligacoes);
    }
    el.querySelectorAll(".ona-drop").forEach(function (d) {
      var inp = d.querySelector("input"), alvo = d.getAttribute("data-alvo");
      d.addEventListener("click", function () { inp.click(); });
      d.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); inp.click(); } });
      inp.addEventListener("change", function () { receber(inp.files, alvo); inp.value = ""; });
      ["dragenter", "dragover"].forEach(function (ev) { d.addEventListener(ev, function (e) { e.preventDefault(); d.classList.add("arrastando"); }); });
      ["dragleave", "drop"].forEach(function (ev) { d.addEventListener(ev, function (e) { e.preventDefault(); d.classList.remove("arrastando"); }); });
      d.addEventListener("drop", function (e) { receber(e.dataTransfer.files, alvo); });
    });
    function msg(h) { $(".ona-msg").innerHTML = h; }

    function analisarArquivos() { carregar(estado.textos.pessoas, estado.textos.ligacoes, (estado.nomes.pessoas || "") + " + " + (estado.nomes.ligacoes || "")); }
    function carregar(pessoas, ligacoes, fonte) {
      var v = ONA.validar(pessoas, ligacoes);
      if (v.erros.length) { msg('<span class="erro">' + v.erros.map(esc).join("<br>") + "</span>"); return; }
      msg(v.avisos.length ? '<span class="aviso">' + v.avisos.map(esc).join("<br>") + "</span>" : "");
      estado.dados = { pessoas: pessoas, ligacoes: ligacoes };
      estado.layouts = {}; estado.sel = -1; estado.filtro = null; estado.saida = null;
      var tipos = {}; ligacoes.forEach(function (l) { if (l.tipo) tipos[l.tipo] = 1; });
      R("tipo").innerHTML = '<option value="todos">todas as perguntas</option>' + Object.keys(tipos).map(function (t) { return '<option value="' + esc(t) + '">' + esc(t) + "</option>"; }).join("");
      R("tipo").parentNode.classList.toggle("oculto", Object.keys(tipos).length < 2);
      R("fonte").textContent = fonte;
      rodar(true);
    }
    function rodar(rolar) {
      if (!estado.dados) return;
      msg('<span class="aviso">Calculando…</span>');
      setTimeout(function () {
        var t0 = Date.now();
        estado.res = ONA.analisar(estado.dados.pessoas, estado.dados.ligacoes, { tipo: R("tipo").value || "todos" });
        estado.ms = Date.now() - t0;
        estado.sel = -1; estado.saida = null;
        msg("");
        $(".ona-res").classList.remove("oculto");
        render();
        if (rolar && opcoes.rolar !== false) $(".ona-res").scrollIntoView({ behavior: "smooth", block: "start" });
      }, 20);
    }

    $('[data-a="analisar"]').onclick = analisarArquivos;
    $('[data-a="exemplo"]').onclick = function () {
      var ex = opcoes.exemplo || raiz.EXEMPLO;
      if (!ex) { msg('<span class="erro">Base de exemplo indisponível.</span>'); return; }
      carregar(ONA.lerCSV(ex.pessoas), ONA.lerCSV(ex.ligacoes), "Base de exemplo: organização fictícia de 114 pessoas");
    };
    $('[data-a="xlsx"]').onclick = baixarModeloXLSX;
    $('[data-a="csvp"]').onclick = function () { baixar(new Blob([csvDe(MODELO_PESSOAS)], { type: "text/csv" }), "pessoas.csv"); };
    $('[data-a="csvl"]').onclick = function () { baixar(new Blob([csvDe(MODELO_LIGACOES)], { type: "text/csv" }), "ligacoes.csv"); };
    R("tipo").onchange = function () { rodar(false); };
    R("cor").onchange = function () { legenda(); desenhar(); };
    R("busca").addEventListener("input", function () {
      var q = this.value.trim().toLowerCase(); if (!q || !estado.res) return;
      var i = estado.res.por_pessoa.findIndex(function (p) { return String(p.id).toLowerCase() === q; });
      if (i >= 0) selecionar(i, false);
    });
    $('[data-a="tabpessoas"]').onclick = function () {
      var w = R("tabpessoas-w"); w.classList.toggle("oculto");
      this.textContent = w.classList.contains("oculto") ? "Mostrar a tabela por pessoa" : "Esconder a tabela por pessoa";
    };
    $('[data-a="csv"]').onclick = function () {
      var cab = ["id", "area", "cargo", "respondeu", "citacoes_recebidas", "citacoes_feitas", "conexoes", "intermediacao", "intermediacao_dirigida", "restricao", "tamanho_efetivo", "nucleo", "comunidade", "papel", "coordenador", "consultor", "representante", "porteiro", "ligacao"];
      var linhas = [cab.join(";")].concat(estado.res.por_pessoa.map(function (p) {
        return cab.map(function (k) {
          var v = k === "comunidade" ? p[k] + 1 : p[k];
          if (v === null || v === undefined) v = "";
          if (typeof v === "boolean") v = v ? "sim" : "nao";
          if (typeof v === "number" && v % 1) v = v.toFixed(4).replace(".", ",");
          return String(v).replace(/;/g, ",");
        }).join(";");
      }));
      baixar(new Blob(["﻿" + linhas.join("\n")], { type: "text/csv" }), "ona-metricas-por-pessoa.csv");
    };

    // ----- render -----
    function render() {
      var r = estado.res;
      var c = r.confiabilidade, s = r.sensibilidade;
      var conf = R("conf");
      conf.className = "ona-conf " + c.nivel;
      conf.innerHTML = c.nivel === "insuficiente" ?
        "<b>Dados insuficientes para concluir sobre pontes e isolados.</b> Só " + pct(r.taxa_resposta) + " das pessoas responderam (o mínimo para essa leitura é " + pct(ONA.LIMIAR_RESPOSTA) + "). Use o resultado para planejar a próxima rodada." :
        (c.nivel === "cautela" ? "<b>Leia com cautela:</b> " + esc(c.motivos.join("; ")) + ". Veja a seção de sensibilidade à não resposta." :
          "<b>Base consistente.</b> " + pct(r.taxa_resposta) + " de resposta e resultados estáveis quando simulamos mais não resposta.");
      cards(); listaInsights(); filtroAreas(); legenda(); tabelaRiscos(); tabelaAreas(); papeis(); sensib(); tabelaPessoas(); metodo();
      var grande = r.pessoas > LIMITE_DESENHO;
      R("rede").classList.toggle("oculto", grande); R("filtro").classList.toggle("oculto", grande); R("legenda").classList.toggle("oculto", grande);
      R("rede-nota").innerHTML = grande ? "Com mais de " + LIMITE_DESENHO + " pessoas, o desenho fica ilegível e pesado; a página mostra só as métricas. Filtre a base por diretoria para ver a rede." :
        "Tamanho do ponto = intermediação na rede simetrizada (quanto a pessoa está no caminho entre outras). Ponto vazado = não respondeu ao questionário; ela aparece porque alguém a citou. Calculado em " + inteiro(estado.ms) + " ms neste navegador.";
      if (!grande) { painel(); desenhar(); }
      R("sens-lead").innerHTML = "Quem não responde deixa a rede furada exatamente nas ligações que faria. Para saber se as conclusões aguentam, a página apaga as citações de mais " + (s ? s.pessoas_retiradas : "10%") + " pessoas que responderam (" + (s ? s.replicas : "") + " sorteios) e refaz as contas. Regra de leitura: abaixo de " + pct(ONA.LIMIAR_RESPOSTA) + " de resposta, o relatório não conclui nada sobre pontes e isolados.";
    }

    function cards() {
      var r = estado.res, risco = r.riscos[0], silos = r.areas.filter(function (a) { return a.silo; });
      var c = [
        [inteiro(r.pessoas), "pessoas", inteiro(r.responderam) + " responderam (" + pct(r.taxa_resposta) + "). Quem não respondeu aparece quando é citado."],
        [inteiro(r.ligacoes), "pares ligados", "Pares em que pelo menos um citou o outro. Densidade de " + num(r.densidade * 100, 1) + "% dos pares possíveis."],
        [r.comunidades, "grupos reais", "Comunidades achadas pelo Louvain (modularidade " + num(r.modularidade, 2) + "; acima de 0,3 = grupos bem separados)."],
        [num(r.distancia_media, 1), "passos em média", "Distância média entre duas pessoas, contando quem fala com quem. Quanto menor, mais rápido a informação circula."],
        [silos.length, silos.length === 1 ? "área em silo" : "áreas em silo", silos.length ? silos.map(function (a) { return esc(a.area); }).join(", ") + ": muito mais fechada do que o acaso daria." : "Nenhuma área está muito mais fechada do que o acaso daria."],
        [risco ? inteiro(risco.perdem_caminho) : "0", "sem caminho numa saída", risco && risco.perdem_caminho ? "Pessoas que ficam sem rota até o resto da rede se " + esc(risco.id) + " sair." : "Nenhuma saída isolada desconecta alguém."],
        [r.isolados.length, "fora do fluxo", "Ninguém citou e têm no máximo uma ligação. Sinal para conversar, não diagnóstico."],
        [pct(r.reciprocidade), "reciprocidade", "Entre quem respondeu, a fração dos pares que se citam nos dois sentidos."]
      ];
      R("cards").innerHTML = c.map(function (x) { return '<div class="ona-card"><div class="n">' + x[0] + '</div><div class="r">' + x[1] + '</div><div class="e">' + x[2] + "</div></div>"; }).join("");
    }
    var NOME_NIVEL = { alerta: "Alerta", risco: "Risco", atencao: "Atenção", info: "Informação" };
    function listaInsights() {
      R("ins").innerHTML = estado.res.insights.map(function (i) {
        return '<article class="ona-in ' + i.nivel + '"><span class="tag"><i></i>' + NOME_NIVEL[i.nivel] + "</span><b>" + esc(i.titulo) + "</b><p>" + esc(i.texto) + "</p>" +
          (i.ids && i.ids.length && estado.res.pessoas <= LIMITE_DESENHO ? '<div class="ona-chips">' + i.ids.map(function (id) { return '<button class="ona-chip" data-ver="' + esc(id) + '">ver ' + esc(id) + " na rede</button>"; }).join("") + "</div>" : "") +
          "</article>";
      }).join("");
      R("ins").querySelectorAll("[data-ver]").forEach(function (b) {
        b.onclick = function () { var i = indicePorId(b.getAttribute("data-ver")); if (i >= 0) { selecionar(i, true); } };
      });
    }
    function indicePorId(id) { return estado.res.por_pessoa.findIndex(function (p) { return p.id === id; }); }

    // ----- cores -----
    function escuro() { // pelo fundo da página: funciona com qualquer forma de trocar o tema
      var m = String(getComputedStyle(document.body).backgroundColor).match(/\d+(\.\d+)?/g);
      return m ? (+m[0] * 0.299 + +m[1] * 0.587 + +m[2] * 0.114) < 128 : false;
    }
    function grupos() {
      var r = estado.res, modo = R("cor").value, chave, cont = {};
      r.por_pessoa.forEach(function (p) {
        chave = modo === "area" ? p.area : modo === "comunidade" ? "Grupo " + (p.comunidade + 1) : (p.papel ? PAPEL_CURTO[p.papel] : "Sem papel de destaque");
        cont[chave] = (cont[chave] || 0) + 1;
      });
      var ordem = Object.keys(cont).sort(function (a, b) { return cont[b] - cont[a] || (a < b ? -1 : 1); });
      if (modo === "papel") ordem = ["Porteiro", "Representante", "Ligação", "Consultor", "Coordenador", "Sem papel de destaque"].filter(function (k) { return cont[k]; });
      if (modo === "area") ordem.sort(function (a, b) { return a < b ? -1 : 1; });
      var pal = escuro() ? CORES_ESCURO : CORES_CLARO, cor = {};
      ordem.forEach(function (k, i) {
        cor[k] = k === "Sem papel de destaque" ? (escuro() ? "#4a4643" : "#d8d4cf") : (i < 7 || ordem.length <= 8 ? pal[i] : (escuro() ? COR_OUTRAS.escuro : COR_OUTRAS.claro));
      });
      return { chave: function (p) { return modo === "area" ? p.area : modo === "comunidade" ? "Grupo " + (p.comunidade + 1) : (p.papel ? PAPEL_CURTO[p.papel] : "Sem papel de destaque"); }, cor: cor, ordem: ordem, modo: modo };
    }
    function legenda() {
      var g = grupos();
      var itens = g.ordem.slice(0, 8).map(function (k) { return '<span><i class="bol" style="background:' + g.cor[k] + '"></i>' + esc(k) + "</span>"; });
      if (g.ordem.length > 8) itens.push("<span>demais em cinza</span>");
      itens.push('<span><i class="vaz"></i>não respondeu</span>');
      R("legenda").innerHTML = itens.join("");
    }
    function filtroAreas() {
      var areas = {}; estado.res.por_pessoa.forEach(function (p) { areas[p.area] = (areas[p.area] || 0) + 1; });
      var nomes = Object.keys(areas).sort();
      R("filtro").innerHTML = '<button class="ona-chip ativo" data-area="">Todas as áreas</button>' + nomes.map(function (a) { return '<button class="ona-chip" data-area="' + esc(a) + '">' + esc(a) + " · " + areas[a] + "</button>"; }).join("");
      R("filtro").querySelectorAll("[data-area]").forEach(function (b) {
        b.onclick = function () {
          estado.filtro = b.getAttribute("data-area") || null;
          R("filtro").querySelectorAll("[data-area]").forEach(function (x) { x.classList.toggle("ativo", x === b); });
          desenhar();
        };
      });
    }

    // ----- layout de força (Fruchterman e Reingold, determinístico) -----
    function layout() {
      var chave = R("tipo").value || "todos";
      if (estado.layouts[chave]) return estado.layouts[chave];
      var r = estado.res, n = r.pessoas, adj = r._rede.adjS, rnd = mulberry32(42), i, j, it;
      var arestas = []; for (i = 0; i < n; i++) adj[i].forEach(function (k) { if (k > i) arestas.push([i, k]); });
      var areas = {}, na = 0; r.por_pessoa.forEach(function (p) { if (!(p.area in areas)) areas[p.area] = na++; });
      var x = new Float64Array(n), y = new Float64Array(n);
      for (i = 0; i < n; i++) { var ang = 2 * Math.PI * areas[r.por_pessoa[i].area] / Math.max(1, na); x[i] = 0.5 + Math.cos(ang) * 0.25 + (rnd() - 0.5) * 0.15; y[i] = 0.5 + Math.sin(ang) * 0.25 + (rnd() - 0.5) * 0.15; }
      var k = Math.sqrt(1 / Math.max(1, n)) * 0.9, temp = 0.1, iters = n > 300 ? 160 : 300;
      var dx = new Float64Array(n), dy = new Float64Array(n);
      for (it = 0; it < iters; it++) {
        dx.fill(0); dy.fill(0);
        for (i = 0; i < n; i++) for (j = i + 1; j < n; j++) {
          var ddx = x[i] - x[j], ddy = y[i] - y[j], d2 = ddx * ddx + ddy * ddy || 1e-6, f = k * k / d2;
          dx[i] += ddx * f; dy[i] += ddy * f; dx[j] -= ddx * f; dy[j] -= ddy * f;
        }
        for (var e = 0; e < arestas.length; e++) {
          var a = arestas[e][0], b = arestas[e][1], ex = x[a] - x[b], ey = y[a] - y[b], d = Math.sqrt(ex * ex + ey * ey) || 1e-6, fa = d / k;
          dx[a] -= ex * fa; dy[a] -= ey * fa; dx[b] += ex * fa; dy[b] += ey * fa;
        }
        for (i = 0; i < n; i++) {
          var gr = adj[i].length ? 0.6 : 4; // gravidade: quem não tem ligação não foge da tela
          dx[i] += (0.5 - x[i]) * gr; dy[i] += (0.5 - y[i]) * gr;
          var m = Math.sqrt(dx[i] * dx[i] + dy[i] * dy[i]) || 1, passo = Math.min(m, temp);
          x[i] += dx[i] / m * passo; y[i] += dy[i] / m * passo;
        }
        temp *= 0.985;
      }
      var minx = Infinity, maxx = -Infinity, miny = Infinity, maxy = -Infinity;
      for (i = 0; i < n; i++) { minx = Math.min(minx, x[i]); maxx = Math.max(maxx, x[i]); miny = Math.min(miny, y[i]); maxy = Math.max(maxy, y[i]); }
      var pos = []; for (i = 0; i < n; i++) pos.push({ x: (x[i] - minx) / ((maxx - minx) || 1), y: (y[i] - miny) / ((maxy - miny) || 1) });
      return (estado.layouts[chave] = { pos: pos, arestas: arestas });
    }

    var cv = el.querySelector("canvas"), tip = el.querySelector(".ona-tip"), geo = null;
    function desenhar() {
      var r = estado.res; if (!r || r.pessoas > LIMITE_DESENHO) return;
      var W = cv.clientWidth, H = cv.clientHeight, dpr = window.devicePixelRatio || 1;
      if (!W || !H) return;
      cv.width = W * dpr; cv.height = H * dpr;
      var L = layout(), pad = Math.min(36, W * 0.06), ctx = cv.getContext("2d");
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
      var cs = getComputedStyle(el), fg = cs.getPropertyValue("--ona-fg").trim() || "#0a0a0a", bg = cs.getPropertyValue("--ona-bg").trim() || "#fff", ac = cs.getPropertyValue("--ona-accent").trim() || "#8b5e3c";
      var topo = estado.saida ? Math.max(pad, W < 500 ? 96 : 74) : pad; // espaço para o aviso da simulação
      var px = function (i) { return pad + L.pos[i].x * (W - 2 * pad); }, py = function (i) { return topo + L.pos[i].y * (H - topo - pad); };
      var g = grupos(), maxB = Math.max.apply(null, r.por_pessoa.map(function (p) { return p.intermediacao; })) || 1;
      var escala = Math.min(1, Math.max(0.6, W / 900)) * (r.pessoas > 250 ? 0.75 : 1);
      var raio = function (p) { return (3.5 + 15 * Math.sqrt(p.intermediacao / maxB)) * escala; };
      var sel = estado.sel, vizSel = {}, saida = estado.saida, removido = {}, perde = {};
      var av = el.querySelector(".ona-aviso-sim");
      av.classList.toggle("oculto", !saida);
      if (saida) av.innerHTML = "<b>Sem " + esc(saida.ids.join(", ")) + ":</b> " + (saida.perdem_caminho.length ? saida.perdem_caminho.length + (saida.perdem_caminho.length === 1 ? " pessoa fica" : " pessoas ficam") + " sem caminho até o resto da rede (anel)" : "ninguém perde o caminho até o resto da rede") + "; eficiência " + (saida.queda_eficiencia > 0 ? "cai " : "muda ") + pct(saida.queda_eficiencia) + ".";
      if (sel >= 0) r._rede.adjS[sel].forEach(function (k) { vizSel[k] = 1; });
      if (saida) { saida.ids.forEach(function (id) { removido[indicePorId(id)] = 1; }); saida.perdem_caminho.forEach(function (id) { perde[indicePorId(id)] = 1; }); }
      var ativo = function (i) {
        if (estado.filtro && r.por_pessoa[i].area !== estado.filtro) return false;
        if (sel >= 0 && !saida) return i === sel || vizSel[i];
        return true;
      };
      // ligações
      ctx.lineWidth = 1;
      L.arestas.forEach(function (e) {
        var a = e[0], b = e[1];
        if (removido[a] || removido[b]) return;
        var dest = (sel >= 0 && !saida && (a === sel || b === sel));
        var on = ativo(a) && ativo(b);
        ctx.strokeStyle = dest ? ac : fg;
        ctx.globalAlpha = dest ? 0.7 : (on ? (sel >= 0 && !saida ? 0.25 : 0.09) : 0.025);
        ctx.beginPath(); ctx.moveTo(px(a), py(a)); ctx.lineTo(px(b), py(b)); ctx.stroke();
      });
      ctx.globalAlpha = 1;
      // pessoas (as maiores por cima)
      var ordem = r.por_pessoa.map(function (p, i) { return i; }).sort(function (a, b) { return r.por_pessoa[a].intermediacao - r.por_pessoa[b].intermediacao; });
      geo = [];
      ordem.forEach(function (i) {
        var p = r.por_pessoa[i], x = px(i), y = py(i), rr = raio(p), cor = g.cor[g.chave(p)];
        geo[i] = { x: x, y: y, r: rr };
        if (removido[i]) {
          ctx.globalAlpha = 1; ctx.strokeStyle = fg; ctx.lineWidth = 2; ctx.setLineDash([3, 3]);
          ctx.beginPath(); ctx.arc(x, y, rr + 3, 0, 2 * Math.PI); ctx.stroke(); ctx.setLineDash([]);
          ctx.beginPath(); ctx.moveTo(x - rr * 0.6, y - rr * 0.6); ctx.lineTo(x + rr * 0.6, y + rr * 0.6); ctx.moveTo(x + rr * 0.6, y - rr * 0.6); ctx.lineTo(x - rr * 0.6, y + rr * 0.6); ctx.stroke();
          return;
        }
        var on = ativo(i);
        ctx.globalAlpha = saida ? (perde[i] ? 1 : 0.25) : (on ? 1 : 0.12);
        ctx.beginPath(); ctx.arc(x, y, rr, 0, 2 * Math.PI);
        if (p.respondeu) { ctx.fillStyle = cor; ctx.fill(); ctx.strokeStyle = bg; ctx.lineWidth = 1.5; ctx.stroke(); }
        else { ctx.fillStyle = bg; ctx.fill(); ctx.strokeStyle = cor; ctx.lineWidth = 2; ctx.stroke(); }
        if (perde[i]) { ctx.strokeStyle = ac; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(x, y, rr + 3.5, 0, 2 * Math.PI); ctx.stroke(); }
        if (i === sel) { ctx.globalAlpha = 1; ctx.strokeStyle = fg; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x, y, rr + 4, 0, 2 * Math.PI); ctx.stroke(); }
        if (i === estado.hover) { ctx.globalAlpha = 1; ctx.strokeStyle = fg; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y, rr + 2.5, 0, 2 * Math.PI); ctx.stroke(); }
      });
      ctx.globalAlpha = 1;
      // rótulos só das pessoas em destaque
      var rot = {};
      if (sel >= 0) rot[sel] = 1;
      if (saida) saida.ids.forEach(function (id) { rot[indicePorId(id)] = 1; });
      if (sel < 0 && !saida) r.pontes.slice(0, 3).forEach(function (p) { rot[indicePorId(p.id)] = 1; });
      ctx.font = "500 11.5px " + (cs.getPropertyValue("--ona-mono").trim() || "monospace"); ctx.textBaseline = "middle";
      Object.keys(rot).forEach(function (k) {
        var i = +k, gx = geo[i]; if (!gx) return;
        var t = r.por_pessoa[i].id, w = ctx.measureText(t).width, lx = gx.x + gx.r + 6, ly = gx.y;
        if (lx + w + 8 > W) lx = gx.x - gx.r - 10 - w;
        ctx.fillStyle = bg; ctx.globalAlpha = 0.85; ctx.fillRect(lx - 3, ly - 8, w + 6, 16); ctx.globalAlpha = 1;
        ctx.fillStyle = fg; ctx.fillText(t, lx, ly);
      });
    }

    function maisPerto(ev) {
      if (!geo) return -1;
      var b = cv.getBoundingClientRect(), x = ev.clientX - b.left, y = ev.clientY - b.top, melhor = -1, md = Infinity;
      geo.forEach(function (gx, i) { if (!gx) return; var d = Math.hypot(gx.x - x, gx.y - y); if (d < gx.r + 8 && d < md) { md = d; melhor = i; } });
      return melhor;
    }
    function textoTip(i) {
      var r = estado.res, p = r.por_pessoa[i];
      var rank = r.por_pessoa.filter(function (q) { return q.intermediacao > p.intermediacao; }).length + 1;
      return "<b>" + esc(p.id) + "</b> · " + esc(p.area) + (p.cargo ? " · " + esc(p.cargo) : "") +
        "<br>Citada por " + p.citacoes_recebidas + (p.respondeu ? ", citou " + p.citacoes_feitas : " · não respondeu") +
        "<br>Intermediação " + num(p.intermediacao, 3) + " (" + rank + "ª de " + r.pessoas + ")" +
        "<br>Papel: " + (p.papel ? esc(PAPEL_CURTO[p.papel].toLowerCase()) : "sem destaque") +
        (p.restricao !== null ? "<br>Restrição de Burt " + num(p.restricao, 2) : "");
    }
    cv.addEventListener("pointermove", function (ev) {
      if (ev.pointerType === "touch") return;
      var i = maisPerto(ev);
      if (i !== estado.hover) { estado.hover = i; desenhar(); }
      if (i < 0) { tip.style.opacity = 0; cv.style.cursor = "default"; return; }
      cv.style.cursor = "pointer";
      tip.innerHTML = textoTip(i);
      var b = cv.getBoundingClientRect(), x = ev.clientX - b.left, y = ev.clientY - b.top;
      tip.style.opacity = 1;
      var tw = tip.offsetWidth, th = tip.offsetHeight;
      tip.style.left = Math.min(b.width - tw - 8, Math.max(8, x + 14)) + "px";
      tip.style.top = (y + th + 20 > b.height ? y - th - 12 : y + 14) + "px";
    });
    cv.addEventListener("pointerleave", function () { estado.hover = -1; tip.style.opacity = 0; desenhar(); });
    cv.addEventListener("click", function (ev) {
      var i = maisPerto(ev);
      if (i < 0) { if (!estado.saida) { estado.sel = -1; painel(); desenhar(); } return; }
      selecionar(i, false);
    });

    function selecionar(i, rolar) {
      estado.sel = i; estado.saida = null;
      var p = estado.res.por_pessoa[i];
      if (estado.filtro && p.area !== estado.filtro) {
        estado.filtro = null;
        R("filtro").querySelectorAll("[data-area]").forEach(function (x) { x.classList.toggle("ativo", !x.getAttribute("data-area")); });
      }
      painel(); desenhar();
      if (rolar) R("ancora-rede").scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function painel() {
      var r = estado.res, pn = R("painel");
      if (estado.sel < 0) {
        pn.innerHTML = '<span class="ona-eyebrow">E se essa pessoa sair?</span><p class="vazio">Clique numa pessoa da rede (ou num código dos insights) para ver os números dela e simular a saída: quem perde o caminho até o resto da organização e quanto a rede fica mais lenta.</p>' +
          (r.riscos.length ? '<p class="vazio">Sugestão: comece por <button class="ona-link" data-sel="' + esc(r.riscos[0].id) + '">' + esc(r.riscos[0].id) + "</button>, a saída de maior impacto.</p>" : "");
        var b = pn.querySelector("[data-sel]"); if (b) b.onclick = function () { selecionar(indicePorId(b.getAttribute("data-sel")), false); };
        return;
      }
      var p = r.por_pessoa[estado.sel], s = estado.saida;
      var vz = r._rede.adjS[estado.sel].length;
      var h = '<span class="ona-eyebrow">Pessoa selecionada</span><h3 class="ona-mono" style="font-size:18px;margin-top:4px">' + esc(p.id) + "</h3>" +
        '<span style="color:var(--ona-sec)">' + esc(p.area) + (p.cargo ? " · " + esc(p.cargo) : "") + (p.respondeu ? "" : " · não respondeu") + "</span>" +
        "<dl><dt>Citada por</dt><dd>" + p.citacoes_recebidas + "</dd><dt>Citou</dt><dd>" + (p.respondeu ? p.citacoes_feitas : "–") + "</dd><dt>Ligações (vizinhos)</dt><dd>" + vz + "</dd>" +
        "<dt>Intermediação</dt><dd>" + num(p.intermediacao, 3) + "</dd><dt>Restrição de Burt</dt><dd>" + num(p.restricao, 2) + "</dd><dt>Papel</dt><dd>" + (p.papel ? esc(PAPEL_CURTO[p.papel]) : "sem destaque") + "</dd></dl>";
      if (!s) h += '<button class="ona-bt peq" data-a="simular">Simular a saída de ' + esc(p.id) + '</button> <button class="ona-link" data-a="limpar" style="margin-left:8px">limpar</button>';
      else {
        var areas = Object.keys(s.areas_afetadas).sort(function (a, b) { return s.areas_afetadas[b] - s.areas_afetadas[a]; });
        h += '<div class="ona-sim"><span class="ona-eyebrow">Sem ' + esc(p.id) + "</span>" +
          '<div class="big">' + s.perdem_caminho.length + "</div><div>" + (s.perdem_caminho.length === 1 ? "pessoa fica" : "pessoas ficam") + " sem caminho até o resto da rede" +
          (areas.length ? " (" + areas.map(function (a) { return esc(a) + " " + s.areas_afetadas[a]; }).join(", ") + ")" : "") + ".</div>" +
          "<dl><dt>Eficiência da rede</dt><dd>" + num(s.eficiencia_antes, 3) + " → " + num(s.eficiencia, 3) + "</dd><dt>Queda</dt><dd>" + pct(s.queda_eficiencia) + "</dd>" +
          (s.perdem_caminho.length ? "" : "<dt>Distância média</dt><dd>" + num(s.distancia_media_antes, 2) + " → " + num(s.distancia_media, 2) + "</dd>") +
          "<dt>Grupos desconectados</dt><dd>" + s.componentes_antes + " → " + s.componentes + "</dd></dl>" +
          '<p class="vazio" style="margin:0 0 10px">' + (s.perdem_caminho.length ? "Os pontos com anel ficam isolados do resto. É um retrato do risco da rede, não do valor da pessoa." : "A rede continua conectada. Veja a distância média: se subir, a informação passa a dar mais voltas.") + "</p>" +
          '<button class="ona-bt sec peq" data-a="desfazer">Desfazer</button></div>';
      }
      pn.innerHTML = h;
      var b1 = pn.querySelector('[data-a="simular"]'), b2 = pn.querySelector('[data-a="desfazer"]'), b3 = pn.querySelector('[data-a="limpar"]');
      if (b1) b1.onclick = function () { estado.saida = ONA.simularSaida(r, [p.id]); painel(); desenhar(); };
      if (b2) b2.onclick = function () { estado.saida = null; painel(); desenhar(); };
      if (b3) b3.onclick = function () { estado.sel = -1; estado.saida = null; painel(); desenhar(); };
    }

    function tabelaRiscos() {
      var r = estado.res;
      R("riscos").innerHTML = '<tr><th>Pessoa</th><th>Área</th><th class="num">Intermediação</th><th class="num">Sem caminho</th><th class="num">Queda de eficiência</th><th></th></tr>' +
        r.riscos.map(function (x) {
          return '<tr><td class="ona-mono">' + esc(x.id) + "</td><td>" + esc(x.area) + '</td><td class="num">' + num(x.intermediacao, 3) + '</td><td class="num">' + x.perdem_caminho + '</td><td class="num">' + pct(x.queda_eficiencia) + "</td><td>" +
            (r.pessoas <= LIMITE_DESENHO ? '<button class="ona-link" data-sim="' + esc(x.id) + '">simular na rede</button>' : "") + "</td></tr>";
        }).join("");
      R("riscos").querySelectorAll("[data-sim]").forEach(function (b) {
        b.onclick = function () { var i = indicePorId(b.getAttribute("data-sim")); selecionar(i, true); estado.saida = ONA.simularSaida(r, [b.getAttribute("data-sim")]); painel(); desenhar(); };
      });
    }
    function tabelaAreas() {
      var r = estado.res, vis = r.areas.filter(function (a) { return !a.oculta; }), ocultas = r.areas.length - vis.length;
      R("areas-lead").innerHTML = "O índice E-I vai de -1 (só ligações internas) a +1 (só externas). Como toda área conversa mais com o próprio time, a página compara com o E-I esperado se as ligações ignorassem a área (1.000 sorteios das áreas entre as pessoas, mantendo a rede). Só é silo a área com menos de " + pct(ONA.LIMIAR_SILO) + " das ligações externas que teria ao acaso." +
        (ocultas ? " " + ocultas + (ocultas === 1 ? " área tem" : " áreas têm") + " menos de " + ONA.GRUPO_MINIMO + " pessoas e não aparece, para não expor indivíduos." : "");
      R("areas").innerHTML = '<tr><th>Área</th><th class="num">Pessoas</th><th class="num">Resposta</th><th class="num">E-I</th><th class="num">Esperado ao acaso</th><th class="num">Externas vs. acaso</th><th>Leitura</th><th>Porteiro principal</th><th class="num">Na mesma comunidade</th></tr>' +
        vis.sort(function (a, b) { return (a.externo_vs_acaso || 0) - (b.externo_vs_acaso || 0); }).map(function (a) {
          var leitura = a.silo ? '<span class="selo silo">silo</span>' : (a.p_valor !== null && a.p_valor < 0.01 && a.ei < a.ei_esperado ? '<span class="selo">mais fechada que o acaso</span>' : '<span class="selo">como o acaso</span>');
          return "<tr><td>" + esc(a.area) + '</td><td class="num">' + a.pessoas + '</td><td class="num">' + pct(a.taxa_resposta) + (a.taxa_resposta < ONA.LIMIAR_RESPOSTA ? " ⚠" : "") + '</td><td class="num">' + num(a.ei, 2) + '</td><td class="num">' + num(a.ei_esperado, 2) +
            '</td><td class="num">' + (a.externo_vs_acaso === null ? "–" : pct(a.externo_vs_acaso)) + "</td><td>" + leitura + '</td><td><span class="ona-mono">' + esc(a.porteiro_principal || "–") + "</span>" + (a.porteiro_principal ? " · " + pct(a.porteiro_participacao) + " das entradas" : "") +
            '</td><td class="num">' + pct(a.coesao) + "</td></tr>";
        }).join("");
    }
    var DESENHO_PAPEL = {
      coordenador: [0, 0, 0], consultor: [0, 1, 0], representante: [0, 0, 1], porteiro: [1, 0, 0], ligacao: [0, 1, 2]
    };
    var TXT_PAPEL = {
      coordenador: "A, B e C na mesma área. Faz a informação circular dentro do time.",
      consultor: "A e C na mesma área, B de fora. Une duas pessoas de outro time.",
      representante: "A e B na mesma área, C de fora. Leva o que o time sabe para outra área.",
      porteiro: "B e C na mesma área, A de fora. Traz para o time o que vem de fora.",
      ligacao: "A, B e C em três áreas diferentes. Conecta áreas que não se falam."
    };
    function svgPapel(p) {
      var g = DESENHO_PAPEL[p], cores = ["var(--ona-fg)", "var(--ona-accent)", "var(--ona-muted)"];
      var c = function (x, k, l) { return '<circle cx="' + x + '" cy="14" r="7" fill="' + (k === 0 ? "var(--ona-bg)" : cores[k]) + '" stroke="' + cores[k] + '" stroke-width="1.6"/><text x="' + x + '" y="34" font-size="9" text-anchor="middle" fill="currentColor">' + l + "</text>"; };
      return '<svg width="120" height="38" viewBox="0 0 120 38" aria-hidden="true"><path d="M19 14H51M69 14H101" stroke="currentColor" stroke-width="1.4"/><path d="M47 10.5 51 14 47 17.5M97 10.5 101 14 97 17.5" fill="none" stroke="currentColor" stroke-width="1.4"/>' + c(12, g[0], "A") + c(60, g[1], "B") + c(108, g[2], "C") + "</svg>";
    }
    function papeis() {
      var r = estado.res;
      R("papeis").innerHTML = ["porteiro", "representante", "ligacao", "consultor", "coordenador"].map(function (p) {
        var top = r.por_pessoa.filter(function (x) { return x[p] > 0; }).sort(function (a, b) { return b[p] - a[p]; }).slice(0, 3);
        return '<div class="ona-papel">' + svgPapel(p) + "<b>" + PAPEL_CURTO[p] + "</b><p>" + TXT_PAPEL[p] + '</p><span class="ona-mono">' + (top.length ? top.map(function (x) { return esc(x.id) + " (" + x[p] + ")"; }).join("<br>") : "ninguém") + "</span></div>";
      }).join("");
    }
    function sensib() {
      var s = estado.res.sensibilidade; if (!s) { R("sens").innerHTML = ""; return; }
      var d = s.dirigida_vs_simetrizada;
      R("sens").innerHTML = [
        [pct(s.pontes_mantidas), "das 5 maiores pontes continuam no topo", "Média dos sorteios (pior caso: " + pct(s.pontes_mantidas_min) + "). Acima de 60%, as pontes são confiáveis."],
        [pct(s.silo_estavel), "dos sorteios repetem o diagnóstico de silo", "A mesma lista de áreas em silo aparece com menos respostas."],
        [s.isolados_min === s.isolados_max ? String(s.isolados_min) : s.isolados_min + " a " + s.isolados_max, "pessoas fora do fluxo", "Faixa nos sorteios. Se varia muito, isolamento pode ser só falta de resposta."],
        [num(s.ei_variacao_media, 2), "de variação no E-I", "Maior mudança média no E-I de uma área, numa escala de -1 a +1."],
        [pct(d.top5_em_comum), "das 5 maiores pontes iguais nas duas redes", "Comparando a rede simetrizada (padrão) com a dirigida, que só usa o sentido citado."],
        [String(d.nao_respondentes_top10_simetrizada), "não respondentes entre as 10 maiores pontes", "Na rede dirigida seriam " + d.nao_respondentes_top10_dirigida + ": sem citar ninguém, quem não respondeu nunca vira ponte lá."]
      ].map(function (x) { return '<div><div class="n">' + x[0] + "</div><b>" + x[1] + "</b><p>" + x[2] + "</p></div>"; }).join("");
    }
    function tabelaPessoas() {
      var l = estado.res.por_pessoa.slice().sort(function (a, b) { return b.intermediacao - a.intermediacao; });
      R("pessoas").innerHTML = '<tr><th>Pessoa</th><th>Área</th><th>Respondeu</th><th class="num">Citada por</th><th class="num">Citou</th><th class="num">Intermediação</th><th class="num">Restrição</th><th class="num">Tam. efetivo</th><th>Papel</th><th class="num">Grupo</th></tr>' +
        l.map(function (p) {
          return '<tr><td class="ona-mono">' + esc(p.id) + "</td><td>" + esc(p.area) + "</td><td>" + (p.respondeu ? "sim" : "não") + '</td><td class="num">' + p.citacoes_recebidas + '</td><td class="num">' + p.citacoes_feitas +
            '</td><td class="num">' + num(p.intermediacao, 3) + '</td><td class="num">' + num(p.restricao, 2) + '</td><td class="num">' + num(p.tamanho_efetivo, 1) + "</td><td>" + (p.papel ? PAPEL_CURTO[p.papel] : "–") + '</td><td class="num">' + (p.comunidade + 1) + "</td></tr>";
        }).join("");
    }
    function metodo() {
      var r = estado.res;
      R("metodo").innerHTML = [
        "<p><b>Duas redes.</b> Citações recebidas, reciprocidade e papéis de corretagem usam o sentido citado (quem cita quem). Intermediação, comunidades, E-I, restrição de Burt e a simulação de saída usam a rede simetrizada: há ligação se um dos dois citou o outro. Informação corre nos dois sentidos, e assim quem não respondeu não some.</p>",
        "<p><b>Intermediação</b> (Brandes, 2001): fração dos caminhos mais curtos entre outras duas pessoas que passam pela pessoa. De 0 a 1.</p>",
        "<p><b>Comunidades</b>: Louvain (Blondel et al., 2008) rodado " + r.execucoes_louvain + " vezes com sementes diferentes; fica a divisão de maior modularidade. Comunidades com pedaços sem ligação entre si são separadas, a garantia que motivou o Leiden (Traag et al., 2019). Estabilidade = índice de Rand ajustado médio entre as execuções.</p>",
        "<p><b>Índice E-I</b> (Krackhardt e Stern, 1988): (externas − internas) / total, por área. A linha de base embaralha as áreas entre as pessoas 1.000 vezes, mantendo o tamanho de cada área e a rede.</p>",
        "<p><b>Papéis de corretagem</b> (Gould e Fernandez, 1989): coordenador, consultor, representante, porteiro e ligação, usando a área como grupo.</p>",
        "<p><b>Restrição e tamanho efetivo</b> (Burt, 1992 e 2004): restrição baixa = contatos que não se conhecem entre si, ou seja, a pessoa cobre buracos estruturais.</p>",
        "<p><b>E se sair</b>: tira a pessoa e mede quem perde o caminho até a maior parte da rede e a eficiência global (Latora e Marchiori, 2001).</p>",
        "<p><b>Sensibilidade</b>: apaga as citações de mais 10% de quem respondeu, várias vezes, e confere o que muda (ideia de Borgatti, Carley e Krackhardt, 2006).</p>",
        "<p><b>Uso responsável.</b> É um diagnóstico de como a informação circula, não avaliação de desempenho. Resultados por área só aparecem com " + ONA.GRUPO_MINIMO + " pessoas ou mais. Combine o uso com a pesquisa antes de coletar (LGPD: finalidade, transparência e acesso restrito).</p>",
        "<p><b>Reprodutível.</b> Gerador pseudoaleatório com semente fixa (mulberry32, semente " + r.semente + "): o mesmo arquivo dá sempre o mesmo resultado. Código aberto em github.com/gleissonbispo/ona-de-bolso.</p>"
      ].join("");
    }

    var obs = null, mq = null, aoMudarTema = function () { if (estado.res) { legenda(); desenhar(); } };
    var aoRedimensionar = function () { desenhar(); };
    window.addEventListener("resize", aoRedimensionar);
    if (window.MutationObserver) { obs = new MutationObserver(aoMudarTema); obs.observe(document.documentElement, { attributes: true, attributeFilter: ["class", "data-theme", "style"] }); }
    if (window.matchMedia) { mq = window.matchMedia("(prefers-color-scheme: dark)"); if (mq.addEventListener) mq.addEventListener("change", aoMudarTema); }
    atualizarCaixas();
    if (opcoes.abrirExemplo) $('[data-a="exemplo"]').click();

    return {
      destruir: function () { window.removeEventListener("resize", aoRedimensionar); if (obs) obs.disconnect(); if (mq && mq.removeEventListener) mq.removeEventListener("change", aoMudarTema); el.innerHTML = ""; },
      estado: estado,
      carregarExemplo: function () { $('[data-a="exemplo"]').click(); },
      simular: function (id) { var i = indicePorId(id); if (i < 0) return; selecionar(i, false); estado.saida = ONA.simularSaida(estado.res, [id]); painel(); desenhar(); }
    };
  }

  var OnaUI = { montar: montar, lerXLSX: lerXLSX };
  if (typeof module !== "undefined" && module.exports) module.exports = OnaUI;
  else raiz.OnaUI = OnaUI;
})(this);
