from pathlib import Path

from ona_de_bolso.cli import main

RAIZ = Path(__file__).resolve().parent.parent
EX = RAIZ / "ona_de_bolso" / "exemplo"


def test_analisar_gera_relatorio_csv_e_json(tmp_path, capsys):
    saida = tmp_path / "relatorio.html"
    codigo = main(["analisar", str(EX / "pessoas.csv"), str(EX / "ligacoes.csv"), "--saida", str(saida),
                   "--csv", str(tmp_path / "m.csv"), "--json", str(tmp_path / "r.json")])
    assert codigo == 0
    html = saida.read_text(encoding="utf-8")
    assert "Financeiro fala quase só para dentro" in html
    assert "<svg" in html and "http" not in html.split("<footer>")[0].replace("http-equiv", "")
    assert "Por pessoa" not in html  # ranking individual fica fora por padrão
    assert (tmp_path / "m.csv").read_bytes().startswith("﻿id,area".encode())
    assert "leitura cautela" in capsys.readouterr().out


def test_analisar_xlsx_com_duas_abas(tmp_path):
    assert main(["analisar", str(RAIZ / "questionario" / "modelo-ona.xlsx"), "--saida", str(tmp_path / "r.html")]) == 0


def test_erro_amigavel_sem_as_tabelas(tmp_path, capsys):
    f = tmp_path / "x.csv"
    f.write_text("a,b\n1,2\n", encoding="utf-8")
    assert main(["analisar", str(f), "--saida", str(tmp_path / "r.html")]) == 2
    assert "Não achei as duas tabelas" in capsys.readouterr().err


def test_converter_forms(tmp_path):
    forms = RAIZ / "testes" / "forms"
    assert main(["converter-forms", str(forms / "respostas-google.csv"), "--pessoas", str(forms / "pessoas.csv"),
                 "--quem", "Seu código", "--pergunta", "informacao=Com quem", "--pergunta", "ajuda=A quem",
                 "--saida", str(tmp_path / "l.csv"), "--marcar-respondeu", str(tmp_path / "p.csv")]) == 0
    assert len((tmp_path / "l.csv").read_text(encoding="utf-8-sig").strip().splitlines()) == 6
