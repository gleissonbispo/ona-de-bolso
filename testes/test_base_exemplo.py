"""Parte 2: a base sintética tem estrutura plantada; o que foi plantado tem de aparecer."""

import time

import pandas as pd
import pytest

import ona_de_bolso as ona
from ona_de_bolso import metricas as m


def test_validacao_sem_erros(base):
    erros, _ = ona.validar(*base)
    assert erros == []


def test_pessoas_citacoes_e_pares(resultado, gabarito):
    assert resultado["pessoas"] == gabarito["pessoas"]
    assert resultado["citacoes"] == gabarito["pares_citados"]
    assert resultado["ligacoes"] == gabarito["pares_ligados"]


def test_pontes_e_porteiro_entre_as_5_maiores_intermediacoes(resultado, gabarito):
    top5 = [p["id"] for p in resultado["pontes"]]
    assert all(x in top5 for x in gabarito["pontes"] + [gabarito["porteiro"]])


def test_ponte_que_nao_respondeu(resultado, gabarito):
    pp = {p["id"]: p for p in resultado["por_pessoa"]}
    ranks = [p["id"] for p in sorted(resultado["por_pessoa"], key=lambda p: -p["intermediacao"])]
    alvo = gabarito["ponte_nao_respondente"]
    assert pp[alvo]["intermediacao_dirigida"] == 0
    assert ranks.index(alvo) < 10


def test_so_o_silo_plantado_e_silo(resultado, gabarito):
    silos = [a["area"] for a in resultado["areas"] if a["silo"]]
    assert silos == [gabarito["silo"]]
    assert all(a["ei"] < a["ei_esperado"] for a in resultado["areas"])
    assert all(a["externo_vs_acaso"] > m.LIMIAR_SILO for a in resultado["areas"] if not a["silo"])


def test_porteiro_plantado(resultado, gabarito):
    pp = {p["id"]: p for p in resultado["por_pessoa"]}
    silo = next(a for a in resultado["areas"] if a["area"] == gabarito["silo"])
    assert pp[gabarito["porteiro"]]["papel"] == "porteiro"
    assert silo["porteiro_principal"] == gabarito["porteiro"]
    assert silo["porteiro_participacao"] > 0.9
    assert pp[gabarito["porteiro"]]["representante"] == 0


def test_e_se_sair_o_ponto_de_corte_e_o_mais_grave(resultado, gabarito):
    risco = resultado["riscos"][0]
    assert risco["id"] == gabarito["ponto_de_corte"]
    assert risco["perdem_caminho"] == 15
    assert risco["areas_afetadas"][gabarito["silo"]] == 15


def test_simulacao_tirar_uma_ponte_nao_parte_mas_alonga_caminhos(resultado, gabarito):
    sim = ona.simular_saida(resultado, [gabarito["pontes"][0]])
    assert sim["perdem_caminho"] == []
    assert sim["distancia_media"] > sim["distancia_media_antes"]


def test_simulacao_de_duas_saidas(resultado, gabarito):
    sim = ona.simular_saida(resultado, [gabarito["porteiro"], gabarito["pontes"][0]])
    assert len(sim["perdem_caminho"]) >= 15
    assert sim["queda_eficiencia"] > resultado["riscos"][0]["queda_eficiencia"]


def test_burt_as_pontes_plantadas_tem_a_menor_restricao(resultado, gabarito):
    com = sorted([p for p in resultado["por_pessoa"] if p["restricao"] is not None and p["conexoes"] >= 4],
                 key=lambda p: p["restricao"])
    ids = [p["id"] for p in com]
    assert all(ids.index(x) < 3 for x in gabarito["pontes"])


def test_isolados_gestor_e_taxa(resultado, gabarito):
    iso = [p["id"] for p in resultado["isolados"]]
    assert all(x in iso for x in gabarito["isolados"])
    gf = next(x for x in resultado["gestores"] if x["gestor"] == gabarito["gestor_fora_do_fluxo"])
    assert gf["fracao"] == min(x["fracao"] for x in resultado["gestores"])
    assert resultado["taxa_resposta"] == pytest.approx(1 - gabarito["nao_respondentes"] / gabarito["pessoas"])


