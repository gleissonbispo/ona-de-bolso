#!/usr/bin/env python3
"""Gera web/exemplo.js (base de exemplo embutida) e dist/ona-de-bolso.html (página num arquivo só,
que abre com duplo clique, sem servidor e sem internet)."""
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ler(*p):
    with open(os.path.join(RAIZ, *p), encoding="utf-8") as f:
        return f.read()


def main():
    exemplo = "window.EXEMPLO = %s;\n" % json.dumps(
        {"pessoas": ler("dados", "exemplo", "pessoas.csv"), "ligacoes": ler("dados", "exemplo", "ligacoes.csv")},
        ensure_ascii=False)
    with open(os.path.join(RAIZ, "web", "exemplo.js"), "w", encoding="utf-8") as f:
        f.write(exemplo)

    html = ler("web", "ona.html")
    html = html.replace('<script src="ona-motor.js"></script>', "<script>\n%s\n</script>" % ler("web", "ona-motor.js"))
    html = html.replace('<script src="exemplo.js"></script>', "<script>\n%s</script>" % exemplo)
    os.makedirs(os.path.join(RAIZ, "dist"), exist_ok=True)
    destino = os.path.join(RAIZ, "dist", "ona-de-bolso.html")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(html)
    print("ok: %s (%d KB)" % (destino, os.path.getsize(destino) // 1024))


if __name__ == "__main__":
    main()
