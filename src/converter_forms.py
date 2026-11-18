#!/usr/bin/env python3
"""Converte a exportação do Google Forms ou do Microsoft Forms na tabela ligacoes.csv da ONA de bolso.

O formulário tem uma linha por resposta e uma coluna por pergunta. Nas perguntas de nomeação
(caixas de seleção), cada opção traz o código da pessoa, por exemplo "Ana Souza (A001)".
O Google Forms junta as opções marcadas com vírgula; o Microsoft Forms, com ponto e vírgula.
O script procura, em cada resposta, os códigos que existem em pessoas.csv.

Uso:
  python3 src/converter_forms.py respostas.csv --pessoas pessoas.csv \\
      --quem "Seu código" \\
      --pergunta informacao="Com quem você trocou informação" \\
      --pergunta ajuda="A quem você pede ajuda" \\
      --saida ligacoes.csv --marcar-respondeu pessoas_atualizado.csv

Aceita .csv (vírgula ou ponto e vírgula) e .xlsx. O texto de --quem e de cada --pergunta pode ser
só o começo do título da coluna. Só biblioteca padrão.
"""
import argparse
import csv
import io
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def ler_tabela(caminho):
    if caminho.lower().endswith(".xlsx"):
        return ler_xlsx(caminho)
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        texto = f.read()
    sep = ";" if texto.split("\n", 1)[0].count(";") > texto.split("\n", 1)[0].count(",") else ","
    linhas = list(csv.reader(io.StringIO(texto), delimiter=sep))
    return linhas[0], linhas[1:]


def ler_xlsx(caminho):
    """Primeira aba de um .xlsx, sem dependências."""
    with zipfile.ZipFile(caminho) as z:
        comp = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                comp.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rid = wb.find("m:sheets/m:sheet", NS).get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        alvo = [r.get("Target") for r in rels if r.get("Id") == rid][0].lstrip("/").replace("xl/", "")
        folha = ET.fromstring(z.read("xl/" + alvo))
    linhas = []
    for row in folha.iter("{%s}row" % NS["m"]):
        l = []
        for c in row.findall("m:c", NS):
            col = 0
            for ch in re.match(r"[A-Z]+", c.get("r")).group(0):
                col = col * 26 + ord(ch) - 64
            while len(l) < col - 1:
                l.append("")
            t, v = c.get("t"), c.find("m:v", NS)
            if t == "s":
                val = comp[int(v.text)]
            elif t == "inlineStr":
                val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
            else:
                val = v.text if v is not None else ""
            l.append(val or "")
        linhas.append(l)
    return linhas[0], linhas[1:]


def coluna(cab, inicio):
    alvo = inicio.strip().lower()
    for i, c in enumerate(cab):
        if c.strip().lower().startswith(alvo):
            return i
    sys.exit("Coluna não encontrada: %r. Colunas do arquivo:\n- %s" % (inicio, "\n- ".join(cab)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("respostas")
    ap.add_argument("--pessoas", required=True, help="pessoas.csv com a coluna id")
    ap.add_argument("--quem", required=True, help="início do título da coluna com o código de quem respondeu")
    ap.add_argument("--pergunta", action="append", required=True, help='tipo="início do título da coluna"')
    ap.add_argument("--saida", default="ligacoes.csv")
    ap.add_argument("--marcar-respondeu", help="grava uma cópia de pessoas.csv com a coluna respondeu preenchida")
    a = ap.parse_args()

    with open(a.pessoas, encoding="utf-8-sig", newline="") as f:
        txt = f.read()
    sep = ";" if txt.split("\n", 1)[0].count(";") > txt.split("\n", 1)[0].count(",") else ","
    pessoas = list(csv.DictReader(io.StringIO(txt), delimiter=sep))
    ids = [p["id"].strip() for p in pessoas]
    padrao = re.compile(r"(?<![\w-])(%s)(?![\w-])" % "|".join(re.escape(i) for i in sorted(ids, key=len, reverse=True)))

    cab, linhas = ler_tabela(a.respostas)
    c_quem = coluna(cab, a.quem)
    perguntas = []
    for p in a.pergunta:
        tipo, _, titulo = p.partition("=")
        perguntas.append((tipo.strip(), coluna(cab, titulo)))

    ligacoes, responderam, sem_id, desconhecidos = set(), set(), 0, 0
    for l in linhas:
        quem = padrao.search(l[c_quem] if c_quem < len(l) else "")
        if not quem:
            sem_id += 1
            continue
        o = quem.group(1)
        responderam.add(o)
        for tipo, c in perguntas:
            resposta = l[c] if c < len(l) else ""
            achados = set(padrao.findall(resposta))
            partes = [x for x in re.split(r"[;\n]|,(?![^()]*\))", resposta) if x.strip()]
            desconhecidos += max(0, len(partes) - len(achados))
            for d in achados:
                if d != o:
                    ligacoes.add((o, d, tipo))

    with open(a.saida, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["origem_id", "destino_id", "tipo", "peso"])
        for o, d, t in sorted(ligacoes):
            w.writerow([o, d, t, 1])
    if a.marcar_respondeu:
        campos = list(pessoas[0].keys()) + ([] if "respondeu" in pessoas[0] else ["respondeu"])
        with open(a.marcar_respondeu, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            for p in pessoas:
                p["respondeu"] = "sim" if p["id"].strip() in responderam else "nao"
                w.writerow(p)
    print("ok: %d respostas, %d com código reconhecido, %d ligações em %s" % (len(linhas), len(responderam), len(ligacoes), a.saida))
    if sem_id:
        print("aviso: %d respostas sem código de quem respondeu foram ignoradas" % sem_id)
    if desconhecidos:
        print("aviso: %d nomes citados sem código conhecido foram ignorados" % desconhecidos)


if __name__ == "__main__":
    main()