def test_comunidades_separadas_estaveis_e_conexas(resultado, base):
    assert resultado["modularidade"] > 0.3
    assert resultado["estabilidade_comunidades"] >= 0.8
    g = resultado.rede
    com = [p["comunidade"] for p in resultado["por_pessoa"]]
    assert m.comunidade_conexa(g.adj_s, com)
    uma = m.modularidade(g, m.separar_desconexas(g.adj_s, m.louvain(g, 1)))
    assert resultado["modularidade"] >= uma - 1e-12


def test_sensibilidade(resultado):
    s = resultado["sensibilidade"]
    assert s["pontes_mantidas"] >= 0.6
    assert s["silo_estavel"] >= 0.8
    assert resultado["confiabilidade"]["nivel"] == "cautela"


def test_abaixo_de_70_por_cento_alerta_e_some_pontes(base):
    pessoas, ligacoes = base
    rnd = m.mulberry32(5)
    resp = pessoas.loc[pessoas["respondeu"] == "sim", "id"].tolist()
    cortar: set[str] = set()
    while len(cortar) < 20:
        cortar.add(resp[int(rnd() * len(resp))])
    p2 = pessoas.copy()
    p2.loc[p2["id"].isin(cortar), "respondeu"] = "nao"
    l2 = ligacoes[~ligacoes["origem_id"].isin(cortar)]
    r2 = ona.analisar(p2, l2, com_sensibilidade=False)
    assert r2["taxa_resposta"] < 0.7
    assert r2["insights"][0]["nivel"] == "alerta"
    assert not any(i["tema"] in ("pontes", "isolados", "burt", "dependencia") for i in r2["insights"])


def test_entre_70_e_85_pede_cautela_acima_nao(base):
    pessoas, ligacoes = base
    todos = pessoas.copy()
    todos["respondeu"] = "sim"
    r = ona.analisar(todos, ligacoes, com_sensibilidade=False, permutacoes=200)
    assert r["confiabilidade"]["nivel"] == "boa"


def test_area_pequena_fica_escondida(base):
    pessoas, ligacoes = base
    p2 = pessoas.copy()
    p2.loc[p2["id"].isin(["P001", "P002", "P003"]), "area"] = "Diretoria"
    r = ona.analisar(p2, ligacoes, com_sensibilidade=False, permutacoes=100)
    diretoria = next(a for a in r["areas"] if a["area"] == "Diretoria")
    assert diretoria["oculta"] and not diretoria["silo"]
    assert not any(i.get("area") == "Diretoria" for i in r["insights"])


def test_reprodutivel(base, resultado):
    r2 = ona.analisar(*base)
    assert r2.json() == resultado.json()


def test_insights_ordenados_e_dependencia_antes_das_informacoes(resultado):
    ins = resultado["insights"]
    assert all(ins[i - 1]["prioridade"] <= ins[i]["prioridade"] for i in range(1, len(ins)))
    temas = [i["tema"] for i in ins]
    assert temas.index("dependencia") < temas.index("comunidades")


def test_insights_lembram_que_nao_e_avaliacao_de_pessoa(resultado):
    textos = " ".join(i["texto"] for i in resultado["insights"])
    assert "não de desempenho" in textos
    assert "sinal para conversar, não diagnóstico" in textos


def test_aceita_dataframe_ou_lista_de_dicts(base, resultado):
    pessoas, ligacoes = base
    r = ona.analisar(pessoas.to_dict("records"), ligacoes.to_dict("records"))
    assert r["modularidade"] == resultado["modularidade"]
    assert isinstance(resultado.pessoas_df(), pd.DataFrame)


def test_filtro_por_pergunta(base):
    r = ona.analisar(*base, tipo="ajuda", com_sensibilidade=False, permutacoes=100)
    assert r["tipo"] == "ajuda"
    assert r["citacoes"] < 834


def test_calculo_completo_em_menos_de_10_segundos(base):
    t0 = time.perf_counter()
    ona.analisar(*base)
    assert time.perf_counter() - t0 < 10


def test_posicoes_para_desenho(resultado):
    pos = ona.posicoes(resultado)
    assert len(pos) == 114
