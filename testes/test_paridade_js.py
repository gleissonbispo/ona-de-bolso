"""Paridade com o motor JavaScript da v1 (tag v1-javascript), na base de exemplo.

A referência foi gerada com ``python testes/gerar_referencia_js.py``. O E-I, os sorteios da
sensibilidade e tudo que não depende de Louvain usam o mesmo gerador (mulberry32) e as mesmas regras,
então batem número a número. O Louvain do networkx não é o do motor JS: a partição pode mudar, e aí só
a modularidade (com tolerância) e o que depende dela entram na comparação.
"""

import pytest

import ona_de_bolso as ona

EXATO = 1e-9


def test_resumo_igual(resultado, referencia_js):
    for k in ["pessoas", "ligacoes", "citacoes", "responderam", "componentes", "maior_componente", "nucleo_max",
              "nucleo_pessoas"]:
        assert resultado[k] == referencia_js[k], k
    for k in ["taxa_resposta", "densidade", "reciprocidade", "concentracao_top5pct", "eficiencia", "distancia_media"]:
        assert resultado[k] == pytest.approx(referencia_js[k], abs=EXATO), k


def test_comunidades_com_tolerancia(resultado, referencia_js):
    assert resultado["modularidade"] == pytest.approx(referencia_js["modularidade"], abs=0.02)
    assert resultado["comunidades"] == referencia_js["comunidades"]
    assert abs(resultado["estabilidade_comunidades"] - referencia_js["estabilidade_comunidades"]) < 0.1


def test_areas_e_silo_iguais(resultado, referencia_js):
    for a, b in zip(resultado["areas"], referencia_js["areas"], strict=True):
        assert a["area"] == b["area"]
        assert a["silo"] == b["silo"]
        assert (a["interno"], a["externo"]) == (b["interno"], b["externo"])
        for k in ["ei", "ei_esperado", "p_valor", "externo_vs_acaso", "porteiro_participacao", "representante_participacao"]:
            assert a[k] == pytest.approx(b[k], abs=EXATO), (a["area"], k)
        assert a["porteiro_principal"] == b["porteiro_principal"]
        assert a["representante_principal"] == b["representante_principal"]


def test_pontes_e_porteiro_iguais(resultado, referencia_js):
    assert [p["id"] for p in resultado["pontes"]] == [p["id"] for p in referencia_js["pontes"]]
    silo = next(a for a in resultado["areas"] if a["silo"])
    silo_js = next(a for a in referencia_js["areas"] if a["silo"])
    assert silo["porteiro_principal"] == silo_js["porteiro_principal"] == "P088"


def test_metricas_por_pessoa_iguais(resultado, referencia_js):
    campos_num = ["intermediacao", "intermediacao_dirigida", "intermediacao_simetrizada", "tamanho_efetivo"]
    campos_eq = ["citacoes_recebidas", "citacoes_feitas", "conexoes", "nucleo", "papel", "respondeu",
                 "coordenador", "consultor", "representante", "porteiro", "ligacao"]
    for a, b in zip(resultado["por_pessoa"], referencia_js["por_pessoa"], strict=True):
        assert a["id"] == b["id"]
        for k in campos_eq:
            assert a[k] == b[k], (a["id"], k)
        for k in campos_num:
            assert a[k] == pytest.approx(b[k], abs=EXATO), (a["id"], k)
        if b["restricao"] is None:
            assert a["restricao"] is None
        else:
            assert a["restricao"] == pytest.approx(b["restricao"], abs=EXATO)


def test_e_se_sair_igual(resultado, referencia_js):
    assert [x["id"] for x in resultado["riscos"]] == [x["id"] for x in referencia_js["riscos"]]
    for a, b in zip(resultado["riscos"], referencia_js["riscos"], strict=True):
        assert a["perdem_caminho"] == b["perdem_caminho"]
        assert a["areas_afetadas"] == b["areas_afetadas"]
        assert a["queda_eficiencia"] == pytest.approx(b["queda_eficiencia"], abs=EXATO)
    for pid, b in referencia_js["simulacoes"].items():
        a = ona.simular_saida(resultado, [pid])
        assert sorted(a["perdem_caminho"]) == sorted(b["perdem_caminho"])
        assert a["eficiencia"] == pytest.approx(b["eficiencia"], abs=EXATO)
        assert a["distancia_media"] == pytest.approx(b["distancia_media"], abs=EXATO)


def test_sensibilidade_igual_menos_a_modularidade(resultado, referencia_js):
    a, b = resultado["sensibilidade"], referencia_js["sensibilidade"]
    for k in ["replicas", "pessoas_retiradas", "isolados_min", "isolados_max"]:
        assert a[k] == b[k]
    for k in ["pontes_mantidas", "pontes_mantidas_min", "ei_variacao_media", "silo_estavel"]:
        assert a[k] == pytest.approx(b[k], abs=EXATO)
    assert a["dirigida_vs_simetrizada"] == pytest.approx(b["dirigida_vs_simetrizada"], abs=EXATO)
    assert a["modularidade_min"] == pytest.approx(b["modularidade_min"], abs=0.03)
    assert a["modularidade_max"] == pytest.approx(b["modularidade_max"], abs=0.03)


def test_confiabilidade_e_insights_iguais(resultado, referencia_js):
    assert resultado["confiabilidade"] == referencia_js["confiabilidade"]
    assert [i["titulo"] for i in resultado["insights"]] == [i["titulo"] for i in referencia_js["insights"]]
    for a, b in zip(resultado["insights"], referencia_js["insights"], strict=True):
        if a["tema"] == "comunidades":
            continue  # cita modularidade e estabilidade, que dependem do Louvain
        assert a["texto"].replace("a análise conta", "a página conta") == b["texto"], a["tema"]
