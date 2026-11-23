"""Relatório HTML autocontido (um arquivo, sem internet) para mandar a um gestor."""

from __future__ import annotations

import datetime as _dt
import html
import math

from .insights import lista, num, pct
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


# ------------------------------------------------------------------ resumo para o gestor

CSS_GESTOR = """
:root{--fg:#0a0a0a;--sub:#525252;--muted:#6b6b6b;--line:#eaeaea;--surface:#fafafa;--accent:#8b5e3c;--accent-subtle:#faf3ee}
*{box-sizing:border-box}
body{margin:0;background:#fff;color:var(--fg);font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-font-smoothing:antialiased}
main{max-width:760px;margin:0 auto;padding:40px 16px 56px}
h1{font-size:28px;font-weight:600;letter-spacing:-.02em;margin:0 0 6px;line-height:1.2}
h2{font-size:17px;font-weight:600;margin:32px 0 10px;letter-spacing:-.01em}
p.sub{color:var(--sub);margin:0 0 4px}
.leitura{color:var(--sub);font-size:14px;margin:10px 0 0}
.leitura b{color:var(--fg);font-weight:600}
.perguntas{display:grid;gap:10px;margin:16px 0 0}
.pergunta{border:1px solid var(--line);border-radius:12px;padding:14px 16px;display:grid;grid-template-columns:7.5rem 1fr;gap:4px 16px;align-items:baseline}
.pergunta .q{color:var(--sub);font-size:13.5px;grid-column:1/-1}
.pergunta .r{font-weight:600;font-size:17px;letter-spacing:-.01em}
.pergunta.sim .r{color:var(--accent)}
.pergunta .d{color:var(--fg)}
ol{padding-left:22px;margin:0}
ol li{margin:8px 0;padding-left:4px}
ol li b{font-weight:600}
ul.acoes{list-style:none;padding:0;margin:0}
ul.acoes li{border-left:3px solid var(--accent);background:var(--accent-subtle);padding:10px 14px;border-radius:0 8px 8px 0;margin:8px 0}
p.limites{color:var(--muted);font-size:13px;border-top:1px solid var(--line);padding-top:14px;margin-top:32px}
@media (max-width:560px){.pergunta{grid-template-columns:1fr}}
@media print{main{padding:0}body{font-size:13.5px}.pergunta,li{break-inside:avoid}}
"""


def _pergunta(q: str, resposta: str, detalhe: str, alerta: bool) -> str:
    return (f'<div class="pergunta{" sim" if alerta else ""}"><span class="q">{_e(q)}</span>'
            f'<span class="r">{_e(resposta)}</span><span class="d">{detalhe}</span></div>')


