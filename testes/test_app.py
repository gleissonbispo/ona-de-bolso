"""O app Streamlit importa e roda sem erro, com e sem a base de exemplo (AppTest, sem navegador)."""

from pathlib import Path

import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")

APP = str(Path(__file__).resolve().parent.parent / "app" / "app.py")


def test_app_abre_sem_dados():
    at = st_testing.AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert any("ONA de bolso" in t.value for t in at.title)


def test_app_com_a_base_de_exemplo():
    at = st_testing.AppTest.from_file(APP, default_timeout=120).run()
    at.button[0].click().run()
    assert not at.exception
    textos = " ".join(m.value for m in at.markdown)
    assert "Financeiro fala quase só para dentro" in textos
    assert "15 pessoas ficam sem nenhum caminho" in textos
