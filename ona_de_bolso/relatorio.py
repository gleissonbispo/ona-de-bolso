"""Relatório HTML autocontido (um arquivo, sem internet) para mandar a um gestor."""

from __future__ import annotations

import datetime as _dt
import html
import math

from .insights import num, pct
from .metricas import GRUPO_MINIMO, LIMIAR_RESPOSTA, NOME_PAPEL, Resultado, posicoes

# Paleta das áreas, com o terracota do site primeiro. As 5 primeiras passam no validador de daltonismo
# (separação entre vizinhas); da 6ª em diante a legenda e as tabelas carregam a identidade.
CORES = ["#a65a2e", "#2f6db5", "#d9a31a", "#7b4fb0", "#2e9268", "#5f6b7a", "#c2457a", "#8c7a5b",
         "#4e8a86", "#3f3f3f"]

NIVEL = {"alerta": "Alerta", "risco": "Risco", "atencao": "Atenção", "info": "Informação"}

CSS = """
:root{--bg:#fff;--fg:#0a0a0a;--sub:#525252;--muted:#8a8a8a;--line:#eaeaea;--surface:#fafafa;--accent:#8b5e3c;--accent-subtle:#faf3ee}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-font-smoothing:antialiased}
main{max-width:920px;margin:0 auto;padding:40px 16px 64px}
.eyebrow{font:11px/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}
h1{font-size:34px;font-weight:500;letter-spacing:-.02em;margin:12px 0 6px}
h2{font-size:20px;font-weight:600;margin:40px 0 8px;letter-spacing:-.01em}
p.sub{color:var(--sub);margin:0 0 24px}
.aviso{border:1px solid var(--line);border-left:3px solid var(--accent);background:var(--accent-subtle);padding:12px 16px;border-radius:8px;margin:16px 0}
.numeros{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:16px 0}
.num{border:1px solid var(--line);border-radius:10px;padding:14px 16px;background:var(--surface)}
.num b{display:block;font-size:26px;font-weight:500;letter-spacing:-.02em}
.num span{color:var(--sub);font-size:13px}
.insight{border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:10px 0}
.insight .tag{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.insight.risco .tag,.insight.alerta .tag{color:var(--accent);font-weight:600}
.insight h3{font-size:16px;margin:4px 0 6px;font-weight:600}
.insight p{margin:0;color:var(--sub)}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin:8px 0}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-weight:600;color:var(--sub)}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.legenda{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px;color:var(--sub);margin:6px 0}
.legenda i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:-1px}
svg{width:100%;height:auto;border:1px solid var(--line);border-radius:10px;background:var(--surface)}
footer{color:var(--muted);font-size:12.5px;margin-top:48px;border-top:1px solid var(--line);padding-top:16px}
ul{padding-left:20px}li{margin:4px 0}
@media print{main{padding:0}.insight,.num{break-inside:avoid}}
"""


def _e(x: object) -> str:
    return html.escape("" if x is None else str(x))


def _svg_rede(r: Resultado, cor_area: dict[str, str]) -> str:
    pos = posicoes(r)
    if not pos:
        return ""
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    lx, ly = max(xs) - min(xs) or 1, max(ys) - min(ys) or 1
    w, h, m = 880, 560, 24

    def xy(pid: str) -> tuple[float, float]:
        x, y = pos[pid]
        return m + (x - min(xs)) / lx * (w - 2 * m), m + (y - min(ys)) / ly * (h - 2 * m)

    g = r.rede
    linhas = []
    for i in range(g.n):
        for j in g.adj_s[i]:
            if j > i:
                (x1, y1), (x2, y2) = xy(g.nos[i]["id"]), xy(g.nos[j]["id"])
                linhas.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    maxb = max((p["intermediacao"] for p in r["por_pessoa"]), default=0) or 1
    pontos = []
    for p in r["por_pessoa"]:
        x, y = xy(p["id"])
        raio = 3.2 + 7 * math.sqrt(p["intermediacao"] / maxb)
        pontos.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{raio:.1f}" fill="{cor_area.get(p["area"], "#888")}">'
                      f'<title>{_e(p["id"])} · {_e(p["area"])}</title></circle>')
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Desenho da rede, cada ponto é uma pessoa colorida pela área">'
            f'<g stroke="#bdbdbd" stroke-opacity=".45" stroke-width=".7">{"".join(linhas)}</g>'
            f'<g stroke="#fff" stroke-width="1">{"".join(pontos)}</g></svg>')


