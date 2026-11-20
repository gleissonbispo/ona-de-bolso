"""App Streamlit da ONA de bolso.

    streamlit run app/app.py

O mesmo arquivo roda no navegador com stlite (Pyodide) na demonstração do site: nada é enviado a
servidor, as contas acontecem no computador de quem usa.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import ona_de_bolso as ona
except ModuleNotFoundError:  # rodando do repositório sem instalar o pacote
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import ona_de_bolso as ona

import altair as alt
import pandas as pd
import streamlit as st

from ona_de_bolso import io as oio
from ona_de_bolso.insights import num, pct
from ona_de_bolso.metricas import GRUPO_MINIMO, LIMITE_DESENHO, NOME_PAPEL
from ona_de_bolso.relatorio import CORES, gerar_html

st.set_page_config(page_title="ONA de bolso", page_icon=":material/hub:", layout="wide", initial_sidebar_state="collapsed")

st.html("""<style>
.block-container{padding-top:2.2rem;max-width:1180px}
.ona-eyebrow{font:11px/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.14em;text-transform:uppercase;color:#8b5e3c}
.ona-sub{color:#525252;font-size:1.05rem;max-width:44rem;margin:.2rem 0 1rem}
.ona-tag{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#8a8a8a}
.ona-tag.forte{color:#8b5e3c;font-weight:600}
.ona-nota{color:#6b6b6b;font-size:.88rem}
div[data-testid="stMetricValue"]{font-weight:500;letter-spacing:-.02em}
</style>""")

NIVEL = {"alerta": ("Alerta", True), "risco": ("Risco", True), "atencao": ("Atenção", False), "info": ("Informação", False)}
COR_PAPEL = {"porteiro": "#a65a2e", "representante": "#2f6db5", "ligação": "#d9a31a", "consultor": "#7b4fb0",
             "coordenador": "#2e9268", "sem papel": "#d4d4d4"}


# ------------------------------------------------------------------ dados


@st.cache_resource(show_spinner=False, max_entries=6)
def analisar(pessoas: pd.DataFrame, ligacoes: pd.DataFrame, tipo: str, rede: str) -> ona.Resultado:
    return ona.analisar(pessoas, ligacoes, tipo=tipo, rede=rede)


@st.cache_resource(show_spinner=False, max_entries=6)
def layout(_r: ona.Resultado, chave: str) -> dict | None:
    return ona.posicoes(_r)


@st.cache_data(show_spinner=False)
def relatorio_html(_r: ona.Resultado, chave: str, fonte: str) -> bytes:
    return gerar_html(_r, fonte=fonte).encode("utf-8")


def cabecalho() -> None:
    st.html('<span class="ona-eyebrow">People Analytics · ONA</span>')
    st.title("ONA de bolso")
    st.html('<p class="ona-sub">Suba a tabela de pessoas e a de ligações do seu questionário de rede e veja como a '
            "informação circula: quem conecta as áreas, onde há silo de verdade e o que acontece se alguém sair.</p>")


def entrada() -> None:
    carregado = "dados" in st.session_state
    with st.expander("Trocar os dados" if carregado else "Dados", expanded=not carregado):
        c1, c2 = st.columns([3, 2], gap="large")
        with c1:
            arquivos = st.file_uploader(
                "Duas planilhas (pessoas e ligações) ou um Excel com as duas abas", type=["csv", "xlsx"],
                accept_multiple_files=True, help="pessoas: id, area, cargo, gestor_id, unidade, respondeu. "
                "ligações: origem_id, destino_id, tipo, peso (quem respondeu cita quem).")
            if arquivos:
                assinatura = tuple((f.name, f.size) for f in arquivos)
                if st.session_state.get("assinatura") != assinatura:
                    ent = oio.ler_entrada([(f.name, f.getvalue()) for f in arquivos])
                    st.session_state["assinatura"] = assinatura
                    if ent.completa:
                        st.session_state["dados"] = (ent.pessoas, ent.ligacoes, " + ".join(ent.nomes.values()))
                        st.session_state.pop("pessoa_sel", None)
                        st.rerun()
                    else:
                        falta = "pessoas (coluna id)" if ent.pessoas is None else "ligações (colunas origem_id e destino_id)"
                        st.error(f"Falta a tabela de {falta}. Suba as duas de uma vez, ou um Excel com as duas abas.")
        with c2:
            st.write("Sem dados à mão? A base de exemplo é uma organização fictícia de 114 pessoas com um silo, um "
                     "ponto único de falha e 20% de não resposta plantados de propósito.")
            if st.button("Usar a base de exemplo", type="primary", icon=":material/play_arrow:"):
                p, l = ona.exemplo()
                st.session_state["dados"] = (p, l, "base de exemplo (sintética)")
                st.session_state.pop("assinatura", None)
                st.session_state.pop("pessoa_sel", None)
                st.rerun()
            st.caption("Modelos de planilha")
            m1, m2 = st.columns(2)
            m1.download_button("pessoas.csv", oio.para_csv(oio.modelo_pessoas()), "pessoas.csv", "text/csv",
                               icon=":material/download:", on_click="ignore")
            m2.download_button("ligacoes.csv", oio.para_csv(oio.modelo_ligacoes()), "ligacoes.csv", "text/csv",
                               icon=":material/download:", on_click="ignore")


# ------------------------------------------------------------------ rede (Altair)


def cores_por(r: ona.Resultado, modo: str) -> tuple[pd.Series, list[str], list[str]]:
    df = r.pessoas_df()
    if modo == "área":
        dom = [a["area"] for a in r["areas"]]
        return df["area"], dom, [CORES[i % len(CORES)] for i in range(len(dom))]
    if modo == "comunidade":
        tam = df["comunidade"].value_counts()
        rot = df["comunidade"].map(lambda c: f"grupo {c + 1}" if tam[c] > 1 else "sozinho")
        dom = [f"grupo {c + 1}" for c in sorted(c for c in tam.index if tam[c] > 1)] + (["sozinho"] if (tam == 1).any() else [])
        return rot, dom, [CORES[i % len(CORES)] if d != "sozinho" else "#d4d4d4" for i, d in enumerate(dom)]
    rot = df["papel"].map(lambda p: NOME_PAPEL.get(p, "sem papel") if p else "sem papel")
    dom = [p for p in COR_PAPEL if p in set(rot)]
    return rot, dom, [COR_PAPEL[p] for p in dom]


def grafico_rede(r: ona.Resultado, pos: dict, modo: str, areas: list[str], foco: str | None = None,
                 removidos: list[str] | None = None, perdem: list[str] | None = None, selecionavel: bool = True,
                 altura: int = 560) -> alt.LayerChart:
    df = r.pessoas_df()
    df["x"] = df["id"].map(lambda i: pos[i][0])
    df["y"] = df["id"].map(lambda i: pos[i][1])
    df["cor"], dom, rng = cores_por(r, modo)
    df["papel_txt"] = df["papel"].map(lambda p: NOME_PAPEL.get(p, "–") if p else "–")
    df["intermed"] = df["intermediacao"].round(3)
    df = df[df["area"].isin(areas)]
    visiveis = set(df["id"])
    g = r.rede
    vizinhos = set()
    if foco and foco in g.idx:
        vizinhos = {g.nos[j]["id"] for j in g.adj_s[g.idx[foco]]} | {foco}
    removidos, perdem = set(removidos or []), set(perdem or [])
    arestas = []
    for i in range(g.n):
        a = g.nos[i]["id"]
        for j in g.adj_s[i]:
            b = g.nos[j]["id"]
            if j > i and a in visiveis and b in visiveis:
                destaque = foco is not None and foco in (a, b)
                some = a in removidos or b in removidos
                arestas.append({"x": pos[a][0], "y": pos[a][1], "x2": pos[b][0], "y2": pos[b][1],
                                "op": 0.03 if some else (0.75 if destaque else (0.08 if foco else 0.22))})
    ea = pd.DataFrame(arestas, columns=["x", "y", "x2", "y2", "op"])
    df["op"] = [0.15 if i in removidos else (1.0 if (not foco or i in vizinhos) else 0.18) for i in df["id"]]
    df["borda"] = ["#0a0a0a" if (i == foco or i in perdem) else "#ffffff" for i in df["id"]]
    df["larg"] = [2.2 if (i == foco or i in perdem) else 0.8 for i in df["id"]]
    eixo = alt.Axis(title=None, labels=False, ticks=False, domain=False, grid=False)
    base_x = alt.X("x:Q", axis=eixo, scale=alt.Scale(zero=False, padding=12))
    base_y = alt.Y("y:Q", axis=eixo, scale=alt.Scale(zero=False, padding=12))
    linhas = alt.Chart(ea).mark_rule(color="#9a9a9a", strokeWidth=0.8).encode(
        x=base_x, y=base_y, x2="x2:Q", y2="y2:Q", opacity=alt.Opacity("op:Q", legend=None, scale=None))
    pontos = alt.Chart(df).mark_circle(stroke="#ffffff").encode(
        x=base_x, y=base_y,
        color=alt.Color("cor:N", scale=alt.Scale(domain=dom, range=rng), legend=alt.Legend(title=None, orient="bottom", columns=6)),
        size=alt.Size("intermediacao:Q", scale=alt.Scale(range=[30, 520]), legend=None),
        opacity=alt.Opacity("op:Q", legend=None, scale=None),
        stroke=alt.Stroke("borda:N", scale=None), strokeWidth=alt.StrokeWidth("larg:Q", scale=None),
        tooltip=[alt.Tooltip("id:N", title="Pessoa"), alt.Tooltip("area:N", title="Área"),
                 alt.Tooltip("papel_txt:N", title="Papel"), alt.Tooltip("citacoes_recebidas:Q", title="Citações recebidas"),
                 alt.Tooltip("intermed:Q", title="Intermediação")])
    if selecionavel:
        pontos = pontos.add_params(alt.selection_point(name="pessoa", fields=["id"], on="click", empty=False))
    marcas = [linhas, pontos]
    if removidos:
        fora = df[df["id"].isin(removidos)]
        marcas.append(alt.Chart(fora).mark_point(shape="cross", size=260, color="#0a0a0a", strokeWidth=2.5).encode(x=base_x, y=base_y))
    return alt.layer(*marcas).properties(height=altura).configure_view(strokeWidth=0)


# ------------------------------------------------------------------ abas


def aba_visao_geral(r: ona.Resultado) -> None:
    conf = r["confiabilidade"]
    if conf["nivel"] == "insuficiente":
        st.error(f"Só {pct(r['taxa_resposta'])} responderam. Abaixo de 70%, a análise não conclui sobre pontes, isolados, "
                 "buracos estruturais nem dependência. Os números servem para planejar a próxima rodada.", icon=":material/block:")
    elif conf["nivel"] == "cautela":
        st.warning("Leia com cautela: " + "; ".join(conf["motivos"]) + ".", icon=":material/info:")
    else:
        st.success("Taxa de resposta e simulações dão uma leitura estável.", icon=":material/check:")
    c = st.columns(4)
    c[0].metric("Responderam", pct(r["taxa_resposta"]), help=f"{r['responderam']} de {r['pessoas']} pessoas convidadas.", border=True)
    c[1].metric("Grupos de conversa", r["comunidades"], help=f"Louvain em {r['execucoes_louvain']} execuções. "
                f"Modularidade {num(r['modularidade'], 2)}; concordância entre execuções {num(r['estabilidade_comunidades'], 2)}.",
                border=True)
    c[2].metric("Distância média", num(r["distancia_media"], 1), help="Passos, em média, entre duas pessoas (rede simetrizada).", border=True)
    c[3].metric("Eficiência da rede", num(r["eficiencia"], 2), help="Eficiência global (Latora e Marchiori, 2001), de 0 a 1.",
                border=True)
    c = st.columns(4)
    silos = [a["area"] for a in r["areas"] if a["silo"]]
    c[0].metric("Pessoas", r["pessoas"], border=True)
    c[1].metric("Pares ligados", r["ligacoes"], help=f"{r['citacoes']} citações dirigidas.", border=True)
    c[2].metric("Áreas em silo", len(silos), help=", ".join(silos) or "nenhuma", border=True)
    c[3].metric("Reciprocidade", pct(r["reciprocidade"]), help="Entre pares em que as duas pessoas responderam.", border=True)
    st.markdown("#### Primeiro, o que pesa")
    for i in r["insights"][:3]:
        cartao(i)
    st.caption("Diagnóstico de rede, não avaliação de pessoa. Intermediação alta não é desempenho alto, e isolamento é "
               "sinal para conversar.")


def cartao(i: dict) -> None:
    rotulo, forte = NIVEL[i["nivel"]]
    with st.container(border=True):
        st.html(f'<span class="ona-tag{" forte" if forte else ""}">{rotulo}</span>')
        st.markdown(f"**{i['titulo']}**")
        st.write(i["texto"])


def aba_insights(r: ona.Resultado) -> None:
    st.write("Do mais importante para o menos. Cada achado traz o número, a leitura e uma pergunta para levar ao gestor.")
    for i in r["insights"]:
        cartao(i)


def aba_rede(r: ona.Resultado, chave: str) -> None:
    pos = layout(r, chave)
    if pos is None:
        st.info(f"A rede tem {r['pessoas']} pessoas. Acima de {LIMITE_DESENHO - 1}, o app mostra só as métricas.")
        return
    evento = st.session_state.get("grafico_rede")
    if evento and evento.get("selection", {}).get("pessoa"):
        clicado = evento["selection"]["pessoa"][0].get("id")
        if clicado and clicado != st.session_state.get("ultimo_clique"):
            st.session_state["ultimo_clique"] = clicado
            st.session_state["pessoa_sel"] = clicado
    todas = [a["area"] for a in r["areas"]]
    c1, c2 = st.columns([1, 2])
    modo = c1.segmented_control("Cor por", ["área", "comunidade", "papel"], default="área", key="modo_cor") or "área"
    areas = c2.multiselect("Áreas no desenho", todas, default=todas, key="areas_rede") or todas
    esq, dir_ = st.columns([3, 1.25], gap="medium")
    ids = [p["id"] for p in r["por_pessoa"]]
    with dir_:
        foco = st.selectbox("Pessoa", ids, index=None, placeholder="clique num ponto ou escolha", key="pessoa_sel")
        if foco:
            detalhe_pessoa(r, foco)
        else:
            st.html('<p class="ona-nota">Passe o mouse para ver o detalhe. Clique num ponto para destacar a pessoa e '
                    "quem está ligado a ela. Role para aproximar.</p>")
    with esq:
        st.altair_chart(grafico_rede(r, pos, modo, areas, foco), width="stretch", on_select="rerun",
                        selection_mode="pessoa", key="grafico_rede")
        st.caption("Cada ponto é uma pessoa; cada linha, uma ligação citada em qualquer sentido. O tamanho cresce com a "
                   "intermediação.")


def detalhe_pessoa(r: ona.Resultado, pid: str) -> None:
    pp = {p["id"]: p for p in r["por_pessoa"]}
    p = pp[pid]
    ordem = sorted(r["por_pessoa"], key=lambda x: -x["intermediacao"])
    pos_btw = [x["id"] for x in ordem].index(pid) + 1
    with st.container(border=True):
        st.markdown(f"**{pid}** · {p['area']}" + (f" · {p['cargo']}" if p["cargo"] else ""))
        st.write(f"{'Respondeu' if p['respondeu'] else 'Não respondeu'} ao questionário. "
                 f"{p['citacoes_recebidas']} citações recebidas, {p['conexoes']} ligações em qualquer sentido.")
        st.write(f"Intermediação {num(p['intermediacao'], 3)} ({pos_btw}ª de {r['pessoas']}). "
                 + (f"Restrição de Burt {num(p['restricao'], 2)}. " if p["restricao"] is not None else "")
                 + f"Papel: {NOME_PAPEL.get(p['papel'] or '', 'nenhum em destaque')}. Grupo {p['comunidade'] + 1}.")
        st.caption("Posição na rede, não desempenho.")
        if st.button("Simular a saída", icon=":material/person_remove:", key="simular_desta"):
            st.session_state["saem"] = [pid]
            st.toast(f"Abra a aba \"E se sair\" para ver o efeito de tirar {pid}.")


def aba_saida(r: ona.Resultado, chave: str) -> None:
    pode = r["confiabilidade"]["nivel"] != "insuficiente"
    if not pode:
        st.warning("Com menos de 70% de resposta, a simulação aparece só para orientar a próxima rodada.")
    ids = [p["id"] for p in r["por_pessoa"]]
    padrao = st.session_state.get("saem") or ([r["riscos"][0]["id"]] if r["riscos"] else [])
    padrao = [i for i in padrao if i in ids]
    saem = st.multiselect("Quem sai", ids, default=padrao, key=f"saem_{chave}",
                          help="Escolha uma ou mais pessoas. A rede é recalculada sem elas.")
    if saem:
        s = ona.simular_saida(r, saem)
        c = st.columns(4)
        c[0].metric("Ficam sem caminho", len(s["perdem_caminho"]), help="Pessoas que estavam ligadas à maior parte da rede e deixam de estar.",
                    border=True)
        c[1].metric("Pedaços da rede", s["componentes"], delta=s["componentes"] - s["componentes_antes"] or None,
                    delta_color="inverse", border=True)
        c[2].metric("Eficiência", num(s["eficiencia"], 2), delta=f"-{pct(s['queda_eficiencia'])}" if s["queda_eficiencia"] > 0.0005 else None,
                    border=True)
        c[3].metric("Distância média", num(s["distancia_media"], 2),
                    delta=num(s["distancia_media"] - s["distancia_media_antes"], 2) if not s["perdem_caminho"] else None,
                    delta_color="inverse", border=True,
                    help="Passos, em média, entre duas pessoas. Com gente sem caminho, só conta quem continua ligado.")
        if s["perdem_caminho"]:
            areas = ", ".join(f"{a} ({q})" for a, q in sorted(s["areas_afetadas"].items(), key=lambda x: -x[1]))
            st.markdown(f"**Sem {', '.join(saem)}, {len(s['perdem_caminho'])} pessoas ficam sem nenhum caminho até o resto "
                        f"da organização.** Por área: {areas}. É um ponto único de falha: vale criar um segundo canal antes "
                        "que ele faça falta.")
        else:
            st.markdown(f"**Ninguém perde o caminho**, mas a informação passa a dar mais voltas: a eficiência cai "
                        f"{pct(s['queda_eficiencia'])}.")
        pos = layout(r, chave)
        if pos:
            st.altair_chart(grafico_rede(r, pos, "área", [a["area"] for a in r["areas"]], removidos=saem,
                                         perdem=s["perdem_caminho"], selecionavel=False, altura=460), width="stretch")
            st.caption("O X marca quem saiu; o contorno escuro, quem ficou sem caminho.")
    st.markdown("#### As maiores intermediações, tiradas uma de cada vez")
    df = r.riscos_df()
    if not df.empty:
        df = df.assign(queda=lambda d: (d["queda_eficiencia"] * 100).round(0))[["id", "area", "perdem_caminho", "queda", "intermediacao"]]
        st.dataframe(df, hide_index=True, width="stretch", column_config={
            "id": "Pessoa", "area": "Área", "perdem_caminho": st.column_config.NumberColumn("Ficam sem caminho"),
            "queda": st.column_config.NumberColumn("Queda da eficiência", format="%d%%"),
            "intermediacao": st.column_config.NumberColumn("Intermediação", format="%.3f")})


def aba_areas(r: ona.Resultado) -> None:
    st.write("E-I vai de -1 (só ligações internas) a +1 (só externas). Toda área conversa mais para dentro do que o acaso; "
             "silo é a área com E-I abaixo do esperado (p < 0,01) e menos de 25% das ligações externas que teria ao acaso.")
    linhas = []
    for a in r["areas"]:
        if a["oculta"]:
            linhas.append({"Área": a["area"], "Pessoas": a["pessoas"], "Resposta": None, "E-I": None, "E-I esperado": None,
                           "Externas vs. acaso": None, "Silo": f"menos de {GRUPO_MINIMO} pessoas", "Porteiro principal": "–"})
            continue
        linhas.append({
            "Área": a["area"], "Pessoas": a["pessoas"], "Resposta": round(a["taxa_resposta"] * 100),
            "E-I": a["ei"], "E-I esperado": a["ei_esperado"],
            "Externas vs. acaso": round(a["externo_vs_acaso"] * 100) if a["externo_vs_acaso"] is not None else None,
            "Silo": "sim" if a["silo"] else "não",
            "Porteiro principal": f"{a['porteiro_principal']} ({pct(a['porteiro_participacao'])})" if a["porteiro_principal"] else "–"})
    st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch", column_config={
        "Resposta": st.column_config.NumberColumn(format="%d%%"), "E-I": st.column_config.NumberColumn(format="%.2f"),
        "E-I esperado": st.column_config.NumberColumn(format="%.2f"),
        "Externas vs. acaso": st.column_config.NumberColumn(format="%d%%")})
    st.markdown("#### Gestor e time")
    g = pd.DataFrame(r["gestores"])
    if not g.empty:
        g = g[g["time"] >= GRUPO_MINIMO].assign(fracao=lambda d: (d["fracao"] * 100).round(0))
        st.dataframe(g, hide_index=True, width="stretch", column_config={
            "gestor": "Gestor", "area": "Área", "time": "Time", "ligados": "Ligados ao gestor",
            "fracao": st.column_config.NumberColumn("Fração do time", format="%d%%")})
    st.markdown("#### Quanto o resultado aguenta menos dados")
    s = r.get("sensibilidade")
    if s:
        d = s["dirigida_vs_simetrizada"]
        st.markdown(
            f"- Em {s['replicas']} sorteios, apagando as citações de mais {s['pessoas_retiradas']} pessoas, "
            f"{pct(s['pontes_mantidas'])} das cinco maiores pontes continuaram no topo (no pior sorteio, {pct(s['pontes_mantidas_min'])}).\n"
            f"- O diagnóstico de silo se repetiu em {pct(s['silo_estavel'])} dos sorteios; os isolados variaram de "
            f"{s['isolados_min']} a {s['isolados_max']}.\n"
            f"- Rede dirigida x simetrizada: {pct(d['top5_em_comum'])} das cinco maiores pontes em comum. Entre as dez maiores, "
            f"{d['nao_respondentes_top10_simetrizada']} não respondeu ao questionário; na rede dirigida, "
            f"{d['nao_respondentes_top10_dirigida']}.")


def aba_pessoas(r: ona.Resultado) -> None:
    st.write("A tabela por pessoa fica escondida por padrão. Ela serve para quem conduz a análise conferir os números, "
             "não para circular. Nenhuma métrica daqui deve entrar em avaliação, promoção ou desligamento.")
    if not st.toggle("Mostrar a tabela por pessoa", value=False, key="mostrar_pessoas"):
        return
    df = r.pessoas_df().copy()
    df["papel"] = df["papel"].map(lambda p: NOME_PAPEL.get(p, "") if p else "")
    df["comunidade"] = df["comunidade"] + 1
    cols = ["id", "area", "respondeu", "citacoes_recebidas", "conexoes", "intermediacao", "restricao", "tamanho_efetivo",
            "nucleo", "comunidade", "papel"]
    st.dataframe(df[cols].sort_values("intermediacao", ascending=False), hide_index=True, width="stretch", column_config={
        "id": "Pessoa", "area": "Área", "respondeu": "Respondeu", "citacoes_recebidas": "Citações recebidas",
        "conexoes": "Ligações", "intermediacao": st.column_config.NumberColumn("Intermediação", format="%.3f"),
        "restricao": st.column_config.NumberColumn("Restrição", format="%.2f"),
        "tamanho_efetivo": st.column_config.NumberColumn("Tamanho efetivo", format="%.1f"),
        "nucleo": "Núcleo (k-core)", "comunidade": "Grupo", "papel": "Papel"})


def aba_baixar(r: ona.Resultado, chave: str, fonte: str) -> None:
    st.write("O relatório é um arquivo HTML único, que abre sem internet: dá para mandar ao gestor por e-mail. Ele não traz "
             "a tabela por pessoa. O CSV tem as métricas por pessoa, para o Power BI ou o Excel.")
    c1, c2 = st.columns(2)
    c1.download_button("Relatório HTML", relatorio_html(r, chave, fonte), "relatorio-ona.html", "text/html", type="primary",
                       icon=":material/description:", on_click="ignore", width="stretch")
    c2.download_button("Métricas por pessoa (CSV)", oio.para_csv(r.pessoas_df()), "metricas-ona.csv", "text/csv",
                       icon=":material/table:", on_click="ignore", width="stretch")


# ------------------------------------------------------------------ página


def main() -> None:
    cabecalho()
    entrada()
    dados = st.session_state.get("dados")
    if not dados:
        st.html('<p class="ona-nota">Nada sai do seu computador: as contas rodam aqui, e as planilhas não vão para servidor.</p>')
        return
    pessoas, ligacoes, fonte = dados
    erros, avisos = oio.validar(pessoas, ligacoes)
    if erros:
        for e in erros:
            st.error(e)
        return
    for a in avisos:
        st.caption(a)
    tipos = sorted(t for t in ligacoes.get("tipo", pd.Series(dtype=str)).dropna().unique() if t)
    with st.sidebar:
        st.subheader("Opções")
        tipo = st.selectbox("Pergunta", ["todos"] + tipos, format_func=lambda t: "todas as perguntas" if t == "todos" else t)
        rede = st.radio("Rede para intermediação e saída", ["simetrizada", "dirigida"],
                        help="Simetrizada: há ligação se um dos dois citou o outro (padrão). Dirigida: só o sentido citado; "
                             "quem não respondeu nunca vira ponte.")
        st.caption(f"Fonte: {fonte}")
    with st.spinner("Calculando a rede, 1.000 permutações e 20 sorteios de não resposta..."):
        r = analisar(pessoas, ligacoes, tipo, rede)
    chave = f"{fonte}|{tipo}|{rede}|{len(pessoas)}|{len(ligacoes)}"
    st.caption(f"{fonte} · {r['pessoas']} pessoas · {r['ligacoes']} pares ligados")
    abas = st.tabs(["Visão geral", "Insights", "Rede", "E se sair", "Áreas", "Pessoas", "Baixar"])
    with abas[0]:
        aba_visao_geral(r)
    with abas[1]:
        aba_insights(r)
    with abas[2]:
        aba_rede(r, chave)
    with abas[3]:
        aba_saida(r, chave)
    with abas[4]:
        aba_areas(r)
    with abas[5]:
        aba_pessoas(r)
    with abas[6]:
        aba_baixar(r, chave, fonte)


main()