def resumo_gestor(r: Resultado) -> dict:
    """As três perguntas, os achados principais e o que fazer, em linguagem de gestor.

    Usa só o que o relatório completo já mostra (mesmos critérios e mesmos números); muda a forma.
    """
    conf = r["confiabilidade"]
    pode = conf["nivel"] != "insuficiente"
    silos = [a for a in r["areas"] if a["silo"]]
    corte = [x for x in r["riscos"] if x["perdem_caminho"] >= max(3, 0.03 * r["pessoas"])]
    gestores_fora = [g for g in r["gestores"] if g["time"] >= GRUPO_MINIMO and g["fracao"] < 0.2]
    gestores_ok = [g for g in r["gestores"] if g["time"] >= GRUPO_MINIMO]

    perguntas = []
    if silos:
        a = silos[0]
        det = (f'{_e(lista([s["area"] for s in silos]))}: {"a área tem" if len(silos) == 1 else "a primeira tem"} só '
               f'{pct(a["externo_vs_acaso"])} das conversas com outras áreas que se esperaria pelo tamanho dela.')
        if a["porteiro_principal"] and a["porteiro_participacao"] >= 0.5:
            det += f' E o que chega de fora passa quase todo por uma pessoa ({_e(a["porteiro_principal"])}).'
        if not pode:
            det += " Com tão pouca resposta, confirme numa nova rodada antes de agir."
        perguntas.append(("Alguma área virou silo?", "Sim", det, True))
    else:
        perguntas.append(("Alguma área virou silo?", "Não",
                          "Toda área conversa mais com o próprio time, e isso é normal. Nenhuma está muito abaixo das outras.", False))
    if not pode:
        perguntas.append(("A rede depende de alguém? E se essa pessoa sair?", "Não dá para dizer",
                          f'Só {pct(r["taxa_resposta"])} responderam. Abaixo de {pct(LIMIAR_RESPOSTA)}, a análise não conclui sobre pontes.', False))
    elif corte:
        x = corte[0]
        det = (f'Sem {_e(x["id"])} ({_e(x["area"])}), {x["perdem_caminho"]} pessoas ficam sem nenhum caminho de conversa '
               f'com o resto da empresa, e a rede fica {pct(x["queda_eficiencia"])} menos eficiente.')
        if len(corte) > 1:
            det += f' {_e(corte[1]["id"])} também é ponto único de falha ({corte[1]["perdem_caminho"]} pessoas).'
        perguntas.append(("A rede depende de alguém? E se essa pessoa sair?", "Sim", det, True))
    else:
        top = max(r["riscos"], key=lambda x: x["queda_eficiencia"]) if r["riscos"] else None
        det = "Nenhuma saída isolada deixa um grupo sem caminho até o resto."
        if top:
            det += f' A maior perda é de {pct(top["queda_eficiencia"])} na eficiência da rede.'
        perguntas.append(("A rede depende de alguém? E se essa pessoa sair?", "Não", det, False))
    if gestores_fora:
        g = gestores_fora[0]
        com = (f'não tem ligação direta com nenhuma das {g["time"]} pessoas' if g["ligados"] == 0
               else f'tem ligação direta com só {g["ligados"]} de {g["time"]} pessoas')
        det = (f'O gestor de {_e(g["area"])} ({_e(g["gestor"])}) {com} do time.'
               + (f' Há mais {len(gestores_fora) - 1} na mesma situação.' if len(gestores_fora) > 1 else ""))
        perguntas.append(("Os gestores estão no fluxo do time?", "Nem todos", det, True))
    elif gestores_ok:
        perguntas.append(("Os gestores estão no fluxo do time?", "Sim",
                          f"Todos os gestores com time de {GRUPO_MINIMO} pessoas ou mais têm ligação direta com pelo menos 20% do time.", False))
    else:
        perguntas.append(("Os gestores estão no fluxo do time?", "Sem dado",
                          f"A tabela de pessoas não tem gestor com time de {GRUPO_MINIMO} pessoas ou mais (coluna gestor_id).", False))

    achados: list[str] = []
    acoes: list[str] = []
    if not pode:
        achados.append(f'<b>A participação foi baixa.</b> {r["responderam"]} de {r["pessoas"]} pessoas responderam '
                       f'({pct(r["taxa_resposta"])}). Com isso, quem parece ponte ou isolado pode ser só falta de dado.')
        acoes.append(f'Rodar o questionário de novo, com prazo de uma a duas semanas e lembrete dos gestores, até passar de {pct(LIMIAR_RESPOSTA)}.')
    for x in corte[:2] if pode else []:
        achados.append(f'<b>Ponto único de falha em {_e(x["area"])}.</b> Sem {_e(x["id"])}, {x["perdem_caminho"]} pessoas perdem '
                       "o único caminho até as outras áreas. O problema é a rede depender de uma pessoa, não a pessoa.")
        acoes.append(f'Criar um segundo canal entre {_e(x["area"])} e as outras áreas: um par de backup para {_e(x["id"])} e um '
                     "ritual fixo entre as áreas que mais dependem dessa ponte.")
    for a in silos:
        outras = [b["externo_vs_acaso"] for b in r["areas"] if not b["oculta"] and not b["silo"] and b["externo_vs_acaso"] is not None]
        achados.append(f'<b>{_e(a["area"])} fala quase só para dentro.</b> A área tem {pct(a["externo_vs_acaso"])} das conversas '
                       "com outras áreas que se esperaria pelo tamanho dela"
                       + (f'; as demais ficam entre {pct(min(outras))} e {pct(max(outras))}.' if outras else "."))
        acoes.append(f'Perguntar ao gestor de {_e(a["area"])} se o isolamento é escolha (trabalho que pede foco) ou gargalo. '
                     "Se for gargalo, pôr mais gente do time em contato direto com as áreas parceiras.")
    for g in gestores_fora:
        quantos = (f'Nenhuma das {g["time"]} pessoas do time tem' if g["ligados"] == 0
                   else f'Só {g["ligados"]} de {g["time"]} pessoas do time têm')
        achados.append(f'<b>Gestor de {_e(g["area"])} fora do fluxo.</b> {quantos} ligação direta com o gestor. '
                       "A informação do time está passando por outro caminho.")
        acoes.append(f'Entender com o gestor de {_e(g["area"])} por onde a informação do time circula e rever os rituais '
                     "(conversas individuais, reunião de time).")
    for a in r["areas"]:
        if (pode and not a["oculta"] and not a["silo"] and a["porteiro_principal"] and a["porteiro_participacao"] >= 0.5
                and a["entradas_de_fora"] >= 10):
            achados.append(f'<b>Em {_e(a["area"])}, a informação de fora entra por uma pessoa.</b> {_e(a["porteiro_principal"])} '
                           f'aparece em {pct(a["porteiro_participacao"])} das entradas.')
            acoes.append(f'Abrir contato direto entre mais gente de {_e(a["area"])} e as áreas parceiras.')
    if pode and r["pontes"]:
        p3 = [p["id"] for p in r["pontes"][:3]]
        achados.append(f'<b>As maiores pontes entre áreas são {_e(lista(p3))}.</b> Estão no caminho mais curto entre muitos '
                       "colegas. Isso é posição na rede, não desempenho.")
        acoes.append(f"Saber o que passa por {_e(lista(p3))} e quem assumiria se uma delas sair ou mudar de função.")
    if pode and r["isolados"]:
        achados.append(f'<b>{len(r["isolados"])} pessoas fora do fluxo.</b> Ninguém as citou. Pode ser pessoa nova, afastada, '
                       "remota ou que não respondeu.")
        acoes.append("Antes de concluir qualquer coisa sobre quem está fora do fluxo, conversar com o gestor de cada uma.")

    limites = (f'Base: {r["responderam"]} de {r["pessoas"]} pessoas responderam ({pct(r["taxa_resposta"])}), '
               "num questionário de percepção feito num momento. Mostra como a informação circula, não o desempenho de "
               "ninguém, e não deve entrar em avaliação, promoção ou desligamento.")
    return {"perguntas": perguntas, "achados": achados[:5], "acoes": acoes[:4], "limites": limites,
            "leitura": {"boa": "leitura estável", "cautela": "leia com cautela", "insuficiente": "dados insuficientes"}[conf["nivel"]],
            "motivos": conf["motivos"]}


