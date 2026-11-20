"""Parte 1: cada algoritmo numa rede pequena com resposta conhecida (porte dos testes do motor JS)."""

import math

import networkx as nx
import pytest

from ona_de_bolso import analisar
from ona_de_bolso import metricas as m


def pessoas_de(n, area=None):
    return [{"id": f"N{i}", "area": area(i) if area else "A", "respondeu": "sim"} for i in range(n)]


def cita(pares, tipo="informacao"):
    return [{"origem_id": f"N{o}", "destino_id": f"N{d}", "tipo": tipo, "peso": "1"} for o, d in pares]


def test_mulberry32_reproduz_sequencia_de_referencia():
    r = m.mulberry32(1)
    assert r() == pytest.approx(0.6270739405881613, abs=1e-15)
    assert r() == pytest.approx(0.002735721180215478, abs=1e-15)


def test_mulberry32_fica_entre_0_e_1_com_media_meio():
    r = m.mulberry32(20261116)
    xs = [r() for _ in range(20000)]
    assert all(0 <= x < 1 for x in xs)
    assert sum(xs) / len(xs) == pytest.approx(0.5, abs=0.01)


def test_intermediacao_no_caminho_de_5():
    cam = m.grafo_de_arestas(5, [(0, 1), (1, 2), (2, 3), (3, 4)])
    bc = m.intermediacao(cam)
    assert bc[0] == 0
    assert bc[1] == pytest.approx(0.5)
    assert bc[2] == pytest.approx(4 / 6)
    assert bc[3] == pytest.approx(0.5)


def test_intermediacao_do_centro_da_estrela_e_1():
    est = m.grafo_de_arestas(5, [(0, 1), (0, 2), (0, 3), (0, 4)])
    assert m.intermediacao(est)[0] == pytest.approx(1)


def test_nao_respondente_que_liga_dois_grupos_so_aparece_na_simetrizada():
    ppl = pessoas_de(5, lambda i: "A" if i < 2 else ("B" if i < 4 else "C"))
    ppl[4]["respondeu"] = "nao"
    lig = cita([(0, 1), (1, 0), (2, 3), (3, 2), (0, 4), (1, 4), (2, 4), (3, 4)])
    rs = analisar(ppl, lig, com_sensibilidade=False, permutacoes=50)
    rd = analisar(ppl, lig, com_sensibilidade=False, permutacoes=50, rede="dirigida")
    assert rs["por_pessoa"][4]["intermediacao"] > 0.5
    assert rd["por_pessoa"][4]["intermediacao"] == 0


@pytest.fixture
def duas_panelinhas():
    ar = []
    for a in range(5):
        for b in range(a + 1, 5):
            ar += [(a, b), (a + 5, b + 5)]
    ar.append((4, 5))
    return m.grafo_de_arestas(10, ar)


CERTO = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]


def test_louvain_separa_duas_panelinhas(duas_panelinhas):
    cm = m.comunidades_estaveis(duas_panelinhas, 7, 20)
    assert m.rand_ajustado(cm["comunidade"], CERTO) == 1
    assert cm["estabilidade"] == pytest.approx(1)


def test_modularidade_da_particao_certa_bate_com_a_conta_a_mao(duas_panelinhas):
    assert m.modularidade(duas_panelinhas, CERTO) == pytest.approx(2 * (20 / 42 - (21 / 42) ** 2), abs=1e-12)


def test_refinamento_separa_comunidade_desconectada_sem_perder_modularidade(duas_panelinhas):
    ruim = [0 if (i < 3 or i >= 8) else 1 for i in range(10)]  # {0,1,2,8,9} desconexo
    sep = m.separar_desconexas(duas_panelinhas.adj_s, ruim)
    assert not m.comunidade_conexa(duas_panelinhas.adj_s, ruim)
    assert m.comunidade_conexa(duas_panelinhas.adj_s, sep)
    assert len(set(sep)) == 3
    assert m.modularidade(duas_panelinhas, sep) >= m.modularidade(duas_panelinhas, ruim)


def test_rand_ajustado_ignora_rotulos():
    assert m.rand_ajustado([0, 0, 1, 1], [5, 5, 3, 3]) == pytest.approx(1)


