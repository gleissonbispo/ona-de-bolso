#!/usr/bin/env python3
"""Gera uma organização fictícia para testar a ONA de bolso.

Saída (em dados/exemplo/):
  pessoas.csv   id, area, cargo, gestor_id, unidade, respondeu
  ligacoes.csv  origem_id, destino_id, tipo, peso
  gabarito.json o que foi plantado de propósito, para conferir se a ferramenta acha

A base é sintética do começo ao fim (semente fixa, só biblioteca padrão).
Estrutura plantada:
  - 5 áreas com densidade interna alta e poucas ligações entre áreas;
  - 2 pontes: pessoas com muitas ligações para outras áreas;
  - 1 área em silo (Financeiro) sem ligações para fora, fora as do gestor;
  - isolados: pessoas que ninguém cita e que citam no máximo uma pessoa;
  - 1 gestor fora do fluxo do próprio time;
  - ~20% de não respondentes: recebem citações, mas não citam ninguém.
"""
import csv
import json
import os
import random

SEMENTE = 42
AREAS = {  # área: (tamanho, unidade)
    "Comercial": (30, "São Paulo"),
    "Operações": (34, "Campinas"),
    "Tecnologia": (22, "São Paulo"),
    "Financeiro": (16, "São Paulo"),
    "Gente e Gestão": (12, "São Paulo"),
}
TIPOS = ("informacao", "ajuda")
TAXA_NAO_RESPOSTA = 0.20
P_DENTRO = {"informacao": 0.22, "ajuda": 0.12}  # chance de citar um colega da própria área
P_FORA = 0.004  # chance de citar alguém de outra área (pessoa comum)


def main():
    rnd = random.Random(SEMENTE)
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    saida = os.path.join(raiz, "dados", "exemplo")
    os.makedirs(saida, exist_ok=True)

    pessoas, por_area, n = [], {}, 1
    for area, (tam, unidade) in AREAS.items():
        ids = ["P%03d" % (n + i) for i in range(tam)]
        n += tam
        por_area[area] = ids
        gestor = ids[0]
        for i, pid in enumerate(ids):
            cargo = "Gestor" if i == 0 else ("Especialista" if i <= 3 else "Analista")
            pessoas.append({"id": pid, "area": area, "cargo": cargo,
                            "gestor_id": "" if i == 0 else gestor, "unidade": unidade})
    area_de = {p["id"]: p["area"] for p in pessoas}
    todos = [p["id"] for p in pessoas]

    # Plantados
    pontes = [por_area["Operações"][5], por_area["Tecnologia"][4]]
    silo = "Financeiro"
    gestor_fora = por_area["Comercial"][0]
    isolados = [por_area["Operações"][-1], por_area["Comercial"][-1], por_area["Tecnologia"][-1]]

    # Não respondentes (nunca as pontes, para o exemplo ficar legível)
    candidatos = [p for p in todos if p not in pontes]
    nao_resp = set(rnd.sample(candidatos, round(TAXA_NAO_RESPOSTA * len(todos))))
    for p in pessoas:
        p["respondeu"] = "nao" if p["id"] in nao_resp else "sim"

    ligacoes = set()

    def liga(o, d, tipo):
        if o != d and o not in nao_resp:
            ligacoes.add((o, d, tipo))

    for o in todos:
        if o in isolados:
            continue
        for tipo in TIPOS:
            for d in todos:
                if d in isolados or d == o:
                    continue
                if o == gestor_fora and area_de[d] == "Comercial":
                    continue  # o gestor não cita o próprio time
                if d == gestor_fora and area_de[o] == "Comercial":
                    continue  # e o time não cita o gestor
                mesma = area_de[o] == area_de[d]
                if mesma:
                    p = P_DENTRO[tipo]
                elif silo in (area_de[o], area_de[d]):
                    p = 0.0  # Financeiro só fala para dentro
                else:
                    p = P_FORA
                if rnd.random() < p:
                    liga(o, d, tipo)

    # Pontes: muitas ligações nos dois sentidos com as outras áreas (menos o silo)
    for b in pontes:
        for area, ids in por_area.items():
            if area in (area_de[b], silo):
                continue
            for d in rnd.sample([x for x in ids if x not in isolados], 4):
                liga(b, d, "informacao")
                liga(d, b, "informacao")
                if rnd.random() < 0.5:
                    liga(d, b, "ajuda")

    # O silo só se conecta pelo gestor do Financeiro, com uma pessoa do Comercial
    gf = por_area[silo][0]
    liga(gf, por_area["Comercial"][2], "informacao")
    liga(por_area["Comercial"][2], gf, "informacao")

    # Isolados: cada um cita no máximo uma pessoa da própria área
    for iso in isolados:
        if rnd.random() < 0.7:
            liga(iso, rnd.choice([x for x in por_area[area_de[iso]] if x not in isolados]), "informacao")

    with open(os.path.join(saida, "pessoas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "area", "cargo", "gestor_id", "unidade", "respondeu"])
        w.writeheader()
        w.writerows(pessoas)
    with open(os.path.join(saida, "ligacoes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["origem_id", "destino_id", "tipo", "peso"])
        for o, d, t in sorted(ligacoes):
            w.writerow([o, d, t, rnd.randint(1, 5)])
    gab = {"semente": SEMENTE, "pessoas": len(pessoas), "ligacoes": len(ligacoes),
           "pares_ligados": len({(o, d) for o, d, _ in ligacoes}),
           "porteiros_do_silo": [gf, por_area["Comercial"][2]],
           "pontes": pontes, "silo": silo, "gestor_fora_do_fluxo": gestor_fora,
           "isolados": isolados, "nao_respondentes": len(nao_resp)}
    with open(os.path.join(saida, "gabarito.json"), "w", encoding="utf-8") as f:
        json.dump(gab, f, ensure_ascii=False, indent=2)
    print(json.dumps(gab, ensure_ascii=False))


if __name__ == "__main__":
    main()
