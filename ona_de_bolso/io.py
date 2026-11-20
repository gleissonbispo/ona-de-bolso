"""Leitura das planilhas, validação e conversor do Google Forms e do Microsoft Forms.

Tudo aqui usa só a biblioteca padrão e o pandas. O leitor de ``.xlsx`` é próprio (zip + XML),
para não depender do openpyxl, que não vem no Pyodide usado pela demonstração no navegador.

Formato esperado:

- pessoas: ``id, area, cargo, gestor_id, unidade, respondeu`` (só ``id`` e ``area`` são obrigatórias);
- ligações: ``origem_id, destino_id, tipo, peso`` (origem cita destino; ``tipo`` e ``peso`` opcionais).
"""

from __future__ import annotations

import csv
import io as _io
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
_PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"

COLUNAS_PESSOAS = ["id", "area", "cargo", "gestor_id", "unidade", "respondeu"]
COLUNAS_LIGACOES = ["origem_id", "destino_id", "tipo", "peso"]


# ---------------------------------------------------------------- leitura


def normalizar_cabecalho(h: object) -> str:
    """'Área ' -> 'area'; 'Gestor ID' -> 'gestor_id'."""
    t = unicodedata.normalize("NFD", str(h or "").strip().lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", "_", t)


def _de_linhas(linhas: list[list[str]]) -> pd.DataFrame:
    """Matriz (primeira linha = cabeçalho) -> DataFrame de texto, sem linhas vazias."""
    linhas = [l for l in linhas if any(str(x).strip() for x in l)]
    if not linhas:
        return pd.DataFrame()
    cab = [normalizar_cabecalho(h) for h in linhas[0]]
    corpo = [[str(l[j]).strip() if j < len(l) and l[j] is not None else "" for j in range(len(cab))]
             for l in linhas[1:]]
    return pd.DataFrame(corpo, columns=cab, dtype=str)


def _separador(primeira: str) -> str:
    v, pv, tab = primeira.count(","), primeira.count(";"), primeira.count("\t")
    if pv > v:
        return ";"
    if tab > v:
        return "\t"
    return ","


def ler_csv_texto(texto: str) -> list[list[str]]:
    texto = texto.lstrip("﻿")
    sep = _separador(texto.split("\n", 1)[0])
    return list(csv.reader(_io.StringIO(texto), delimiter=sep))


def _texto(dados: bytes) -> str:
    for cod in ("utf-8-sig", "cp1252"):
        try:
            return dados.decode(cod)
        except UnicodeDecodeError:
            continue
    return dados.decode("latin-1")


def ler_xlsx(dados: bytes) -> dict[str, list[list[str]]]:
    """Todas as abas de um .xlsx -> {nome da aba: matriz de texto}. Sem dependências."""
    with zipfile.ZipFile(_io.BytesIO(dados)) as z:
        nomes = {n.lower(): n for n in z.namelist()}

        def ler(nome: str) -> bytes | None:
            n = nomes.get(nome.lower())
            return z.read(n) if n else None

        comp: list[str] = []
        ss = ler("xl/sharedStrings.xml")
        if ss:
            for si in ET.fromstring(ss).findall("m:si", NS):
                comp.append("".join(t.text or "" for t in si.iter("{{{}}}t".format(NS["m"]))))
        wb = ET.fromstring(ler("xl/workbook.xml") or b"")
        rels = ET.fromstring(ler("xl/_rels/workbook.xml.rels") or b"")
        alvo = {r.get("Id"): r.get("Target") for r in rels.iter(_PKG + "Relationship")}
        abas: dict[str, list[list[str]]] = {}
        for s in wb.iter("{{{}}}sheet".format(NS["m"])):
            t = (alvo.get(s.get(_REL)) or "").lstrip("/")
            caminho = t if t.startswith("xl/") else "xl/" + t
            xml = ler(caminho)
            abas[s.get("name") or caminho] = _linhas_da_aba(xml, comp) if xml else []
    return abas


def _linhas_da_aba(xml: bytes, comp: list[str]) -> list[list[str]]:
    linhas = []
    for row in ET.fromstring(xml).iter("{{{}}}row".format(NS["m"])):
        lin: list[str] = []
        for c in row.findall("m:c", NS):
            ref = c.get("r") or ""
            m = re.match(r"[A-Z]+", ref)
            col = 0
            for ch in m.group(0) if m else "":
                col = col * 26 + ord(ch) - 64
            while col and len(lin) < col - 1:
                lin.append("")
            tipo, v = c.get("t"), c.find("m:v", NS)
            if tipo == "s" and v is not None:
                val = comp[int(v.text or 0)]
            elif tipo == "inlineStr":
                val = "".join(x.text or "" for x in c.iter("{{{}}}t".format(NS["m"])))
            else:
                val = v.text if v is not None and v.text else ""
                if tipo != "str" and re.fullmatch(r"-?\d+\.0", val):
                    val = val[:-2]  # número inteiro gravado como 4.0
            lin.append(val)
        linhas.append(lin)
    return linhas


def ler_tabelas(fonte: str | Path | bytes, nome: str | None = None) -> dict[str, pd.DataFrame]:
    """Lê um CSV ou um XLSX (caminho ou bytes) e devolve {nome: DataFrame} (uma por aba)."""
    if isinstance(fonte, (str, Path)):
        nome = nome or Path(fonte).name
        dados = Path(fonte).read_bytes()
    else:
        dados = fonte
        nome = nome or "arquivo"
    if dados[:2] == b"PK" or nome.lower().endswith(".xlsx"):
        return {f"{nome} · aba {aba}": _de_linhas(l) for aba, l in ler_xlsx(dados).items()}
    return {nome: _de_linhas(ler_csv_texto(_texto(dados)))}


def classificar(df: pd.DataFrame) -> str | None:
    """'ligacoes' se tem origem_id e destino_id; 'pessoas' se tem id; senão None."""
    if df.empty:
        return None
    cols = set(df.columns)
    if {"origem_id", "destino_id"} <= cols:
        return "ligacoes"
    if "id" in cols:
        return "pessoas"
    return None


@dataclass
class Entrada:
    pessoas: pd.DataFrame | None = None
    ligacoes: pd.DataFrame | None = None
    nomes: dict[str, str] = field(default_factory=dict)

    @property
    def completa(self) -> bool:
        return self.pessoas is not None and self.ligacoes is not None


def ler_entrada(arquivos: list[tuple[str, bytes]]) -> Entrada:
    """Recebe arquivos soltos (dois CSV, um XLSX com duas abas...) e acha qual tabela é qual."""
    ent = Entrada()
    for nome, dados in arquivos:
        for rotulo, df in ler_tabelas(dados, nome).items():
            tipo = classificar(df)
            if tipo and getattr(ent, tipo) is None:
                setattr(ent, tipo, df)
                ent.nomes[tipo] = rotulo
    return ent


def ler_pessoas_ligacoes(pessoas: str | Path, ligacoes: str | Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Atalho para scripts e CLI: dois CSV/XLSX, ou um XLSX com as duas abas."""
    arquivos = [(Path(pessoas).name, Path(pessoas).read_bytes())]
    if ligacoes:
        arquivos.append((Path(ligacoes).name, Path(ligacoes).read_bytes()))
    ent = ler_entrada(arquivos)
    if not ent.completa:
        raise ValueError("Não achei as duas tabelas. A de pessoas precisa da coluna id; "
                         "a de ligações, de origem_id e destino_id.")
    return ent.pessoas, ent.ligacoes


def exemplo() -> tuple[pd.DataFrame, pd.DataFrame]:
    """A base sintética de 114 pessoas que acompanha o pacote."""
    pasta = Path(__file__).parent / "exemplo"
    return ler_pessoas_ligacoes(pasta / "pessoas.csv", pasta / "ligacoes.csv")


# ---------------------------------------------------------------- validação


def validar(pessoas: pd.DataFrame, ligacoes: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Devolve (erros, avisos). Com erro, a análise não roda."""
    erros: list[str] = []
    avisos: list[str] = []
    if pessoas is None or pessoas.empty:
        erros.append("A tabela de pessoas está vazia.")
    else:
        if "id" not in pessoas.columns:
            erros.append("A tabela de pessoas precisa da coluna id.")
        if "area" not in pessoas.columns:
            erros.append("A tabela de pessoas precisa da coluna area.")
    if ligacoes is None or ligacoes.empty:
        erros.append("A tabela de ligações está vazia.")
    elif not {"origem_id", "destino_id"} <= set(ligacoes.columns):
        erros.append("A tabela de ligações precisa das colunas origem_id e destino_id.")
    if erros:
        return erros, avisos
    ids = pessoas["id"].astype(str).str.strip()
    vazios = int((ids == "").sum())
    if vazios:
        avisos.append(f"{vazios} linhas da tabela de pessoas estão sem id e foram ignoradas.")
    dup = int(ids[ids != ""].duplicated().sum())
    if dup:
        avisos.append(f"{dup} ids repetidos na tabela de pessoas; valeu a primeira linha de cada um.")
    conhecidos = set(ids[ids != ""])
    o = ligacoes["origem_id"].astype(str).str.strip()
    d = ligacoes["destino_id"].astype(str).str.strip()
    fora = int((~o.isin(conhecidos) | ~d.isin(conhecidos)).sum())
    auto = int((o.isin(conhecidos) & d.isin(conhecidos) & (o == d)).sum())
    if fora:
        avisos.append(f"{fora} ligações citam ids que não estão na tabela de pessoas e foram ignoradas.")
    if auto:
        avisos.append(f"{auto} ligações de uma pessoa com ela mesma foram ignoradas.")
    if "respondeu" not in pessoas.columns:
        avisos.append("Sem a coluna respondeu, a análise considera que todo mundo respondeu.")
    return erros, avisos


# ---------------------------------------------------------------- modelos


def modelo_pessoas() -> pd.DataFrame:
    return pd.DataFrame([
        ["A001", "Comercial", "Gestor", "", "São Paulo", "sim"],
        ["A002", "Comercial", "Analista", "A001", "São Paulo", "sim"],
        ["A003", "Comercial", "Analista", "A001", "Campinas", "nao"],
        ["B001", "Operações", "Gestor", "", "Campinas", "sim"],
        ["B002", "Operações", "Especialista", "B001", "Campinas", "sim"],
    ], columns=COLUNAS_PESSOAS)


def modelo_ligacoes() -> pd.DataFrame:
    return pd.DataFrame([
        ["A002", "A001", "informacao", "4"],
        ["A002", "B002", "informacao", "2"],
        ["A002", "B002", "ajuda", "3"],
        ["B002", "B001", "informacao", "5"],
        ["A001", "B001", "informacao", "3"],
    ], columns=COLUNAS_LIGACOES)


# ---------------------------------------------------------------- conversor de Forms


def _coluna(cab: list[str], inicio: str) -> int:
    alvo = inicio.strip().lower()
    for i, c in enumerate(cab):
        if c.strip().lower().startswith(alvo):
            return i
    raise ValueError("Coluna não encontrada: {!r}. Colunas do arquivo:\n- {}".format(inicio, "\n- ".join(cab)))


@dataclass
class ResultadoForms:
    ligacoes: pd.DataFrame
    pessoas: pd.DataFrame
    respostas: int
    reconhecidas: int
    sem_codigo: int
    nomes_desconhecidos: int

    def resumo(self) -> str:
        linhas = [f"ok: {self.respostas} respostas, {self.reconhecidas} com código reconhecido, "
                  f"{len(self.ligacoes)} ligações"]
        if self.sem_codigo:
            linhas.append(f"aviso: {self.sem_codigo} respostas sem código de quem respondeu foram ignoradas")
        if self.nomes_desconhecidos:
            linhas.append(f"aviso: {self.nomes_desconhecidos} nomes citados sem código conhecido foram ignorados")
        return "\n".join(linhas)


def converter_forms(respostas: str | Path | bytes, pessoas: pd.DataFrame, quem: str,
                    perguntas: dict[str, str], nome: str | None = None) -> ResultadoForms:
    """Exportação do Google Forms ou do Microsoft Forms -> tabela de ligações.

    Cada opção das perguntas de nomeação traz o código da pessoa, como "Ana Souza (A001)".
    O Google junta as opções marcadas com vírgula; o Microsoft, com ponto e vírgula.
    ``quem`` e cada valor de ``perguntas`` ({tipo: início do título da coluna}) podem ser só o começo
    do título. Devolve também a tabela de pessoas com a coluna ``respondeu`` preenchida.
    """
    if isinstance(respostas, (str, Path)):
        nome = nome or Path(respostas).name
        dados = Path(respostas).read_bytes()
    else:
        dados = respostas
    if dados[:2] == b"PK" or (nome or "").lower().endswith(".xlsx"):
        matriz = next(iter(ler_xlsx(dados).values()))  # primeira aba
    else:
        matriz = ler_csv_texto(_texto(dados))
    cab, linhas = matriz[0], matriz[1:]
    ids = [str(i).strip() for i in pessoas["id"]]
    padrao = re.compile(r"(?<![\w-])({})(?![\w-])".format("|".join(re.escape(i) for i in sorted(ids, key=len, reverse=True))))
    c_quem = _coluna(cab, quem)
    cols = [(tipo, _coluna(cab, titulo)) for tipo, titulo in perguntas.items()]

    ligacoes: set[tuple[str, str, str]] = set()
    responderam: set[str] = set()
    sem_id = desconhecidos = 0
    for lin in linhas:
        achado = padrao.search(lin[c_quem] if c_quem < len(lin) else "")
        if not achado:
            sem_id += 1
            continue
        o = achado.group(1)
        responderam.add(o)
        for tipo, c in cols:
            resposta = lin[c] if c < len(lin) else ""
            achados = set(padrao.findall(resposta))
            partes = [x for x in re.split(r"[;\n]|,(?![^()]*\))", resposta) if x.strip()]
            desconhecidos += max(0, len(partes) - len(achados))
            for d in achados:
                if d != o:
                    ligacoes.add((o, d, tipo))

    lig = pd.DataFrame([[o, d, t, "1"] for o, d, t in sorted(ligacoes)], columns=COLUNAS_LIGACOES)
    pes = pessoas.copy()
    pes["respondeu"] = ["sim" if i in responderam else "nao" for i in ids]
    return ResultadoForms(lig, pes, len(linhas), len(responderam), sem_id, desconhecidos)


def para_csv(df: pd.DataFrame) -> bytes:
    """CSV em UTF-8 com BOM (o Excel abre com acento certo)."""
    return ("﻿" + df.to_csv(index=False, lineterminator="\n")).encode("utf-8")