def test_ei_no_grafo_completo_observado_igual_esperado_igual_formula():
    k10 = m.grafo_de_arestas(10, [(a, b) for a in range(10) for b in range(a + 1, 10)])
    grp = [0, 0, 0, 0, 1, 1, 1, 1, 1, 1]
    ei = m.ei_com_base(k10.adj_s, grp, 2, 200, 3)
    assert ei[0]["ei"] == pytest.approx(0.6)
    assert ei[0]["ei_esperado"] == pytest.approx(0.6)
    assert m.ei_esperado_formula(4, 10) == pytest.approx(0.6)
    assert ei[0]["p_valor"] == 1


def test_ei_das_panelinhas_fica_muito_abaixo_do_acaso(duas_panelinhas):
    ei = m.ei_com_base(duas_panelinhas.adj_s, CERTO, 2, 999, 3)
    assert ei[0]["ei"] < ei[0]["ei_esperado"] - 0.5
    assert ei[0]["p_valor"] < 0.01


@pytest.mark.parametrize("papel,areas", [
    ("coordenador", "XXX"), ("consultor", "XYX"), ("representante", "XXY"), ("porteiro", "YXX"), ("ligacao", "XYZ"),
])
def test_gould_fernandez_os_cinco_papeis(papel, areas):
    # C cita B e B cita A: a informação vai de A para B e de B para C
    p = [{"id": f"N{i}", "area": a, "respondeu": "sim"} for i, a in enumerate(areas)]
    g = m.Rede(p, cita([(2, 1), (1, 0)]))
    c = m.papeis_corretagem(g, list(areas))[1]
    assert [k for k, v in c.items() if v == 1] == [papel]


def test_gould_fernandez_nao_conta_quando_c_ja_busca_direto_com_a():
    p = [{"id": f"N{i}", "area": "X", "respondeu": "sim"} for i in range(3)]
    g = m.Rede(p, cita([(2, 1), (1, 0), (2, 0)]))
    assert m.papeis_corretagem(g, [0, 0, 0])[1]["coordenador"] == 0


def test_burt_na_estrela_e_no_triangulo():
    restr, efet = m.burt(m.grafo_de_arestas(4, [(0, 1), (0, 2), (0, 3)]))
    assert restr[0] == pytest.approx(1 / 3)
    assert efet[0] == pytest.approx(3)
    assert restr[1] == pytest.approx(1)
    restr, efet = m.burt(m.grafo_de_arestas(3, [(0, 1), (1, 2), (0, 2)]))
    assert restr[0] == pytest.approx(1.125)
    assert efet[0] == pytest.approx(1)


def test_burt_igual_ao_networkx_com_pesos(base):
    pessoas, ligacoes = base
    g = m.Rede(pessoas.to_dict("records"), ligacoes.to_dict("records"))
    restr, efet = m.burt(g)
    c = nx.constraint(g.G, weight="weight")
    e = nx.effective_size(g.G, weight="weight")
    for i in range(g.n):
        if restr[i] is None:
            assert math.isnan(c[i])
        else:
            assert restr[i] == pytest.approx(c[i], abs=1e-12)
            assert efet[i] == pytest.approx(e[i], abs=1e-12)


def test_k_core_triangulo_e_cauda():
    g = m.grafo_de_arestas(6, [(0, 1), (1, 2), (0, 2), (2, 3), (3, 4), (4, 5)])
    assert m.nucleos(g) == [2, 2, 2, 1, 1, 1]


def test_tirar_o_meio_do_caminho_parte_a_rede():
    cam = m.grafo_de_arestas(5, [(0, 1), (1, 2), (2, 3), (3, 4)])
    base = m.estrutura_rede(cam)
    sai = m.efeito_saida(cam, base, [2])
    assert sai["componentes"] == 2
    assert len(sai["perdem_caminho"]) == 2


def test_eficiencia_global_do_caminho_bate_com_a_conta_e_com_o_networkx():
    cam = m.grafo_de_arestas(5, [(0, 1), (1, 2), (2, 3), (3, 4)])
    ef = m.estrutura_rede(cam)["eficiencia"]
    assert ef == pytest.approx(2 * (4 + 3 * 0.5 + 2 / 3 + 0.25) / 20, abs=1e-12)
    assert ef == pytest.approx(nx.global_efficiency(cam.G), abs=1e-12)
    sem2 = m.estrutura_rede(cam, {2})["eficiencia"]
    assert sem2 == pytest.approx(nx.global_efficiency(cam.G.subgraph([0, 1, 3, 4])), abs=1e-12)


def test_peso_aceita_virgula_e_cai_para_1_quando_invalido():
    assert m._peso("2,5") == 2.5
    assert m._peso("") == 1
    assert m._peso("abc") == 1
    assert m._peso("-3") == 1
