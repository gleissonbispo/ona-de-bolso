#!/usr/bin/env python3
"""Teste do conversor de Forms (python3 testes/teste_converter.py)."""
import csv
import os
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)

with tempfile.TemporaryDirectory() as tmp:
    lig, pes = os.path.join(tmp, "ligacoes.csv"), os.path.join(tmp, "pessoas.csv")
    subprocess.run([sys.executable, os.path.join(RAIZ, "src", "converter_forms.py"), os.path.join(AQUI, "forms", "respostas-google.csv"),
                    "--pessoas", os.path.join(AQUI, "forms", "pessoas.csv"), "--quem", "Seu código",
                    "--pergunta", "informacao=Com quem", "--pergunta", "ajuda=A quem",
                    "--saida", lig, "--marcar-respondeu", pes], check=True)
    ligacoes = {(r["origem_id"], r["destino_id"], r["tipo"]) for r in csv.DictReader(open(lig, encoding="utf-8"))}
    esperado = {("A002", "A001", "informacao"), ("A002", "B002", "informacao"), ("A002", "B002", "ajuda"),
                ("B002", "A002", "informacao"), ("B002", "B001", "informacao")}
    respondeu = {r["id"]: r["respondeu"] for r in csv.DictReader(open(pes, encoding="utf-8"))}
    ok = ligacoes == esperado and respondeu == {"A001": "nao", "A002": "sim", "B001": "nao", "B002": "sim"}
    print(("ok    " if ok else "FALHOU") + "  conversor lê vírgula (Google) e ponto e vírgula (Microsoft) e marca quem respondeu")
    sys.exit(0 if ok else 1)