def gerar_html(r: Resultado, titulo: str = "Rede de colaboração", fonte: str = "", incluir_pessoas: bool = False) -> str:
    """Monta o relatório. ``incluir_pessoas`` acrescenta a tabela por pessoa (fica fora por padrão)."""
    conf = r["confiabilidade"]
    s = r.get("sensibilidade")
    areas_nomes = [a["area"] for a in r["areas"]]
    cor_area = {a: CORES[k % len(CORES)] for k, a in enumerate(areas_nomes)}
    hoje = _dt.date.today().strftime("%d/%m/%Y")
    partes: list[str] = []
    add = partes.append

    add(f'<main><span class="eyebrow">ONA de bolso · People Analytics</span><h1>{_e(titulo)}</h1>')
    add(f'<p class="sub">Relatório gerado em {hoje}{" a partir de " + _e(fonte) if fonte else ""}. '
        f'{r["pessoas"]} pessoas, {r["ligacoes"]} pares ligados, '
        f'{"rede simetrizada" if r["rede"] == "simetrizada" else "rede dirigida"}'
        f'{", pergunta " + _e(r["tipo"]) if r["tipo"] != "todos" else ""}.</p>')

    if conf["nivel"] == "insuficiente":
        add(f'<div class="aviso"><b>Dados insuficientes.</b> Menos de {pct(LIMIAR_RESPOSTA)} das pessoas responderam. '
            'O relatório não conclui sobre pontes, isolados, buracos estruturais nem dependência.</div>')
    elif conf["nivel"] == "cautela":
        add(f'<div class="aviso"><b>Leia com cautela.</b> Motivo: {_e("; ".join(conf["motivos"]))}.</div>')

    add('<div class="numeros">')
    for valor, rotulo in [
        (f'{pct(r["taxa_resposta"])}', f'responderam ({r["responderam"]} de {r["pessoas"]})'),
        (f'{r["comunidades"]}', f'grupos reais de conversa (modularidade {num(r["modularidade"], 2)})'),
        (f'{num(r["eficiencia"], 2)}', "eficiência global (0 a 1)"),
        (f'{num(r["distancia_media"], 1)}', "passos, em média, entre duas pessoas"),
        (f'{pct(r["reciprocidade"])}', "das citações são recíprocas"),
    ]:
        add(f'<div class="num"><b>{valor}</b><span>{_e(rotulo)}</span></div>')
    add("</div>")

    add('<h2>O que a rede mostra</h2><p class="sub">Do mais importante para o menos. Diagnóstico de rede, não avaliação de pessoa.</p>')
    for i in r["insights"]:
        add(f'<div class="insight {i["nivel"]}"><span class="tag">{NIVEL[i["nivel"]]}</span>'
            f'<h3>{_e(i["titulo"])}</h3><p>{_e(i["texto"])}</p></div>')

    svg = _svg_rede(r, cor_area)
    if svg:
        add('<h2>A rede</h2><p class="sub">Cada ponto é uma pessoa, colorida pela área; o tamanho cresce com a intermediação. '
            'Cada linha é uma ligação citada em qualquer sentido.</p>')
        add('<div class="legenda">' + "".join(f'<span><i style="background:{c}"></i>{_e(a)}</span>' for a, c in cor_area.items()) + "</div>")
        add(svg)

    add('<h2>Áreas</h2><p class="sub">E-I vai de -1 (só ligações internas) a +1 (só externas). O esperado vem de 1.000 '
        f'embaralhamentos das áreas. Áreas com menos de {GRUPO_MINIMO} pessoas não aparecem.</p>')
    add('<table><tr><th>Área</th><th class="n">Pessoas</th><th class="n">Resposta</th><th class="n">E-I</th>'
        '<th class="n">E-I esperado</th><th class="n">Externas vs. acaso</th><th>Silo</th><th>Porteiro principal</th></tr>')
    for a in r["areas"]:
        if a["oculta"]:
            add(f'<tr><td>{_e(a["area"])}</td><td colspan="7">menos de {GRUPO_MINIMO} pessoas: resultado escondido</td></tr>')
            continue
        port = f'{_e(a["porteiro_principal"])} ({pct(a["porteiro_participacao"])})' if a["porteiro_principal"] else "–"
        add(f'<tr><td>{_e(a["area"])}</td><td class="n">{a["pessoas"]}</td><td class="n">{pct(a["taxa_resposta"])}</td>'
            f'<td class="n">{num(a["ei"], 2) if a["ei"] is not None else "–"}</td>'
            f'<td class="n">{num(a["ei_esperado"], 2) if a["ei_esperado"] is not None else "–"}</td>'
            f'<td class="n">{pct(a["externo_vs_acaso"]) if a["externo_vs_acaso"] is not None else "–"}</td>'
            f'<td>{"sim" if a["silo"] else "não"}</td><td>{port}</td></tr>')
    add("</table>")

    if conf["nivel"] != "insuficiente" and r["riscos"]:
        add('<h2>E se essa pessoa sair?</h2><p class="sub">As pessoas com maior intermediação, tiradas uma de cada vez.</p>')
        add('<table><tr><th>Pessoa</th><th>Área</th><th class="n">Ficam sem caminho</th><th class="n">Queda da eficiência</th></tr>')
        for x in r["riscos"]:
            add(f'<tr><td>{_e(x["id"])}</td><td>{_e(x["area"])}</td><td class="n">{x["perdem_caminho"]}</td>'
                f'<td class="n">{pct(x["queda_eficiencia"])}</td></tr>')
        add("</table>")

    if s:
        d = s["dirigida_vs_simetrizada"]
        add('<h2>Quanto o resultado aguenta menos dados</h2><ul>'
            f'<li>Em {s["replicas"]} sorteios, apagando as citações de mais {s["pessoas_retiradas"]} pessoas, '
            f'{pct(s["pontes_mantidas"])} das cinco maiores pontes continuaram no topo (mínimo {pct(s["pontes_mantidas_min"])}).</li>'
            f'<li>O diagnóstico de silo se repetiu em {pct(s["silo_estavel"])} dos sorteios; isolados variaram de '
            f'{s["isolados_min"]} a {s["isolados_max"]}.</li>'
            f'<li>Rede dirigida x simetrizada: {pct(d["top5_em_comum"])} das cinco maiores pontes em comum; '
            f'correlação de Spearman de {num(d["correlacao"], 2)} entre as intermediações.</li></ul>')

    if incluir_pessoas:
        add('<h2>Por pessoa</h2><p class="sub">Uso restrito. Nenhuma métrica daqui deve entrar em avaliação, promoção ou desligamento.</p>')
        add('<table><tr><th>Pessoa</th><th>Área</th><th class="n">Citações recebidas</th><th class="n">Intermediação</th>'
            '<th class="n">Restrição</th><th>Papel</th></tr>')
        for p in sorted(r["por_pessoa"], key=lambda p: -p["intermediacao"]):
            add(f'<tr><td>{_e(p["id"])}</td><td>{_e(p["area"])}</td><td class="n">{p["citacoes_recebidas"]}</td>'
                f'<td class="n">{num(p["intermediacao"], 3)}</td>'
                f'<td class="n">{num(p["restricao"], 2) if p["restricao"] is not None else "–"}</td>'
                f'<td>{_e(NOME_PAPEL.get(p["papel"] or "", "–"))}</td></tr>')
        add("</table>")

    add('<h2>Como ler e cuidados</h2><ul>'
        '<li>O questionário mede a percepção de quem respondeu, num momento. Não é registro de interação.</li>'
        '<li>Intermediação alta não é desempenho alto; isolamento não é problema de comportamento. Os números '
        'servem para discutir como o trabalho circula, não para avaliar pessoas.</li>'
        f'<li>Resultados por área só aparecem com {GRUPO_MINIMO} pessoas ou mais. Use códigos no lugar de nomes.</li>'
        '<li>Silo = E-I abaixo do esperado ao acaso com p &lt; 0,01 e menos de 25% das ligações externas esperadas.</li></ul>')
    add('<footer>ONA de bolso · github.com/gleissonbispo/ona-de-bolso · Métodos: Brandes (2001), Blondel et al. (2008), '
        'Krackhardt e Stern (1988), Gould e Fernandez (1989), Burt (1992), Latora e Marchiori (2001).</footer></main>')

    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{_e(titulo)} · ONA de bolso</title><style>{CSS}</style></head><body>{"".join(partes)}</body></html>')
