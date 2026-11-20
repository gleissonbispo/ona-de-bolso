"""Regra de leitura e insights em português de gestor.

Mesmos critérios e textos do motor JavaScript da v1. Os textos lembram sempre que o resultado é um
diagnóstico da rede, não uma avaliação de pessoa.
"""

from __future__ import annotations

import math

from .metricas import ALFA_SILO, GRUPO_MINIMO, LIMIAR_CAUTELA, LIMIAR_RESPOSTA, LIMIAR_SILO


def pct(x: float) -> str:
    return f"{math.floor(x * 100 + 0.5)}%"


def num(x: float, d: int) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def lista(v: list[str]) -> str:
    if len(v) <= 1:
        return "".join(v)
    return ", ".join(v[:-1]) + " e " + v[-1]


def confiabilidade(r: dict) -> dict:
    """Nível de confiança da leitura: boa, cautela ou insuficiente."""
    s = r.get("sensibilidade")
    motivos: list[str] = []
    if r["taxa_resposta"] < LIMIAR_RESPOSTA:
        motivos.append(f"menos de {pct(LIMIAR_RESPOSTA)} das pessoas responderam")
        return {"nivel": "insuficiente", "motivos": motivos}
    if r["taxa_resposta"] < LIMIAR_CAUTELA:
        motivos.append(f"a taxa de resposta está entre {pct(LIMIAR_RESPOSTA)} e 85%")
    if s and s["pontes_mantidas"] < 0.6:
        motivos.append("as maiores pontes mudam quando a resposta cai mais 10%")
    if s and s["silo_estavel"] < 0.8:
        motivos.append("o diagnóstico de silo muda em parte das simulações")
    return {"nivel": "cautela" if motivos else "boa", "motivos": motivos}


