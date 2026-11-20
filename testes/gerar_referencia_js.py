"""Gera testes/referencia_js.json com o resultado do motor JavaScript (tag v1-javascript).

O motor JS saiu do main, mas a tag guarda a versão exata. Este script tira o arquivo da tag,
roda no Node com a base de exemplo e grava o JSON que o teste de paridade lê.

    python testes/gerar_referencia_js.py      # precisa de git e node
"""

import json
import subprocess
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TAG = "v1-javascript"

ROTEIRO = r"""
const fs = require("fs");
const ONA = require(process.argv[2]);
const base = process.argv[3];
const pessoas = ONA.lerCSV(fs.readFileSync(base + "/pessoas.csv", "utf8"));
const ligacoes = ONA.lerCSV(fs.readFileSync(base + "/ligacoes.csv", "utf8"));
const r = ONA.analisar(pessoas, ligacoes);
const saida = { ...r, simulacoes: {} };
for (const id of ["P088", "P036", "P069"]) saida.simulacoes[id] = ONA.simularSaida(r, [id]);
process.stdout.write(JSON.stringify(saida, null, 1));
"""


def main() -> None:
    motor = subprocess.run(["git", "show", f"{TAG}:web/ona-motor.js"], cwd=RAIZ, check=True,
                           capture_output=True, text=True).stdout
    with tempfile.TemporaryDirectory() as tmp:
        caminho = Path(tmp) / "ona-motor.js"
        caminho.write_text(motor, encoding="utf-8")
        roteiro = Path(tmp) / "referencia.js"
        roteiro.write_text(ROTEIRO, encoding="utf-8")
        saida = subprocess.run(["node", str(roteiro), str(caminho), str(RAIZ / "ona_de_bolso" / "exemplo")],
                               check=True, capture_output=True, text=True).stdout
    dados = json.loads(saida)
    dados["_origem"] = f"motor JavaScript da tag {TAG}, base ona_de_bolso/exemplo"
    destino = RAIZ / "testes" / "referencia_js.json"
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"ok: {destino.relative_to(RAIZ)} ({destino.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
