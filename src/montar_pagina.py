#!/usr/bin/env python3
"""Gera web/exemplo.js (base de exemplo embutida) e dist/ona-de-bolso.html (página num arquivo só,
que abre com duplo clique, sem servidor e sem internet).

Com --site <pasta>, copia também o motor, a interface e a base de exemplo para <pasta>
(usado para levar a mesma lógica ao site gleissonbispo.com.br)."""
import argparse
import json
import os
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ler(*p):
    with open(os.path.join(RAIZ, *p), encoding="utf-8") as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", help="pasta de destino para copiar motor, interface e exemplo")
    args = ap.parse_args()

    exemplo = "window.EXEMPLO = %s;\n" % json.dumps(
        {"pessoas": ler("dados", "exemplo", "pessoas.csv"), "ligacoes": ler("dados", "exemplo", "ligacoes.csv")},
        ensure_ascii=False)
    with open(os.path.join(RAIZ, "web", "exemplo.js"), "w", encoding="utf-8") as f:
        f.write(exemplo)

    html = ler("web", "ona.html")
    for nome, conteudo in (("ona-motor.js", ler("web", "ona-motor.js")), ("ona-ui.js", ler("web", "ona-ui.js")), ("exemplo.js", exemplo)):
        tag = '<script src="%s"></script>' % nome
        assert tag in html, tag
        html = html.replace(tag, "<script>\n%s</script>" % conteudo.replace("</script", "<\\/script"))
    os.makedirs(os.path.join(RAIZ, "dist"), exist_ok=True)
    destino = os.path.join(RAIZ, "dist", "ona-de-bolso.html")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(html)
    print("ok: %s (%d KB)" % (destino, os.path.getsize(destino) // 1024))

    if args.site:
        try:
            commit = subprocess.run(["git", "-C", RAIZ, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
        except OSError:
            commit = "?"
        nota = ("/* Copiado de github.com/gleissonbispo/ona-de-bolso (web/%s, commit %s) por src/montar_pagina.py.\n"
                " * Não edite aqui: altere no repositório e copie de novo. */\n")
        os.makedirs(args.site, exist_ok=True)
        for nome in ("ona-motor.js", "ona-ui.js", "exemplo.js"):
            with open(os.path.join(args.site, nome), "w", encoding="utf-8") as f:
                f.write(nota % (nome, commit) + ler("web", nome))
        print("ok: copiado para %s (commit %s)" % (args.site, commit))


if __name__ == "__main__":
    main()