def gerar_html_gestor(r: Resultado, titulo: str = "Rede de colaboração", fonte: str = "") -> str:
    """Resumo de uma página para o gestor: as três perguntas, os achados, o que fazer e os limites.

    Não traz desenho, tabela técnica nem números por pessoa além de quem é ponto de dependência.
    """
    s = resumo_gestor(r)
    hoje = _dt.date.today().strftime("%d/%m/%Y")
    partes = [f"<main><h1>{_e(titulo)}: resumo para o gestor</h1>",
              f'<p class="sub">{r["pessoas"]} pessoas{" · " + _e(fonte) if fonte else ""} · {hoje}</p>',
              f'<p class="leitura"><b>{pct(r["taxa_resposta"])} responderam: {_e(s["leitura"])}.</b>'
              + (f' Motivo: {_e("; ".join(s["motivos"]))}.' if s["motivos"] and s["leitura"] != "leitura estável" else "") + "</p>",
              '<h2>As três perguntas</h2><div class="perguntas">']
    partes += [_pergunta(*p) for p in s["perguntas"]]
    partes.append("</div>")
    if s["achados"]:
        partes.append("<h2>O que a rede mostra</h2><ol>" + "".join(f"<li>{a}</li>" for a in s["achados"]) + "</ol>")
    if s["acoes"]:
        partes.append('<h2>O que fazer</h2><ul class="acoes">' + "".join(f"<li>{a}</li>" for a in s["acoes"]) + "</ul>")
    partes.append(f'<p class="limites">{_e(s["limites"])} Detalhes e método no relatório completo.</p></main>')
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{_e(titulo)} · resumo para o gestor</title><style>{CSS_GESTOR}</style></head><body>{"".join(partes)}</body></html>')
