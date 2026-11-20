"""Monta demo/index.html: o app Streamlit rodando no navegador com stlite (Pyodide).

A página carrega o @stlite/browser numa versão fixa pelo jsDelivr e monta o mesmo app/app.py e o
mesmo pacote ona_de_bolso/ deste repositório, com a base de exemplo. Os arquivos vão embutidos no
HTML, então dá para servir a página de qualquer lugar (o site copia este arquivo para public/).

    python scripts/montar_demo.py            # grava demo/index.html
"""

from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
STLITE = "1.12.2"  # Pyodide 314.0.3 (Python 3.14), Streamlit 1.65, networkx 3.6.1, pandas 3.0.2
PYODIDE = "314.0.3"
# networkx pelo arquivo do próprio Pyodide: pelo nome, o Pyodide traria o matplotlib junto (7 MB a mais).
REQUISITOS = [f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE}/full/networkx-3.6.1-py3-none-any.whl"]

# Só valores simples: o stlite recusa listas aqui (as cores dos gráficos o app já define).
TEMA = {
    "theme.base": "light",
    "theme.primaryColor": "#8b5e3c",
    "theme.backgroundColor": "#ffffff",
    "theme.secondaryBackgroundColor": "#faf7f4",
    "theme.textColor": "#0a0a0a",
    "theme.borderColor": "#eaeaea",
    # Com "Inter:<url>" o stlite 1.12.2 quebra (erro do Helmet ao injetar a fonte); a página já carrega a Inter.
    "theme.font": "Inter, sans-serif",
    "theme.baseRadius": "0.6rem",
    "client.toolbarMode": "viewer",
}

MODELO = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ONA de bolso · demonstração</title>
<meta name="description" content="O app Streamlit da ONA de bolso rodando no navegador com Pyodide. Nada sai do navegador.">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@stlite/browser@__STLITE__/build/stlite.css">
<style>
  html,body{margin:0;background:#fff;color:#0a0a0a;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
  #carregando{position:fixed;inset:0;z-index:1000;background:#fff;display:flex;align-items:center;justify-content:center;padding:24px;transition:opacity .4s}
  #carregando.saiu{opacity:0;pointer-events:none}
  .caixa{max-width:420px;text-align:center}
  .caixa .eyebrow{font:11px/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.14em;text-transform:uppercase;color:#8b5e3c}
  .caixa h1{font-size:22px;font-weight:500;letter-spacing:-.01em;margin:14px 0 8px}
  .caixa p{color:#525252;font-size:14.5px;line-height:1.55;margin:6px 0}
  .caixa .etapa{color:#8a8a8a;font-size:13px;margin-top:14px;min-height:20px}
  .barra{height:3px;background:#eee;border-radius:3px;overflow:hidden;margin:18px auto 0;width:220px}
  .barra i{display:block;height:100%;width:35%;background:#8b5e3c;border-radius:3px;animation:vai 1.4s ease-in-out infinite}
  @keyframes vai{0%{transform:translateX(-110%)}100%{transform:translateX(320%)}}
  .privacidade{position:fixed;left:0;right:0;bottom:0;z-index:999;font-size:12px;color:#6b6b6b;background:rgba(255,255,255,.92);
    border-top:1px solid #eee;padding:6px 16px;text-align:center}
  @media (max-width:640px){.privacidade{display:none}}
  .embutida .privacidade{display:none}
</style>
</head>
<body>
<div id="carregando" role="status" aria-live="polite">
  <div class="caixa">
    <span class="eyebrow">ONA de bolso · demonstração</span>
    <h1>Carregando o Python no seu navegador</h1>
    <p>Leva uns segundos na primeira vez: o navegador baixa o Python (Pyodide), o Streamlit, o pandas e o networkx. Depois fica em cache.</p>
    <p>Nada sai do seu navegador. As planilhas que você subir são lidas e calculadas aqui mesmo.</p>
    <div class="barra"><i></i></div>
    <div class="etapa" id="etapa"></div>
  </div>
</div>
<div id="root"></div>
<div class="privacidade">Roda inteiro no seu navegador (Pyodide + stlite). Nenhuma planilha é enviada a servidor.</div>
<script type="module">
import { mount } from "https://cdn.jsdelivr.net/npm/@stlite/browser@__STLITE__/build/stlite.js";
const ARQUIVOS = __ARQUIVOS__;
if (window.self !== window.top) document.body.classList.add("embutida"); // no site, a nota fica fora do iframe
const inicio = performance.now();
window.__onaDemo = { inicio, pronto: null };
const etapas = ["Baixando o Python...", "Instalando Streamlit, pandas e networkx...", "Abrindo o app..."];
let k = 0;
const etapa = document.getElementById("etapa");
const tick = setInterval(() => { etapa.textContent = etapas[Math.min(k++, etapas.length - 1)]; }, 6000);
etapa.textContent = etapas[0];
mount({
  entrypoint: "app/app.py",
  files: ARQUIVOS,
  requirements: __REQUISITOS__,
  streamlitConfig: __TEMA__,
  disableProgressToasts: true,
}, document.getElementById("root"));
const vigia = setInterval(() => {
  if (document.querySelector('[data-testid="stAppViewContainer"] h1')) {
    clearInterval(vigia); clearInterval(tick);
    window.__onaDemo.pronto = performance.now() - inicio;
    document.getElementById("carregando").classList.add("saiu");
    setTimeout(() => document.getElementById("carregando").remove(), 600);
  }
}, 400);
</script>
</body>
</html>
"""


def arquivos() -> dict[str, str]:
    out: dict[str, str] = {"app/app.py": (RAIZ / "app" / "app.py").read_text(encoding="utf-8")}
    pacote = RAIZ / "ona_de_bolso"
    for f in sorted(pacote.rglob("*")):
        if f.suffix in {".py", ".csv", ".json"} and "__pycache__" not in f.parts and f.name != "__main__.py" and f.name != "cli.py":
            out[f.relative_to(RAIZ).as_posix()] = f.read_text(encoding="utf-8")
    return out


def montar(destino: Path | None = None) -> Path:
    destino = destino or RAIZ / "demo" / "index.html"
    html = (MODELO.replace("__STLITE__", STLITE)
            .replace("__ARQUIVOS__", json.dumps(arquivos(), ensure_ascii=False).replace("</", "<\\/"))
            .replace("__REQUISITOS__", json.dumps(REQUISITOS))
            .replace("__TEMA__", json.dumps(TEMA, ensure_ascii=False)))
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    return destino


if __name__ == "__main__":
    d = montar()
    print(f"ok: {d.relative_to(RAIZ)} ({d.stat().st_size // 1024} KB), stlite {STLITE}")
