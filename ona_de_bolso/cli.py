"""Linha de comando: ``ona-de-bolso analisar pessoas.csv ligacoes.csv --saida relatorio.html``."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from . import __version__
from .insights import pct
from .io import converter_forms, ler_pessoas_ligacoes, ler_tabelas, para_csv, validar
from .metricas import analisar
from .relatorio import gerar_html, gerar_html_gestor


def _analisar(a: argparse.Namespace) -> int:
    try:
        pessoas, ligacoes = ler_pessoas_ligacoes(a.pessoas, a.ligacoes)
    except (OSError, ValueError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    erros, avisos = validar(pessoas, ligacoes)
    for e in erros:
        print(f"erro: {e}", file=sys.stderr)
    if erros:
        return 2
    for x in avisos:
        print(f"aviso: {x}")
    t0 = time.perf_counter()
    r = analisar(pessoas, ligacoes, tipo=a.tipo, rede=a.rede, semente=a.semente)
    ms = (time.perf_counter() - t0) * 1000
    fonte = " + ".join(Path(x).name for x in [a.pessoas, a.ligacoes] if x)
    Path(a.saida).write_text(gerar_html(r, titulo=a.titulo, fonte=fonte, incluir_pessoas=a.incluir_pessoas), encoding="utf-8")
    if a.gestor:
        Path(a.gestor).write_text(gerar_html_gestor(r, titulo=a.titulo, fonte=fonte), encoding="utf-8")
    if a.csv:
        Path(a.csv).write_bytes(para_csv(r.pessoas_df()))
    if a.json:
        Path(a.json).write_text(r.json(indent=1), encoding="utf-8")
    print(f"ok: {r['pessoas']} pessoas, {pct(r['taxa_resposta'])} de resposta, leitura {r['confiabilidade']['nivel']}, "
          f"{len(r['insights'])} insights em {ms:.0f} ms -> {a.saida}" + (f" e {a.gestor}" if a.gestor else ""))
    for i in r["insights"][:3]:
        print(f"  - {i['titulo']}")
    return 0


def _forms(a: argparse.Namespace) -> int:
    pessoas = next(iter(ler_tabelas(a.pessoas).values()))
    perguntas = {}
    for p in a.pergunta:
        tipo, _, titulo = p.partition("=")
        perguntas[tipo.strip()] = titulo
    try:
        res = converter_forms(a.respostas, pessoas, a.quem, perguntas)
    except ValueError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    Path(a.saida).write_bytes(para_csv(res.ligacoes))
    if a.marcar_respondeu:
        Path(a.marcar_respondeu).write_bytes(para_csv(res.pessoas))
    print(res.resumo() + f" em {a.saida}")
    return 0


def _exemplo(a: argparse.Namespace) -> int:
    origem = Path(__file__).parent / "exemplo"
    destino = Path(a.pasta)
    destino.mkdir(parents=True, exist_ok=True)
    for nome in ("pessoas.csv", "ligacoes.csv", "gabarito.json"):
        (destino / nome).write_bytes((origem / nome).read_bytes())
    print(f"ok: base de exemplo (114 pessoas, sintética) em {destino}")
    return 0


def montar_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="ona-de-bolso", description="Análise de rede organizacional (ONA) a partir de duas planilhas.")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = ap.add_subparsers(dest="comando", required=True)

    a = sub.add_parser("analisar", help="gera o relatório HTML (e, se pedir, o CSV e o JSON)")
    a.add_argument("pessoas", help="pessoas.csv, ou um .xlsx com as abas pessoas e ligacoes")
    a.add_argument("ligacoes", nargs="?", help="ligacoes.csv (dispensável se o .xlsx tiver as duas abas)")
    a.add_argument("--saida", default="relatorio.html")
    a.add_argument("--gestor", help="grava também o resumo de uma página para o gestor neste HTML")
    a.add_argument("--csv", help="grava as métricas por pessoa neste CSV")
    a.add_argument("--json", help="grava o resultado completo neste JSON")
    a.add_argument("--tipo", default="todos", help="só uma pergunta (ex.: informacao); padrão: todas")
    a.add_argument("--rede", choices=["simetrizada", "dirigida"], default="simetrizada")
    a.add_argument("--semente", type=int, default=20261116)
    a.add_argument("--titulo", default="Rede de colaboração")
    a.add_argument("--incluir-pessoas", action="store_true", help="inclui a tabela por pessoa no relatório (uso restrito)")
    a.set_defaults(func=_analisar)

    f = sub.add_parser("converter-forms", help="exportação do Google Forms ou Microsoft Forms -> ligacoes.csv")
    f.add_argument("respostas")
    f.add_argument("--pessoas", required=True, help="pessoas.csv com a coluna id")
    f.add_argument("--quem", required=True, help="início do título da coluna com o código de quem respondeu")
    f.add_argument("--pergunta", action="append", required=True, help='tipo="início do título da coluna"')
    f.add_argument("--saida", default="ligacoes.csv")
    f.add_argument("--marcar-respondeu", help="grava uma cópia de pessoas.csv com a coluna respondeu preenchida")
    f.set_defaults(func=_forms)

    e = sub.add_parser("exemplo", help="copia a base sintética de exemplo para uma pasta")
    e.add_argument("pasta", nargs="?", default="exemplo")
    e.set_defaults(func=_exemplo)
    return ap


def main(argv: list[str] | None = None) -> int:
    a = montar_parser().parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
