"""Métricas da ONA de bolso.

Entrada: pessoas (id, area, cargo, gestor_id, unidade, respondeu) e ligações (origem_id, destino_id,
tipo, peso), em que a origem cita o destino. Saída: um dicionário com o mesmo formato do motor
JavaScript da v1 (tag ``v1-javascript``), mais as tabelas prontas.

Escolhas de método (detalhe no README e em docs/projeto.md):

- Duas redes. A dirigida (quem cita quem) mede citações recebidas e feitas, reciprocidade e os papéis
  de corretagem. A simetrizada (há ligação se um dos dois citou o outro) mede intermediação,
  comunidades, E-I, restrição de Burt, núcleo e o efeito de uma saída. A informação corre nos dois
  sentidos, e quem não respondeu (não cita ninguém) continua podendo aparecer como ponte.
- O networkx resolve intermediação (Brandes), Louvain, modularidade, k-core e o layout do desenho.
  O resto é nosso: E-I com linha de base por permutação, papéis de Gould e Fernandez, separação de
  comunidades desconectadas, Rand ajustado, "e se sair", sensibilidade à não resposta e regra de leitura.
  Restrição de Burt e eficiência global usam a mesma fórmula do networkx (os testes conferem a
  igualdade), reescritas para rodar em milissegundos.
- Sorteios com mulberry32 e semente fixa, o mesmo gerador do motor JavaScript: as 1.000 permutações
  do E-I e os sorteios da sensibilidade dão exatamente os mesmos números nas duas versões.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, deque
from collections.abc import Callable, Iterable, Sequence
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

GRUPO_MINIMO = 5        # menos que isso, resultado por área não aparece (anonimato)
LIMIAR_RESPOSTA = 0.7   # abaixo disso, o relatório não conclui sobre pontes e isolados
LIMIAR_CAUTELA = 0.85   # entre 70% e 85%, "leia com cautela"
LIMIAR_SILO = 0.25      # silo: menos de 1/4 das ligações externas esperadas ao acaso...
ALFA_SILO = 0.01        # ...e E-I abaixo do esperado com p < 0,01 nas permutações
SEMENTE = 20261116
EXECUCOES_LOUVAIN = 20
PERMUTACOES_EI = 1000
LIMITE_DESENHO = 500    # a partir disso, a rede não é desenhada (só as métricas)
PAPEIS = ["coordenador", "consultor", "representante", "porteiro", "ligacao"]
NOME_PAPEL = {"coordenador": "coordenador", "consultor": "consultor", "representante": "representante",
              "porteiro": "porteiro", "ligacao": "ligação"}
_NAO = re.compile(r"^(nao|não|n|no|0|false|falso)$", re.IGNORECASE)
_EPS = 1e-12


# ---------------------------------------------------------------- gerador pseudoaleatório


def mulberry32(semente: int) -> Callable[[], float]:
    """mulberry32, idêntico ao do motor JavaScript (mesma sequência para a mesma semente)."""
    estado = semente & 0xFFFFFFFF

    def imul(a: int, b: int) -> int:
        return (a * b) & 0xFFFFFFFF

    def proximo() -> float:
        nonlocal estado
        estado = (estado + 0x6D2B79F5) & 0xFFFFFFFF
        t = estado
        t = imul(t ^ (t >> 15), t | 1)
        t ^= (t + imul(t ^ (t >> 7), t | 61)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    return proximo


def embaralhar(a: list, rnd: Callable[[], float]) -> list:
    """Fisher-Yates na mesma ordem do motor JavaScript."""
    for i in range(len(a) - 1, 0, -1):
        j = math.floor(rnd() * (i + 1))
        a[i], a[j] = a[j], a[i]
    return a


# ---------------------------------------------------------------- grafo


class Rede:
    """As duas redes (dirigida e simetrizada) com as pessoas numeradas na ordem da tabela."""

    def __init__(self, pessoas: list[dict], ligacoes: list[dict], tipo: str = "todos"):
        self.idx: dict[str, int] = {}
        self.nos: list[dict] = []
        for p in pessoas:
            pid = p["id"]
            if pid and pid not in self.idx:
                self.idx[pid] = len(self.nos)
                self.nos.append(p)
        n = self.n = len(self.nos)
        self.saida: list[dict[int, float]] = [{} for _ in range(n)]
        self.entrada: list[dict[int, float]] = [{} for _ in range(n)]
        self.viz: list[dict[int, float]] = [{} for _ in range(n)]
        for l in ligacoes:
            if tipo and tipo != "todos" and l.get("tipo", "") != tipo:
                continue
            o, d = self.idx.get(l["origem_id"]), self.idx.get(l["destino_id"])
            if o is None or d is None or o == d:
                continue
            w = _peso(l.get("peso", ""))
            self.saida[o][d] = self.saida[o].get(d, 0) + w
            self.entrada[d][o] = self.entrada[d].get(o, 0) + w
            self.viz[o][d] = self.viz[o].get(d, 0) + w
            self.viz[d][o] = self.viz[d].get(o, 0) + w
        self.adj_s = [sorted(v) for v in self.viz]
        self.adj_out = [sorted(v) for v in self.saida]
        self.adj_in = [sorted(v) for v in self.entrada]
        self.G = nx.Graph()
        self.G.add_nodes_from(range(n))
        self.G.add_weighted_edges_from((i, j, w) for i in range(n) for j, w in self.viz[i].items() if i < j)
        self.D = nx.DiGraph()
        self.D.add_nodes_from(range(n))
        self.D.add_weighted_edges_from((i, j, w) for i in range(n) for j, w in self.saida[i].items())


def _peso(valor: Any) -> float:
    m = re.match(r"\s*[-+]?(\d+([.,]\d*)?|[.,]\d+)", str(valor if valor is not None else ""))
    if not m:
        return 1.0
    w = float(m.group(0).replace(",", "."))
    return w if w > 0 else 1.0


def grafo_de_arestas(n: int, arestas: Iterable[Sequence]) -> Rede:
    """Para testes: rede não dirigida a partir de arestas [(a, b[, peso]), ...]."""
    pessoas = [{"id": f"N{i}", "area": "A", "respondeu": "sim"} for i in range(n)]
    ligacoes = [{"origem_id": f"N{e[0]}", "destino_id": f"N{e[1]}", "peso": str(e[2]) if len(e) > 2 else "1"}
                for e in arestas]
    return Rede(pessoas, ligacoes)


def _registros(tabela: pd.DataFrame | list[dict] | None, colunas: list[str]) -> list[dict]:
    if tabela is None:
        return []
    if isinstance(tabela, pd.DataFrame):
        df = tabela.copy()
        df.columns = [str(c) for c in df.columns]
        regs = df.fillna("").astype(str).to_dict("records")
    else:
        regs = [dict(r) for r in tabela]
    out = []
    for r in regs:
        x = {k: ("" if v is None else str(v)).strip() for k, v in r.items()}
        for c in colunas:
            x.setdefault(c, "")
        out.append(x)
    return out


# ---------------------------------------------------------------- intermediação


def intermediacao(rede: Rede, dirigida: bool = False) -> list[float]:
    """Brandes (2001) pelo networkx, sem peso, normalizada de 0 a 1."""
    g = rede.D if dirigida else rede.G
    if rede.n <= 2:
        return [0.0] * rede.n
    b = nx.betweenness_centrality(g, normalized=True)
    return [float(b[i]) for i in range(rede.n)]


# ---------------------------------------------------------------- comunidades


def louvain(rede: Rede, semente: int) -> list[int]:
    """Louvain (Blondel et al. 2008) do networkx, devolvido como lista de rótulos por pessoa."""
    com = [0] * rede.n
    if rede.G.number_of_edges() == 0:
        return list(range(rede.n))
    for k, grupo in enumerate(nx.community.louvain_communities(rede.G, weight="weight", seed=semente)):
        for v in grupo:
            com[v] = k
    return com


def modularidade(rede: Rede, com: Sequence[int]) -> float:
    if rede.G.number_of_edges() == 0:
        return 0.0
    grupos: dict[int, set[int]] = {}
    for v, c in enumerate(com):
        grupos.setdefault(c, set()).add(v)
    return float(nx.community.modularity(rede.G, list(grupos.values()), weight="weight"))


def renumerar(com: Sequence[int]) -> list[int]:
    """Rótulos por tamanho (maior = 0); empate pelo menor índice."""
    cont = Counter(com)
    prim: dict[int, int] = {}
    for i, c in enumerate(com):
        prim.setdefault(c, i)
    ordem = sorted(cont, key=lambda c: (-cont[c], prim[c]))
    mapa = {c: j for j, c in enumerate(ordem)}
    return [mapa[c] for c in com]


def separar_desconexas(adj_s: list[list[int]], com: Sequence[int]) -> list[int]:
    """Quebra cada comunidade nos seus pedaços conectados (a garantia mínima do Leiden).

    Nunca reduz a modularidade: entre dois pedaços sem ligação, separar só retira o termo negativo
    de grau esperado.
    """
    n = len(com)
    novo = [-1] * n
    prox = 0
    for s in range(n):
        if novo[s] >= 0:
            continue
        novo[s] = prox
        fila = deque([s])
        while fila:
            v = fila.popleft()
            for w in adj_s[v]:
                if novo[w] < 0 and com[w] == com[s]:
                    novo[w] = prox
                    fila.append(w)
        prox += 1
    return renumerar(novo)


def comunidade_conexa(adj_s: list[list[int]], com: Sequence[int]) -> bool:
    return len(set(separar_desconexas(adj_s, com))) == len(set(com))


def rand_ajustado(a: Sequence, b: Sequence) -> float:
    """Índice de Rand ajustado (Hubert e Arabie 1985): 1 = partições idênticas, 0 = acaso."""
    n = len(a)

    def c2(x: float) -> float:
        return x * (x - 1) / 2

    sij = sum(c2(v) for v in Counter(zip(a, b, strict=True)).values())
    sa = sum(c2(v) for v in Counter(a).values())
    sb = sum(c2(v) for v in Counter(b).values())
    esperado = sa * sb / c2(n) if n > 1 else 0
    maximo = (sa + sb) / 2
    if maximo == esperado:
        return 1.0
    return (sij - esperado) / (maximo - esperado)


def comunidades_estaveis(rede: Rede, semente: int = SEMENTE, execucoes: int = EXECUCOES_LOUVAIN) -> dict:
    """Louvain com várias sementes; fica a divisão de maior modularidade (depois do refinamento).

    Estabilidade = Rand ajustado médio entre a divisão escolhida e as outras execuções.
    """
    runs = []
    melhor = -1
    for i in range(execucoes):
        bruto = louvain(rede, semente + 7919 * i)
        com = separar_desconexas(rede.adj_s, bruto)
        runs.append({"com": com, "q": modularidade(rede, com), "separadas": len(set(com)) - len(set(bruto))})
        if melhor < 0 or runs[i]["q"] > runs[melhor]["q"] + _EPS:
            melhor = i
    outras = [rand_ajustado(runs[melhor]["com"], r["com"]) for i, r in enumerate(runs) if i != melhor]
    qs = [r["q"] for r in runs]
    return {
        "comunidade": runs[melhor]["com"], "modularidade": runs[melhor]["q"],
        "estabilidade": sum(outras) / len(outras) if outras else 1.0, "execucoes": execucoes,
        "modularidade_min": min(qs), "modularidade_max": max(qs),
        "pedacos_separados": sum(r["separadas"] for r in runs),
    }


# ---------------------------------------------------------------- índice E-I com linha de base


def _pares(adj_s: list[list[int]]) -> tuple[np.ndarray, np.ndarray]:
    i = [a for a, viz in enumerate(adj_s) for b in viz if b > a]
    j = [b for a, viz in enumerate(adj_s) for b in viz if b > a]
    return np.array(i, dtype=np.int64), np.array(j, dtype=np.int64)


def ei_contagem(adj_s: list[list[int]], grupo: Sequence[int], ng: int, pares=None) -> tuple[np.ndarray, np.ndarray]:
    """Ligações internas e externas de cada grupo (pares da rede simetrizada)."""
    pi, pj = pares if pares is not None else _pares(adj_s)
    g = np.asarray(grupo, dtype=np.int64)
    gi, gj = g[pi], g[pj]
    mesma = gi == gj
    interno = np.bincount(gi[mesma], minlength=ng).astype(float)
    externo = (np.bincount(gi[~mesma], minlength=ng) + np.bincount(gj[~mesma], minlength=ng)).astype(float)
    return interno, externo


def ei_com_base(adj_s: list[list[int]], grupo: Sequence[int], ng: int, permutacoes: int = PERMUTACOES_EI,
                semente: int = SEMENTE + 1) -> list[dict]:
    """E-I de Krackhardt e Stern (1988) por grupo, comparado com o E-I ao embaralhar os grupos.

    Embaralhar mantém o tamanho de cada grupo e a rede intacta. ``p_valor`` = fração das permutações
    com E-I menor ou igual ao observado; ``externo_vs_acaso`` = fração das ligações externas que o grupo
    teria se as ligações ignorassem o grupo.
    """
    pares = _pares(adj_s)
    o_int, o_ext = ei_contagem(adj_s, grupo, ng, pares)
    o_tot = o_int + o_ext
    with np.errstate(invalid="ignore", divide="ignore"):
        o_ei = np.where(o_tot > 0, (o_ext - o_int) / o_tot, np.nan)
    rnd = mulberry32(semente)
    soma_ei = np.zeros(ng)
    soma_ext = np.zeros(ng)
    cont = np.zeros(ng)
    menores = np.zeros(ng)
    perm = list(grupo)
    for _ in range(permutacoes):
        embaralhar(perm, rnd)
        c_int, c_ext = ei_contagem(adj_s, perm, ng, pares)
        tot = c_int + c_ext
        ok = tot > 0
        with np.errstate(invalid="ignore", divide="ignore"):
            e = np.where(ok, (c_ext - c_int) / tot, 0.0)
            fe = np.where(ok, c_ext / tot, 0.0)
        soma_ei += np.where(ok, e, 0.0)
        soma_ext += fe
        cont += ok
        menores += ok & ~np.isnan(o_ei) & (e <= np.nan_to_num(o_ei, nan=-9) + _EPS)
    out = []
    for g in range(ng):
        ei = None if math.isnan(o_ei[g]) else float(o_ei[g])
        esp = float(soma_ei[g] / cont[g]) if cont[g] else None
        esp_ext = float(soma_ext[g] / cont[g]) if cont[g] else None
        out.append({
            "interno": int(o_int[g]), "externo": int(o_ext[g]), "ei": ei, "ei_esperado": esp,
            "p_valor": float((menores[g] + 1) / (cont[g] + 1)) if cont[g] else None,
            "externo_vs_acaso": float((o_ext[g] / o_tot[g]) / esp_ext) if o_tot[g] and esp_ext else None,
        })
    return out


def ei_esperado_formula(tamanho: int, total: int) -> float:
    """Fórmula fechada (todas as ligações igualmente prováveis): referência dos testes."""
    interno = tamanho * (tamanho - 1) / 2
    externo = tamanho * (total - tamanho)
    return (externo - interno) / (externo + interno)


# ---------------------------------------------------------------- papéis de corretagem


def papeis_corretagem(rede: Rede, grupo: Sequence) -> list[dict[str, int]]:
    """Gould e Fernandez (1989). A informação corre de quem é citado para quem cita.

    Para cada pessoa B e cada caminho A -> B -> C (B cita A, C cita B) sem C citar A direto:
    coordenador (A, B, C na mesma área), consultor (A e C juntas, B de fora), representante (A e B
    juntas, C de fora: B leva a informação para fora), porteiro (B e C juntas, A de fora: B traz
    informação de fora para dentro) e ligação (as três em áreas diferentes).
    """
    out = []
    for b in range(rede.n):
        c = dict.fromkeys(PAPEIS, 0)
        for a in rede.adj_out[b]:
            for d in rede.adj_in[b]:
                if a == d or a in rede.saida[d]:
                    continue
                ga, gb, gc = grupo[a], grupo[b], grupo[d]
                if ga == gb == gc:
                    c["coordenador"] += 1
                elif ga == gc:
                    c["consultor"] += 1
                elif ga == gb:
                    c["representante"] += 1
                elif gb == gc:
                    c["porteiro"] += 1
                else:
                    c["ligacao"] += 1
        out.append(c)
    return out


def papel_principal(contagens: list[dict[str, int]], grupo: Sequence) -> list[str | None]:
    """Papel principal de cada pessoa.

    1) quem concentra metade ou mais das entradas (porteiro) ou das saídas (representante) de
       informação da própria área, com 5 caminhos ou mais, recebe esse papel;
    2) senão, entre os 20% com mais corretagem entre áreas (mínimo 5 caminhos), vale o papel entre
       áreas mais frequente;
    3) quem só faz corretagem dentro da área (5 caminhos ou mais) é "coordenador".
    """
    fora = ["ligacao", "porteiro", "representante", "consultor"]
    tot = [c["consultor"] + c["representante"] + c["porteiro"] + c["ligacao"] for c in contagens]
    ordem = sorted(x for x in tot if x > 0)
    corte = max(5, ordem[math.floor(0.8 * (len(ordem) - 1))] if ordem else 0)
    ent: Counter = Counter()
    sai: Counter = Counter()
    for c, g in zip(contagens, grupo, strict=True):
        ent[g] += c["porteiro"]
        sai[g] += c["representante"]
    papeis: list[str | None] = []
    for i, c in enumerate(contagens):
        g = grupo[i]
        sp = c["porteiro"] / ent[g] if ent[g] else 0
        sr = c["representante"] / sai[g] if sai[g] else 0
        if c["porteiro"] >= 5 and sp >= 0.5 and sp >= sr:
            papeis.append("porteiro")
        elif c["representante"] >= 5 and sr >= 0.5:
            papeis.append("representante")
        elif tot[i] >= corte:
            melhor = fora[0]
            for p in fora:
                if c[p] > c[melhor]:
                    melhor = p
            papeis.append(melhor)
        else:
            papeis.append("coordenador" if c["coordenador"] >= 5 else None)
    return papeis


# ---------------------------------------------------------------- Burt e núcleo


def burt(rede: Rede) -> tuple[list[float | None], list[float]]:
    """Restrição e tamanho efetivo (Burt 1992), na rede simetrizada com pesos.

    Mesma fórmula de ``nx.constraint`` e ``nx.effective_size`` com ``weight``; os testes conferem a
    igualdade. A versão do networkx recalcula a normalização de cada vizinho a cada termo e leva uns
    10 s na base de exemplo; esta guarda as somas e leva milissegundos.
    """
    viz = rede.viz
    soma = [sum(v.values()) for v in viz]
    maximo = [max(v.values()) if v else 0 for v in viz]
    restr: list[float | None] = []
    efet: list[float] = []
    for i, vi in enumerate(viz):
        if not vi:
            restr.append(None)
            efet.append(0.0)
            continue
        p_i = {q: w / soma[i] for q, w in vi.items()}
        c = ef = 0.0
        for j in vi:
            vj = viz[j]
            indireto = redund = 0.0
            for q, piq in p_i.items():
                if q == j or j not in viz[q]:
                    continue
                indireto += piq * viz[q][j] / soma[q]
                redund += piq * vj[q] / maximo[j]
            c += (p_i[j] + indireto) ** 2
            ef += 1 - redund
        restr.append(c)
        efet.append(ef)
    return restr, efet


def nucleos(rede: Rede) -> list[int]:
    """k-core (Seidman 1983) pelo networkx."""
    c = nx.core_number(rede.G)
    return [int(c[i]) for i in range(rede.n)]


# ---------------------------------------------------------------- "e se essa pessoa sair?"


def estrutura_rede(rede: Rede, removidos: set[int] | None = None) -> dict:
    """Componentes, maior componente, eficiência global (Latora e Marchiori 2001) e distância média.

    A eficiência é a mesma de ``nx.global_efficiency`` (os testes conferem). Aqui ela sai do mesmo
    BFS que dá a distância média, sobre listas de vizinhos: a simulação roda a cada clique no app.
    """
    removidos = removidos or set()
    adj = rede.adj_s
    n = rede.n
    vivo = [i not in removidos for i in range(n)]
    comp = [-1] * n
    tam: list[int] = []
    for i in range(n):
        if comp[i] >= 0 or not vivo[i]:
            continue
        cid = len(tam)
        comp[i] = cid
        fila = [i]
        for v in fila:
            for w in adj[v]:
                if comp[w] < 0 and vivo[w]:
                    comp[w] = cid
                    fila.append(w)
        tam.append(len(fila))
    maior = 0
    for j, t in enumerate(tam):
        if t > tam[maior]:
            maior = j
    soma_inv = 0.0
    soma_d = pares = 0
    for i in range(n):
        if not vivo[i]:
            continue
        dist = {i: 0}
        fila = [i]
        for v in fila:
            dv = dist[v] + 1
            for w in adj[v]:
                if w not in dist and vivo[w]:
                    dist[w] = dv
                    fila.append(w)
                    soma_inv += 1 / dv
                    soma_d += dv
                    pares += 1
    nv = sum(vivo)
    return {
        "componente": comp, "componentes": sum(1 for t in tam if t > 1),
        "sozinhos": sum(1 for t in tam if t == 1),
        "maior_componente": tam[maior] if tam else 0, "id_maior": maior,
        "eficiencia": soma_inv / (nv * (nv - 1)) if nv > 1 else 0.0,
        "distancia_media": soma_d / pares if pares else 0.0,
    }


def efeito_saida(rede: Rede, base: dict, quem: Iterable[int]) -> dict:
    rem = set(quem)
    depois = estrutura_rede(rede, rem)
    perdem = [i for i in range(rede.n) if i not in rem and base["componente"][i] == base["id_maior"]
              and depois["componente"][i] != depois["id_maior"]]
    return {
        "perdem_caminho": perdem, "componentes": depois["componentes"],
        "maior_componente": depois["maior_componente"], "eficiencia": depois["eficiencia"],
        "queda_eficiencia": (base["eficiencia"] - depois["eficiencia"]) / base["eficiencia"] if base["eficiencia"] else 0.0,
        "distancia_media": depois["distancia_media"],
    }


# ---------------------------------------------------------------- auxiliares


def respondeu(p: dict) -> bool:
    v = str(p.get("respondeu", "") or "").strip()
    return not v or not _NAO.match(v)


def _chave(x: float) -> float:
    return round(x, 12)  # empates numéricos de ponto flutuante viram empates de verdade


def top_indices(v: Sequence[float], k: int, filtro: Callable[[int], bool] | None = None) -> list[int]:
    ids = [i for i in range(len(v)) if filtro is None or filtro(i)]
    return sorted(ids, key=lambda i: (-_chave(v[i]), i))[:k]


def spearman(a: Sequence[float], b: Sequence[float]) -> float:
    ra = pd.Series(a).rank(method="average").to_numpy() - 1
    rb = pd.Series(b).rank(method="average").to_numpy() - 1
    n = len(a)
    m = (n - 1) / 2
    sxy = float(((ra - m) * (rb - m)).sum())
    sxx = float(((ra - m) ** 2).sum())
    syy = float(((rb - m) ** 2).sum())
    return sxy / math.sqrt(sxx * syy) if sxx and syy else 1.0


def sobreposicao(a: Sequence, b: Sequence) -> float:
    if not a:
        return 1.0
    s = set(b)
    return sum(1 for x in a if x in s) / len(a)


# ---------------------------------------------------------------- sensibilidade à não resposta


def sensibilidade(pessoas: list[dict], ligacoes: list[dict], tipo: str, semente: int, base: dict) -> dict:
    """(1) dirigida x simetrizada; (2) mais 10% de não resposta, em vários sorteios.

    Em cada sorteio, apaga as citações feitas por mais 10% de quem respondeu e confere se pontes,
    isolados, E-I e silo se mantêm (Borgatti, Carley e Krackhardt 2006; Kossinets 2006).
    """
    n, resp = base["n"], base["resp"]
    rnd = mulberry32(semente + 101)
    replicas = 20 if n <= 300 else (10 if n <= 1000 else 5)
    ids_resp = [i for i in range(n) if resp[i]]
    cortar = max(1, _js_round(0.1 * len(ids_resp)))
    top_base = [i for i in top_indices(base["btw"], 5) if base["btw"][i] > 0]
    mantidas, isol, var_ei, qs = [], [], [], []
    silos_iguais = 0
    for r in range(replicas):
        sorteio = embaralhar(ids_resp.copy(), rnd)[:cortar]
        fora = {pessoas[i]["id"] for i in sorteio}
        g2 = Rede(pessoas, [l for l in ligacoes if l["origem_id"] not in fora], tipo)
        b2 = intermediacao(g2)
        mantidas.append(sobreposicao(top_base, top_indices(b2, 5)))
        isol.append(sum(1 for j in range(n) if not g2.adj_in[j] and len(g2.adj_s[j]) <= 1))
        i2, e2 = ei_contagem(g2.adj_s, base["grupo"], base["ng"])
        maxd = 0.0
        silos2 = []
        for gk in range(base["ng"]):
            tot = i2[gk] + e2[gk]
            ref = base["ei"][gk]
            if not tot or ref["ei"] is None:
                continue
            e = (e2[gk] - i2[gk]) / tot
            maxd = max(maxd, abs(e - ref["ei"]))
            esp = ref["ei_esperado"]
            esp_ext = None if esp is None else (esp + 1) / 2
            if not base["area_oculta"][gk] and esp_ext and (e2[gk] / tot) / esp_ext <= LIMIAR_SILO and e < esp:
                silos2.append(base["nomes_grupo"][gk])
        var_ei.append(float(maxd))
        if sorted(silos2) == base["silos"]:
            silos_iguais += 1
        qs.append(modularidade(g2, separar_desconexas(g2.adj_s, louvain(g2, semente + r))))
    top_dir = [i for i in top_indices(base["btw_dir"], 5) if base["btw_dir"][i] > 0]
    top10 = [i for i in top_indices(base["btw"], 10) if base["btw"][i] > 0]
    top10_dir = [i for i in top_indices(base["btw_dir"], 10) if base["btw_dir"][i] > 0]
    return {
        "replicas": replicas, "pessoas_retiradas": cortar,
        "pontes_mantidas": sum(mantidas) / len(mantidas), "pontes_mantidas_min": min(mantidas),
        "isolados_min": min(isol), "isolados_max": max(isol),
        "ei_variacao_media": sum(var_ei) / len(var_ei), "silo_estavel": silos_iguais / replicas,
        "modularidade_min": min(qs), "modularidade_max": max(qs),
        "dirigida_vs_simetrizada": {
            "top5_em_comum": sobreposicao(top_base, top_dir),
            "correlacao": spearman(base["btw"], base["btw_dir"]),
            "nao_respondentes_top10_simetrizada": sum(1 for i in top10 if not resp[i]),
            "nao_respondentes_top10_dirigida": sum(1 for i in top10_dir if not resp[i]),
        },
    }


def _js_round(x: float) -> int:
    """Math.round do JavaScript (meio arredonda para cima), não o arredondamento bancário do Python."""
    return math.floor(x + 0.5)


# ---------------------------------------------------------------- análise completa


class Resultado(dict):
    """O resultado da análise: um dicionário (vira JSON direto) com atalhos para tabelas."""

    rede: Rede
    base: dict

    def pessoas_df(self) -> pd.DataFrame:
        return pd.DataFrame(self["por_pessoa"])

    def areas_df(self) -> pd.DataFrame:
        return pd.DataFrame(self["areas"])

    def riscos_df(self) -> pd.DataFrame:
        return pd.DataFrame(self["riscos"])

    def json(self, **kw) -> str:
        return json.dumps(self, ensure_ascii=False, **kw)


def analisar(pessoas: pd.DataFrame | list[dict], ligacoes: pd.DataFrame | list[dict], *, tipo: str = "todos",
             rede: str = "simetrizada", semente: int = SEMENTE, permutacoes: int = PERMUTACOES_EI,
             execucoes: int | None = None, com_sensibilidade: bool = True) -> Resultado:
    """Roda a análise completa e devolve o resultado com os insights já escritos."""
    from .insights import confiabilidade, gerar_insights

    pes = _registros(pessoas, ["id", "area", "cargo", "gestor_id", "unidade", "respondeu"])
    lig = _registros(ligacoes, ["origem_id", "destino_id", "tipo", "peso"])
    g = Rede(pes, lig, tipo)
    pes = g.nos
    n = g.n
    grau_ent = [len(a) for a in g.adj_in]
    grau_sai = [len(a) for a in g.adj_out]
    grau_tot = [len(a) for a in g.adj_s]
    simetrica = rede != "dirigida"
    btw_sim = intermediacao(g)
    btw_dir = intermediacao(g, dirigida=True)
    btw = btw_sim if simetrica else btw_dir
    cm = comunidades_estaveis(g, semente, execucoes or (10 if n > 1500 else EXECUCOES_LOUVAIN))
    resp = [respondeu(p) for p in pes]
    n_resp = sum(resp)

    # reciprocidade: só entre pares em que as duas pessoas responderam
    pares = mutuos = 0
    for i in range(n):
        if not resp[i]:
            continue
        for d in g.adj_out[i]:
            if not resp[d]:
                continue
            if i in g.saida[d]:
                if i < d:
                    mutuos += 1
                    pares += 1
            else:
                pares += 1
    total_cit = sum(grau_ent)
    top_n = max(1, _js_round(n * 0.05))
    top_cit = sum(sorted(grau_ent, reverse=True)[:top_n])

    # isolados: ninguém cita e há no máximo uma ligação em qualquer sentido
    isolados = [i for i in range(n) if grau_ent[i] == 0 and grau_tot[i] <= 1]
    quase = [i for i in range(n) if not (grau_ent[i] == 0 and grau_tot[i] <= 1) and grau_tot[i] <= 2]

    # áreas
    nomes_grupo: list[str] = []
    grupo_de: dict[str, int] = {}
    grupo = []
    for p in pes:
        a = p.get("area") or "(sem área)"
        if a not in grupo_de:
            grupo_de[a] = len(nomes_grupo)
            nomes_grupo.append(a)
        grupo.append(grupo_de[a])
    ng = len(nomes_grupo)
    ei = ei_com_base(g.adj_s, grupo, ng, permutacoes, semente + 1)
    tam_grupo = Counter(grupo)
    resp_grupo = Counter(gk for gk, r in zip(grupo, resp, strict=True) if r)
    area_oculta = [tam_grupo[gk] < GRUPO_MINIMO for gk in range(ng)]

    gf = papeis_corretagem(g, grupo)
    papel = papel_principal(gf, grupo)
    restricao, tam_efetivo = burt(g)
    core = nucleos(g)
    nucleo_max = max(core + [0])

    areas = []
    for gk, nome in enumerate(nomes_grupo):
        x = ei[gk]
        membros = [j for j in range(n) if grupo[j] == gk]
        maior = max(Counter(cm["comunidade"][j] for j in membros).values())
        entradas = sum(gf[j]["porteiro"] for j in membros)
        saidas = sum(gf[j]["representante"] for j in membros)
        top_p = top_r = -1
        for j in membros:
            if top_p < 0 or gf[j]["porteiro"] > gf[top_p]["porteiro"]:
                top_p = j
            if top_r < 0 or gf[j]["representante"] > gf[top_r]["representante"]:
                top_r = j
        silo = (not area_oculta[gk] and x["ei"] is not None and x["p_valor"] is not None and x["p_valor"] < ALFA_SILO
                and x["externo_vs_acaso"] is not None and x["externo_vs_acaso"] <= LIMIAR_SILO)
        areas.append({
            "area": nome, "pessoas": tam_grupo[gk], "responderam": resp_grupo[gk],
            "taxa_resposta": resp_grupo[gk] / tam_grupo[gk],
            "interno": x["interno"], "externo": x["externo"], "ei": x["ei"], "ei_esperado": x["ei_esperado"],
            "p_valor": x["p_valor"], "externo_vs_acaso": x["externo_vs_acaso"], "silo": silo, "oculta": area_oculta[gk],
            "coesao": maior / tam_grupo[gk], "entradas_de_fora": entradas, "saidas_para_fora": saidas,
            "porteiro_principal": pes[top_p]["id"] if entradas else None,
            "porteiro_participacao": gf[top_p]["porteiro"] / entradas if entradas else 0,
            "representante_principal": pes[top_r]["id"] if saidas else None,
            "representante_participacao": gf[top_r]["representante"] / saidas if saidas else 0,
        })

    # gestor x time
    times: dict[str, list[int]] = {}
    for j, p in enumerate(pes):
        gid = p.get("gestor_id", "")
        if gid and gid in g.idx and g.idx[gid] != j:
            times.setdefault(gid, []).append(j)
    gestores = []
    for gid, time in times.items():
        gi = g.idx[gid]
        ligados = sum(1 for t in time if t in g.viz[gi])
        gestores.append({"gestor": gid, "area": pes[gi].get("area", ""), "time": len(time),
                         "ligados": ligados, "fracao": ligados / len(time)})

    # e se sair: as 10 maiores intermediações
    base = estrutura_rede(g)
    riscos = []
    for j in [j for j in top_indices(btw, 10) if btw[j] > 0]:
        ef = efeito_saida(g, base, [j])
        riscos.append({
            "id": pes[j]["id"], "area": pes[j].get("area", ""), "intermediacao": btw[j],
            "perdem_caminho": len(ef["perdem_caminho"]),
            "areas_afetadas": dict(Counter(pes[k].get("area", "") for k in ef["perdem_caminho"])),
            "componentes": ef["componentes"], "queda_eficiencia": ef["queda_eficiencia"],
            "distancia_media": ef["distancia_media"],
        })
    riscos.sort(key=lambda x: (-x["perdem_caminho"], -_chave(x["queda_eficiencia"])))

    por_pessoa = []
    for j, p in enumerate(pes):
        por_pessoa.append({
            "id": p["id"], "area": p.get("area", ""), "cargo": p.get("cargo", ""), "respondeu": resp[j],
            "citacoes_recebidas": grau_ent[j], "citacoes_feitas": grau_sai[j], "conexoes": grau_tot[j],
            "intermediacao": btw[j], "intermediacao_dirigida": btw_dir[j], "intermediacao_simetrizada": btw_sim[j],
            "restricao": restricao[j], "tamanho_efetivo": tam_efetivo[j], "nucleo": core[j],
            "comunidade": cm["comunidade"][j], "papel": papel[j], **gf[j],
        })
    pontes = [por_pessoa[j] for j in top_indices(btw, 5) if btw[j] > 0]
    tam_com = Counter(cm["comunidade"])
    n_lig = sum(grau_tot) // 2

    r = Resultado({
        "versao": 3, "pessoas": n, "ligacoes": n_lig, "citacoes": sum(grau_sai),
        "tipo": tipo, "rede": "simetrizada" if simetrica else "dirigida", "semente": semente,
        "taxa_resposta": n_resp / n if n else 0, "responderam": n_resp,
        "densidade": n_lig / (n * (n - 1) / 2) if n > 1 else 0,
        "reciprocidade": mutuos / pares if pares else 0,
        "concentracao_top5pct": top_cit / total_cit if total_cit else 0,
        "comunidades": sum(1 for c in tam_com.values() if c > 1), "comunidades_total": len(tam_com),
        "modularidade": cm["modularidade"], "estabilidade_comunidades": cm["estabilidade"],
        "execucoes_louvain": cm["execucoes"], "modularidade_faixa": [cm["modularidade_min"], cm["modularidade_max"]],
        "pedacos_separados": cm["pedacos_separados"],
        "eficiencia": base["eficiencia"], "distancia_media": base["distancia_media"],
        "maior_componente": base["maior_componente"], "componentes": base["componentes"],
        "nucleo_max": nucleo_max, "nucleo_pessoas": sum(1 for c in core if c == nucleo_max and nucleo_max > 0),
        "isolados": [por_pessoa[j] for j in isolados], "quase_isolados": [por_pessoa[j] for j in quase],
        "pontes": pontes, "riscos": riscos, "areas": areas, "gestores": gestores, "por_pessoa": por_pessoa,
    })
    if com_sensibilidade:
        r["sensibilidade"] = sensibilidade(pes, lig, tipo, semente, {
            "n": n, "resp": resp, "btw": btw_sim, "btw_dir": btw_dir, "grupo": grupo, "ng": ng, "ei": ei,
            "area_oculta": area_oculta, "nomes_grupo": nomes_grupo,
            "silos": sorted(a["area"] for a in areas if a["silo"]),
        })
    r["confiabilidade"] = confiabilidade(r)
    r["insights"] = gerar_insights(r)
    r.rede = g
    r.base = base
    return r


def simular_saida(r: Resultado, ids: Iterable[str]) -> dict:
    """Efeito de tirar uma ou mais pessoas (pelos ids) da rede já analisada."""
    ids = list(ids)
    g, base = r.rede, r.base
    quem = [g.idx[i] for i in ids if i in g.idx]
    ef = efeito_saida(g, base, quem)
    return {
        "ids": ids, "perdem_caminho": [r["por_pessoa"][k]["id"] for k in ef["perdem_caminho"]],
        "areas_afetadas": dict(Counter(r["por_pessoa"][k]["area"] for k in ef["perdem_caminho"])),
        "componentes": ef["componentes"], "componentes_antes": base["componentes"],
        "maior_componente": ef["maior_componente"], "eficiencia": ef["eficiencia"],
        "eficiencia_antes": base["eficiencia"], "queda_eficiencia": ef["queda_eficiencia"],
        "distancia_media": ef["distancia_media"], "distancia_media_antes": base["distancia_media"],
    }


def posicoes(r: Resultado, semente: int = 7) -> dict[str, tuple[float, float]] | None:
    """Layout de força (Fruchterman-Reingold do networkx) para desenhar a rede; None a partir de 500.

    O maior componente vai ao centro. Pedaços soltos e pessoas sem ligação ficam num anel em volta,
    em vez de serem empurrados para longe pelo algoritmo (o que achata o desenho).
    """
    g = r.rede
    if g.n >= LIMITE_DESENHO or g.n == 0:  # o layout denso do networkx vai até 499 sem scipy
        return None
    comps = sorted(nx.connected_components(g.G), key=lambda c: (-len(c), min(c)))
    principal = g.G.subgraph(comps[0])
    k = 1.4 / math.sqrt(max(len(principal), 1))
    pos = nx.spring_layout(principal, seed=semente, weight=None, k=k, iterations=200) if len(principal) > 1 else {
        next(iter(comps[0])): np.zeros(2)}
    centro = np.mean(np.array(list(pos.values())), axis=0)
    raio = max(float(np.max(np.linalg.norm(np.array(list(pos.values())) - centro, axis=1))), 0.5)
    resto = comps[1:]
    for j, comp in enumerate(resto):
        ang = 2 * math.pi * (j + 0.5) / max(len(resto), 1) + 0.35
        base = centro + 1.08 * raio * np.array([math.cos(ang), math.sin(ang)])
        nos = sorted(comp)
        for t, v in enumerate(nos):
            desloc = 0.06 * raio * np.array([math.cos(2 * math.pi * t / len(nos)), math.sin(2 * math.pi * t / len(nos))])
            pos[v] = base + (desloc if len(nos) > 1 else 0)
    return {g.nos[i]["id"]: (float(pos[i][0]), float(pos[i][1])) for i in range(g.n)}
