"""Leitura de CSV e XLSX, validação e conversor do Google Forms e do Microsoft Forms."""

from pathlib import Path

import pandas as pd

from ona_de_bolso import io

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent


def test_csv_com_ponto_e_virgula_bom_e_cabecalho_com_acento():
    dados = "﻿ID;Área;Gestor ID\nA1;Vendas;\nA2;Vendas;A1\n".encode()
    df = next(iter(io.ler_tabelas(dados, "x.csv").values()))
    assert list(df.columns) == ["id", "area", "gestor_id"]
    assert df["area"].tolist() == ["Vendas", "Vendas"]


def test_csv_em_cp1252():
    dados = "id,area\nA1,Operações\n".encode("cp1252")
    df = next(iter(io.ler_tabelas(dados, "x.csv").values()))
    assert df.loc[0, "area"] == "Operações"


def test_xlsx_modelo_com_duas_abas():
    ent = io.ler_entrada([("modelo-ona.xlsx", (RAIZ / "questionario" / "modelo-ona.xlsx").read_bytes())])
    assert ent.completa
    assert len(ent.pessoas) == 5 and len(ent.ligacoes) == 5
    assert "aba pessoas" in ent.nomes["pessoas"]


def test_dois_csv_em_qualquer_ordem():
    ex = RAIZ / "ona_de_bolso" / "exemplo"
    ent = io.ler_entrada([("l.csv", (ex / "ligacoes.csv").read_bytes()), ("p.csv", (ex / "pessoas.csv").read_bytes())])
    assert ent.completa and len(ent.pessoas) == 114


def test_validacao_aponta_colunas_que_faltam():
    erros, _ = io.validar(pd.DataFrame({"codigo": ["a"]}), pd.DataFrame({"de": ["a"], "para": ["b"]}))
    assert any("coluna id" in e for e in erros)
    assert any("origem_id" in e for e in erros)


def test_validacao_avisa_ids_desconhecidos_repetidos_e_autocitacao():
    p = pd.DataFrame({"id": ["A", "B", "B"], "area": ["X", "X", "X"]})
    l = pd.DataFrame({"origem_id": ["A", "A", "Z"], "destino_id": ["A", "B", "A"]})
    erros, avisos = io.validar(p, l)
    assert not erros
    texto = " ".join(avisos)
    assert "1 ids repetidos" in texto and "1 ligações citam ids" in texto and "1 ligações de uma pessoa com ela mesma" in texto
    assert "respondeu" in texto


def test_conversor_le_virgula_do_google_e_ponto_e_virgula_do_microsoft():
    pessoas = next(iter(io.ler_tabelas(AQUI / "forms" / "pessoas.csv").values()))
    res = io.converter_forms(AQUI / "forms" / "respostas-google.csv", pessoas, "Seu código",
                             {"informacao": "Com quem", "ajuda": "A quem"})
    lig = {tuple(x) for x in res.ligacoes[["origem_id", "destino_id", "tipo"]].values}
    assert lig == {("A002", "A001", "informacao"), ("A002", "B002", "informacao"), ("A002", "B002", "ajuda"),
                   ("B002", "A002", "informacao"), ("B002", "B001", "informacao")}
    respondeu = dict(zip(res.pessoas["id"], res.pessoas["respondeu"], strict=True))
    assert respondeu == {"A001": "nao", "A002": "sim", "B001": "nao", "B002": "sim"}


def test_csv_de_saida_abre_no_excel_com_acento():
    b = io.para_csv(pd.DataFrame({"area": ["Operações"]}))
    assert b.startswith("﻿".encode()) and "Operações".encode() in b
