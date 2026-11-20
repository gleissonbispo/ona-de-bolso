import json
from pathlib import Path

import pytest

import ona_de_bolso as ona

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ / "ona_de_bolso" / "exemplo"


@pytest.fixture(scope="session")
def base():
    return ona.exemplo()


@pytest.fixture(scope="session")
def gabarito():
    return json.loads((EXEMPLO / "gabarito.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def resultado(base):
    pessoas, ligacoes = base
    return ona.analisar(pessoas, ligacoes)


@pytest.fixture(scope="session")
def referencia_js():
    return json.loads((RAIZ / "testes" / "referencia_js.json").read_text(encoding="utf-8"))
