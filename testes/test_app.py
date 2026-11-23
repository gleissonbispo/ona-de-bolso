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


def _app_com_exemplo():
    at = st_testing.AppTest.from_file(APP, default_timeout=120).run()
    at.button[0].click().run()
    return at


def test_simular_a_saida_no_painel_da_pessoa_muda_a_simulacao():
    # Antes, o botão gravava outra chave e o multiselect da aba "E se sair" continuava em P088.
    at = _app_com_exemplo()
    saem = next(m for m in at.multiselect if m.key.startswith("saem_"))
    assert saem.value == ["P088"]
    at.selectbox(key="pessoa_sel").select("P036").run()
    at.button(key="simular_desta").click().run()
    assert not at.exception
    saem = next(m for m in at.multiselect if m.key.startswith("saem_"))
    assert saem.value == ["P036"]
    assert any("Sem P036" in m.value for m in at.markdown)


def test_aba_baixar_tem_o_resumo_para_o_gestor():
    at = _app_com_exemplo()
    textos = " ".join(m.value for m in at.markdown)
    assert "Resumo para o gestor" in textos