def gerar_insights(r: dict) -> list[dict]:
    """Lista de insights ordenada por prioridade (1 = ler primeiro). nivel: alerta, risco, atencao, info."""
    out: list[dict] = []
    s = r.get("sensibilidade")
    conf = r["confiabilidade"]
    nr = r["pessoas"] - r["responderam"]
    pode_concluir = conf["nivel"] != "insuficiente"

    if conf["nivel"] == "insuficiente":
        out.append({"prioridade": 1, "nivel": "alerta", "tema": "dados",
                    "titulo": f"Só {pct(r['taxa_resposta'])} responderam: não dá para concluir sobre pontes e isolados",
                    "texto": f"{nr} pessoas não responderam. Abaixo de {pct(LIMIAR_RESPOSTA)}, as ligações que faltam mudam "
                             "quem parece ponte e quem parece isolado. Os números aparecem para orientar a próxima rodada, "
                             "mas não sustentam decisão sobre pessoas ou áreas."})
    elif r["taxa_resposta"] < 0.999:
        cautela = conf["nivel"] == "cautela"
        texto = (f"{nr} pessoas não responderam. Elas aparecem quando alguém as cita, e a análise conta a ligação "
                 "nos dois sentidos para não apagá-las.")
        if s:
            texto += (f" Simulando mais 10% de não resposta ({s['replicas']} sorteios), em média "
                      f"{pct(s['pontes_mantidas'])} das cinco maiores pontes continuam no topo e o diagnóstico de silo "
                      f"se repete em {pct(s['silo_estavel'])} dos sorteios.")
        if conf["motivos"]:
            texto += f" Ponto de atenção: {lista(conf['motivos'])}."
        leitura = ": resultado estável" if conf["nivel"] == "boa" else ": leia com cautela"
        out.append({"prioridade": 2 if cautela else 9, "nivel": "atencao" if cautela else "info", "tema": "dados",
                    "titulo": f"Taxa de resposta de {pct(r['taxa_resposta'])}{leitura}", "texto": texto})

    # risco de dependência
    corte = [x for x in r["riscos"] if x["perdem_caminho"] >= max(3, 0.03 * r["pessoas"])]
    if pode_concluir:
        for k, x in enumerate(corte[:2]):
            areas = sorted(x["areas_afetadas"], key=lambda a: -x["areas_afetadas"][a])
            out.append({"prioridade": 2 + k * 0.1, "nivel": "risco", "tema": "dependencia", "ids": [x["id"]],
                        "titulo": f"Uma saída deixaria {x['perdem_caminho']} pessoas sem caminho até o resto da rede",
                        "texto": f"Sem {x['id']} ({x['area']}), {x['perdem_caminho']} pessoas"
                                 + (f", quase todas de {areas[0]}," if areas else "")
                                 + " deixam de ter qualquer caminho de conversa com o restante da organização, e a eficiência "
                                 f"da rede cai {pct(x['queda_eficiencia'])}. É um ponto único de falha: o problema é a rede "
                                 "depender de uma pessoa só. Vale criar um segundo canal (rituais entre áreas, par de backup) "
                                 "antes que ele faça falta."})
    if pode_concluir and not corte and r["riscos"]:
        top = sorted(r["riscos"], key=lambda x: -x["queda_eficiencia"])[0]
        out.append({"prioridade": 6, "nivel": "info", "tema": "dependencia", "ids": [top["id"]],
                    "titulo": "Nenhuma saída isolada parte a rede",
                    "texto": f"Testamos tirar, uma de cada vez, as {len(r['riscos'])} pessoas com maior intermediação. "
                             f"A maior perda é de {pct(top['queda_eficiencia'])} na eficiência da rede (sem {top['id']}). "
                             "Não há ponto único de falha."})

    # silos (com linha de base)
    for a in [a for a in r["areas"] if a["silo"]]:
        texto = (f"{a['externo']} de {a['interno'] + a['externo']} ligações da área cruzam a fronteira (E-I de {num(a['ei'], 2)}). "
                 f"Se as conversas ignorassem a área, o esperado seria um E-I de {num(a['ei_esperado'], 2)}: a área tem só "
                 f"{pct(a['externo_vs_acaso'])} das ligações externas que teria ao acaso. Toda área conversa mais para dentro, "
                 "e isso é normal; esta está muito abaixo das demais. Confira se é escolha (trabalho que precisa de "
                 "isolamento) ou gargalo.")
        if a["porteiro_principal"] and a["porteiro_participacao"] >= 0.5:
            texto += (f" E a informação de fora entra quase toda por uma pessoa: {a['porteiro_principal']} responde por "
                      f"{pct(a['porteiro_participacao'])} das entradas.")
        out.append({"prioridade": 3, "nivel": "risco", "tema": "silo", "area": a["area"],
                    "titulo": f"{a['area']} fala quase só para dentro", "texto": texto})
    fechadas = [a for a in r["areas"] if not a["oculta"] and not a["silo"] and a["p_valor"] is not None and a["p_valor"] < ALFA_SILO]
    if fechadas:
        vals = [a["externo_vs_acaso"] for a in fechadas]
        out.append({"prioridade": 8, "nivel": "info", "tema": "silo",
                    "titulo": "As demais áreas conversam para dentro na medida do esperado",
                    "texto": f"{lista([a['area'] for a in fechadas])} têm mais ligações internas do que o acaso daria, o que é "
                             "normal em qualquer empresa (as pessoas trabalham com o próprio time). Elas mantêm entre "
                             f"{pct(min(vals))} e {pct(max(vals))} das ligações externas que teriam ao acaso. Só chamamos de "
                             f"silo a área abaixo de {pct(LIMIAR_SILO)}."})

    # porteiros fora dos silos
    for a in r["areas"]:
        if (not a["oculta"] and not a["silo"] and a["porteiro_principal"] and a["porteiro_participacao"] >= 0.5
                and a["entradas_de_fora"] >= 10):
            out.append({"prioridade": 4, "nivel": "atencao", "tema": "porteiro", "area": a["area"], "ids": [a["porteiro_principal"]],
                        "titulo": f"Em {a['area']}, a informação de fora entra por uma pessoa",
                        "texto": f"{a['porteiro_principal']} aparece em {pct(a['porteiro_participacao'])} dos caminhos em que "
                                 "algo de outra área chega ao time (papel de porteiro, Gould e Fernandez). Isso filtra ruído, "
                                 "mas também pode virar gargalo. Vale ver se mais gente do time tem contato direto com as "
                                 "áreas parceiras."})

    for x in r["gestores"]:
        if x["time"] >= GRUPO_MINIMO and x["fracao"] < 0.2:
            out.append({"prioridade": 4.5, "nivel": "atencao", "tema": "gestor", "ids": [x["gestor"]],
                        "titulo": f"Gestor de {x['area']} fora do fluxo do próprio time",
                        "texto": f"Só {x['ligados']} de {x['time']} pessoas do time têm ligação direta, em qualquer sentido, "
                                 f"com o gestor ({x['gestor']}). A informação do time está passando por outro caminho; vale "
                                 "entender qual."})

    if r["pontes"] and pode_concluir:
        p3 = r["pontes"][:3]
        nao_resp = [p["id"] for p in p3 if not p["respondeu"]]
        texto = (f"{lista([p['id'] + ' (' + p['area'] + ')' for p in p3])} têm as maiores intermediações: estão no caminho "
                 "mais curto entre muitos pares de colegas. ")
        if nao_resp:
            texto += (f"{lista(nao_resp)} não respondeu ao questionário e aparece como ponte porque os colegas a citam; na "
                      "rede só com o sentido citado, isso ficaria invisível. ")
        texto += "Pergunta para o gestor: se uma delas sair ou mudar de função, quem assume esse papel?"
        out.append({"prioridade": 5, "nivel": "atencao", "tema": "pontes", "ids": [p["id"] for p in p3],
                    "titulo": "As três maiores pontes da rede", "texto": texto})

    baixos = [p for p in r["por_pessoa"] if p["restricao"] is not None and p["conexoes"] >= 4]
    if len(baixos) >= 10 and pode_concluir:
        ordem = sorted(baixos, key=lambda p: p["restricao"])[:3]
        out.append({"prioridade": 7, "nivel": "info", "tema": "burt", "ids": [p["id"] for p in ordem],
                    "titulo": "Quem cobre buracos estruturais",
                    "texto": f"{lista([p['id'] for p in ordem])} têm a menor restrição de Burt "
                             f"({lista([num(p['restricao'], 2) for p in ordem])}): falam com grupos que não se falam entre si. "
                             "Na pesquisa de Burt (2004), redes assim estão ligadas a ideias mais bem avaliadas. É um retrato "
                             "de posição na rede, não de desempenho."})

    if r["isolados"] and pode_concluir:
        sem_resp = sum(1 for p in r["isolados"] if not p["respondeu"])
        out.append({"prioridade": 6.5, "nivel": "atencao", "tema": "isolados", "ids": [p["id"] for p in r["isolados"]],
                    "titulo": f"{len(r['isolados'])} pessoas fora do fluxo",
                    "texto": "Ninguém as citou e elas têm no máximo uma ligação. "
                             + (f"{sem_resp} delas não respondeu, então pode ser só falta de dado. " if sem_resp else "")
                             + "Antes de qualquer conclusão, confira se são recém-chegadas, se estão afastadas ou se trabalham "
                             "remoto. Isolamento na rede é sinal para conversar, não diagnóstico."})

    estavel = "estável" if r["estabilidade_comunidades"] >= 0.8 else "instável"
    out.append({"prioridade": 8.5, "nivel": "info", "tema": "comunidades",
                "titulo": f"{r['comunidades']} grupos reais de conversa",
                "texto": f"O algoritmo de comunidades (Louvain, {r['execucoes_louvain']} execuções, fica a melhor) achou "
                         f"{r['comunidades']} grupos, com modularidade de {num(r['modularidade'], 2)} (acima de 0,3 indica grupos "
                         f"bem separados). A divisão é {estavel}: concordância média de {num(r['estabilidade_comunidades'], 2)} "
                         "entre as execuções (1 = idênticas). Compare com o organograma: área que se divide em vários grupos "
                         "ou grupos que juntam áreas diferentes dizem como o trabalho acontece."})
    out.append({"prioridade": 9.5, "nivel": "info", "tema": "reciprocidade",
                "titulo": f"Reciprocidade de {pct(r['reciprocidade'])}",
                "texto": f"Entre pares em que as duas pessoas responderam, {math.floor(r['reciprocidade'] * 100 + 0.5)} em cada 100 "
                         "se citam nos dois sentidos. Reciprocidade baixa em pedidos de ajuda costuma indicar sobrecarga em "
                         "quem é muito procurado."})
    out.append({"prioridade": 9.6, "nivel": "info", "tema": "concentracao",
                "titulo": f"As 5% mais citadas recebem {pct(r['concentracao_top5pct'])} das citações",
                "texto": "Quanto maior esse número, mais a rede depende de poucas pessoas para funcionar."})
    return sorted(out, key=lambda x: x["prioridade"])
