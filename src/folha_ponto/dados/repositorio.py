"""Repositório SQLite: o único lugar do app que fala SQL.

Guarda lançamentos (UC01, UC02, UC04), datas do calendário (UC06, UC10) e
preferências (UC11). Também implementa a porta `Calendario` do domínio.
"""

from __future__ import annotations

import calendar
import json
import os
import sqlite3
import threading
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, time
from enum import StrEnum
from pathlib import Path

from folha_ponto.dados.esquema import migrar
from folha_ponto.dominio import (
    DataEspecial,
    Jornada,
    Lancamento,
    Marcacao,
    Marcacoes,
    Natureza,
    TipoDia,
    escrever_horario,
    ler_horario,
)
from folha_ponto.dominio.preferencias import Preferencias

ARQUIVO_DO_BANCO = "folha_de_ponto.db"


def caminho_do_banco() -> Path:
    """Onde fica o banco: FOLHA_PONTO_DB > pasta de dados do Flet (no celular) > ~/.local/share."""
    if explicito := os.environ.get("FOLHA_PONTO_DB"):
        return Path(explicito)
    if flet := os.environ.get("FLET_APP_STORAGE_DATA"):
        return Path(flet) / ARQUIVO_DO_BANCO
    base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "folha-ponto" / ARQUIVO_DO_BANCO


class Origem(StrEnum):
    """De onde veio uma data do calendário (RN09)."""

    NACIONAL = "nacional"
    ESTADUAL = "estadual"
    FACULTATIVO = "facultativo"
    REGRA_EMENDA = "regra_emenda"   # sugestão calculada pela RN05
    MANUAL = "manual"               # cadastrada pelo usuário (UC10) ou emenda confirmada (UC03)

    @property
    def automatica(self) -> bool:
        return self is not Origem.MANUAL


@dataclass(frozen=True)
class DataDoCalendario:
    data: date
    nome: str
    natureza: Natureza
    origem: Origem
    recorrente: bool = False
    oculta: bool = False
    fonte: str = ""

    @property
    def especial(self) -> DataEspecial:
        return DataEspecial(self.nome, self.natureza)


@dataclass(frozen=True)
class Carimbos:
    criado_em: datetime
    atualizado_em: datetime


@dataclass(frozen=True)
class LancamentoCarimbado:
    lancamento: Lancamento
    carimbos: Carimbos


@dataclass(frozen=True)
class Instantaneo:
    """Tudo o que é do usuário (UC09): lançamentos com carimbos, datas manuais (UC10,
    emendas confirmadas), datas da lib que ele ocultou e preferências. O calendário
    automático fica de fora: é refeito pela lib (UC06)."""

    lancamentos: tuple[LancamentoCarimbado, ...]
    datas_manuais: tuple[DataDoCalendario, ...]
    datas_ocultas: tuple[DataDoCalendario, ...]
    preferencias: Preferencias


@dataclass(frozen=True)
class ResultadoDaImportacao:
    lancamentos_gravados: int
    lancamentos_mantidos: int     # mesclar: o do aparelho era mais recente
    datas_manuais: int
    datas_ocultas: int


# Quando uma data tem mais de uma marca, vale a mais forte.
_PRECEDENCIA = {Natureza.FERIADO: 0, Natureza.EMENDA: 1, Natureza.FACULTATIVO: 2, Natureza.EMENDA_SUGERIDA: 3}


class CalendarioDoMes:
    """Implementação da porta `Calendario` para um intervalo já carregado (uma consulta por mês)."""

    def __init__(self, datas: Iterable[DataDoCalendario]) -> None:
        self._por_dia: dict[date, DataEspecial] = {}
        for d in sorted(datas, key=lambda d: _PRECEDENCIA[d.natureza], reverse=True):
            if not d.oculta:
                self._por_dia[d.data] = d.especial  # a de maior precedência sobrescreve

    def data_especial(self, dia: date) -> DataEspecial | None:
        return self._por_dia.get(dia)


def _agora() -> datetime:
    return datetime.now().astimezone().replace(microsecond=0)


class Repositorio:
    def __init__(self, caminho: str | Path | None = None, relogio: Callable[[], datetime] = _agora) -> None:
        destino = ":memory:" if caminho == ":memory:" else Path(caminho or caminho_do_banco())
        if isinstance(destino, Path):
            destino.parent.mkdir(parents=True, exist_ok=True)
        # O Flet chama os eventos em threads diferentes; o lock serializa o acesso.
        self._conexao = sqlite3.connect(destino, check_same_thread=False, isolation_level=None)
        self._conexao.row_factory = sqlite3.Row
        self._trava = threading.RLock()
        self._relogio = relogio
        self.versao = migrar(self._conexao)

    # ---- infraestrutura -----------------------------------------------------
    def fechar(self) -> None:
        self._conexao.close()

    def __enter__(self) -> Repositorio:
        return self

    def __exit__(self, *_exc) -> None:
        self.fechar()

    def _ler(self, sql: str, parametros: Iterable = ()) -> list[sqlite3.Row]:
        with self._trava:
            return self._conexao.execute(sql, tuple(parametros)).fetchall()

    def _transacao(self, comandos: Callable[[sqlite3.Connection], object]) -> object:
        with self._trava:
            self._conexao.execute("BEGIN IMMEDIATE")
            try:
                resultado = comandos(self._conexao)
            except BaseException:
                self._conexao.execute("ROLLBACK")
                raise
            self._conexao.execute("COMMIT")
            return resultado

    # ---- lançamentos ----------------------------------------------------------
    def obter(self, dia: date) -> Lancamento | None:
        linhas = self._ler("SELECT * FROM lancamentos WHERE data = ?", [dia.isoformat()])
        return _lancamento_de(linhas[0]) if linhas else None

    def listar_mes(self, ano: int, mes: int) -> list[Lancamento]:
        prefixo = f"{ano:04d}-{mes:02d}-"
        linhas = self._ler("SELECT * FROM lancamentos WHERE data LIKE ? ORDER BY data", [prefixo + "%"])
        return [_lancamento_de(l) for l in linhas]

    def carimbos(self, dia: date) -> Carimbos | None:
        linhas = self._ler("SELECT criado_em, atualizado_em FROM lancamentos WHERE data = ?", [dia.isoformat()])
        if not linhas:
            return None
        return Carimbos(datetime.fromisoformat(linhas[0][0]), datetime.fromisoformat(linhas[0][1]))

    def salvar(self, lancamento: Lancamento) -> Lancamento:
        """Upsert por data (RN04). Preserva `criado_em`; atualiza `atualizado_em`."""
        agora = self._relogio().isoformat()
        colunas = _colunas_do_lancamento(lancamento)
        nomes = ", ".join(colunas)
        valores = ", ".join(f":{c}" for c in colunas)
        atualiza = ", ".join(f"{c} = excluded.{c}" for c in colunas if c != "data")
        self._transacao(lambda c: c.execute(
            f"INSERT INTO lancamentos ({nomes}, criado_em, atualizado_em) VALUES ({valores}, :agora, :agora) "
            f"ON CONFLICT (data) DO UPDATE SET {atualiza}, atualizado_em = excluded.atualizado_em",
            {**colunas, "agora": agora},
        ))
        return lancamento

    def apagar(self, dia: date) -> bool:
        cursor = self._transacao(lambda c: c.execute("DELETE FROM lancamentos WHERE data = ?", [dia.isoformat()]))
        return cursor.rowcount == 1

    # ---- calendário -------------------------------------------------------------
    def substituir_calendario_automatico(self, ano: int, datas: Iterable[DataDoCalendario]) -> None:
        """UC06 (e o "Recalcular" do 1'): troca as datas automáticas do ano.
        Preserva as manuais (UC10, emendas confirmadas) e o que o usuário ocultou."""
        datas = list(datas)
        for d in datas:
            if d.data.year != ano or not d.origem.automatica:
                raise ValueError(f"Data automática inválida para {ano}: {d}")

        def comandos(c: sqlite3.Connection) -> None:
            ocultas = {
                (r["data"], r["nome"])
                for r in c.execute("SELECT data, nome FROM datas_especiais WHERE oculta = 1 AND data LIKE ?",
                                   [f"{ano:04d}-%"])
            }
            c.execute("DELETE FROM datas_especiais WHERE origem != ? AND data LIKE ?",
                      [Origem.MANUAL.value, f"{ano:04d}-%"])
            manuais = {r[0] for r in c.execute(
                "SELECT data FROM datas_especiais WHERE origem = ? AND data LIKE ?", [Origem.MANUAL.value, f"{ano:04d}-%"])}
            for d in datas:
                if d.natureza is Natureza.EMENDA_SUGERIDA and d.data.isoformat() in manuais:
                    continue  # o usuário já decidiu sobre esse dia
                c.execute(
                    "INSERT OR REPLACE INTO datas_especiais (data, nome, natureza, origem, recorrente, oculta, fonte) "
                    "VALUES (?, ?, ?, ?, 0, ?, ?)",
                    [d.data.isoformat(), d.nome, d.natureza.value, d.origem.value,
                     int((d.data.isoformat(), d.nome) in ocultas), d.fonte],
                )

        self._transacao(comandos)

    def salvar_data_manual(self, d: DataDoCalendario) -> None:
        """UC10 (feriado municipal, emenda da empresa) e UC03 (confirmar emenda)."""
        if d.origem is not Origem.MANUAL:
            raise ValueError("Use substituir_calendario_automatico para datas automáticas.")
        self._transacao(lambda c: c.execute(
            "INSERT OR REPLACE INTO datas_especiais (data, nome, natureza, origem, recorrente, oculta, fonte) "
            "VALUES (?, ?, ?, ?, ?, 0, '')",
            [d.data.isoformat(), d.nome, d.natureza.value, d.origem.value, int(d.recorrente)],
        ))

    def apagar_data_manual(self, dia: date, nome: str) -> bool:
        """Apaga a data manual. Uma recorrente pode ser apagada por qualquer ano em que aparece."""
        cursor = self._transacao(lambda c: c.execute(
            "DELETE FROM datas_especiais WHERE origem = ? AND nome = ? "
            "AND (data = ? OR (recorrente = 1 AND substr(data, 6) = ?))",
            [Origem.MANUAL.value, nome, dia.isoformat(), dia.strftime("%m-%d")]))
        return cursor.rowcount >= 1

    def ocultar_data(self, dia: date, nome: str, oculta: bool = True) -> bool:
        cursor = self._transacao(lambda c: c.execute(
            "UPDATE datas_especiais SET oculta = ? WHERE data = ? AND nome = ?", [int(oculta), dia.isoformat(), nome]))
        return cursor.rowcount == 1

    def datas_do_periodo(self, inicio: date, fim: date, incluir_ocultas: bool = False) -> list[DataDoCalendario]:
        """Datas entre `inicio` e `fim` (inclusive). As manuais recorrentes são projetadas em cada ano do período."""
        linhas = self._ler(
            "SELECT * FROM datas_especiais WHERE (data BETWEEN ? AND ?) OR recorrente = 1 ORDER BY data, nome",
            [inicio.isoformat(), fim.isoformat()])
        datas: dict[tuple[date, str], DataDoCalendario] = {}
        for linha in linhas:
            d = _data_do_calendario_de(linha)
            if not d.recorrente:
                datas[(d.data, d.nome)] = d
                continue
            for ano in range(inicio.year, fim.year + 1):
                try:
                    projetada = d.data.replace(year=ano)
                except ValueError:  # 29/02 em ano não bissexto
                    continue
                if inicio <= projetada <= fim:
                    datas.setdefault((projetada, d.nome), replace(d, data=projetada))
        return [d for _, d in sorted(datas.items()) if incluir_ocultas or not d.oculta]

    def calendario_do_mes(self, ano: int, mes: int) -> CalendarioDoMes:
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        return CalendarioDoMes(self.datas_do_periodo(date(ano, mes, 1), date(ano, mes, ultimo_dia)))

    def anos_com_calendario(self) -> set[int]:
        linhas = self._ler("SELECT DISTINCT substr(data, 1, 4) FROM datas_especiais WHERE origem != ?",
                           [Origem.MANUAL.value])
        return {int(l[0]) for l in linhas}

    # ---- backup (UC09) ----------------------------------------------------------
    def exportar(self) -> Instantaneo:
        with self._trava:  # leitura consistente: tudo na mesma transação
            self._conexao.execute("BEGIN")
            try:
                lancamentos = tuple(
                    LancamentoCarimbado(_lancamento_de(l), Carimbos(datetime.fromisoformat(l["criado_em"]),
                                                                    datetime.fromisoformat(l["atualizado_em"])))
                    for l in self._conexao.execute("SELECT * FROM lancamentos ORDER BY data"))
                datas = [_data_do_calendario_de(l) for l in self._conexao.execute(
                    "SELECT * FROM datas_especiais WHERE origem = ? OR oculta = 1 ORDER BY data, nome",
                    [Origem.MANUAL.value])]
                preferencias = self.preferencias()
            finally:
                self._conexao.execute("COMMIT")
        return Instantaneo(lancamentos,
                           tuple(d for d in datas if d.origem is Origem.MANUAL),
                           tuple(d for d in datas if d.origem is not Origem.MANUAL),
                           preferencias)

    def importar(self, dados: Instantaneo, substituir: bool) -> ResultadoDaImportacao:
        """UC09 3'-4', numa transação única (qualquer erro = rollback).

        substituir: o banco passa a ser o backup (o calendário automático é refeito depois).
        mesclar: por data, vence o lançamento com `atualizado_em` mais recente; datas manuais
        e ocultas do backup são acrescentadas; as preferências do aparelho ficam.
        """
        def comandos(c: sqlite3.Connection) -> ResultadoDaImportacao:
            if substituir:
                c.execute("DELETE FROM lancamentos")
                c.execute("DELETE FROM datas_especiais")
                c.execute("DELETE FROM preferencias")
                _gravar_preferencias(c, dados.preferencias)
            gravados = mantidos = 0
            for item in dados.lancamentos:
                l, carimbos = item.lancamento, item.carimbos
                atual = c.execute("SELECT atualizado_em FROM lancamentos WHERE data = ?",
                                  [l.data.isoformat()]).fetchone()
                if atual is not None and datetime.fromisoformat(atual[0]) >= carimbos.atualizado_em:
                    mantidos += 1
                    continue
                colunas = _colunas_do_lancamento(l)
                c.execute(f"INSERT OR REPLACE INTO lancamentos ({', '.join(colunas)}, criado_em, atualizado_em) "
                          f"VALUES ({', '.join('?' * len(colunas))}, ?, ?)",
                          [*colunas.values(), carimbos.criado_em.isoformat(), carimbos.atualizado_em.isoformat()])
                gravados += 1
            for d in dados.datas_manuais:
                if d.origem is not Origem.MANUAL:
                    raise ValueError(f"Data manual com origem {d.origem}: {d}")
                c.execute("INSERT OR REPLACE INTO datas_especiais (data, nome, natureza, origem, recorrente, oculta, "
                          "fonte) VALUES (?, ?, ?, ?, ?, 0, '')",
                          [d.data.isoformat(), d.nome, d.natureza.value, d.origem.value, int(d.recorrente)])
            for d in dados.datas_ocultas:
                # Se o ano ainda não tem calendário, a linha fica como marcador oculto; o
                # preparo do ano (UC06) a substitui preservando o "oculta".
                c.execute("INSERT OR IGNORE INTO datas_especiais (data, nome, natureza, origem, recorrente, oculta, "
                          "fonte) VALUES (?, ?, ?, ?, 0, 1, ?)",
                          [d.data.isoformat(), d.nome, d.natureza.value, d.origem.value, d.fonte])
                c.execute("UPDATE datas_especiais SET oculta = 1 WHERE data = ? AND nome = ? AND origem != ?",
                          [d.data.isoformat(), d.nome, Origem.MANUAL.value])
            return ResultadoDaImportacao(gravados, mantidos, len(dados.datas_manuais), len(dados.datas_ocultas))

        return self._transacao(comandos)

    # ---- preferências ---------------------------------------------------------
    def preferencias(self) -> Preferencias:
        valores = {r["chave"]: json.loads(r["valor"]) for r in self._ler("SELECT chave, valor FROM preferencias")}
        if "jornada" in valores:
            valores["jornada"] = Jornada(**{k: time.fromisoformat(v) for k, v in valores["jornada"].items()})
        conhecidas = Preferencias.__dataclass_fields__
        return Preferencias(**{k: v for k, v in valores.items() if k in conhecidas})

    def salvar_preferencias(self, preferencias: Preferencias) -> None:
        self._transacao(lambda c: _gravar_preferencias(c, preferencias))


def _gravar_preferencias(c: sqlite3.Connection, preferencias: Preferencias) -> None:
    valores = asdict(preferencias)
    valores["jornada"] = {k: v.strftime("%H:%M") for k, v in valores["jornada"].items()}
    for chave, valor in valores.items():
        c.execute("INSERT OR REPLACE INTO preferencias (chave, valor) VALUES (?, ?)",
                  [chave, json.dumps(valor, ensure_ascii=False)])


# ---- conversões linha <-> domínio ---------------------------------------------
def _colunas_do_lancamento(lancamento: Lancamento) -> dict[str, object]:
    return {
        "data": lancamento.data.isoformat(),
        "tipo": lancamento.tipo.value,
        **{m.value: escrever_horario(lancamento.marcacoes[m]) or None for m in Marcacao},
        "observacao": lancamento.observacao,
    }


def _lancamento_de(linha: sqlite3.Row) -> Lancamento:
    return Lancamento(
        data=date.fromisoformat(linha["data"]),
        tipo=TipoDia(linha["tipo"]),
        marcacoes=Marcacoes(**{m.value: ler_horario(linha[m.value]) for m in Marcacao}),
        observacao=linha["observacao"],
    )


def _data_do_calendario_de(linha: sqlite3.Row) -> DataDoCalendario:
    return DataDoCalendario(
        data=date.fromisoformat(linha["data"]),
        nome=linha["nome"],
        natureza=Natureza(linha["natureza"]),
        origem=Origem(linha["origem"]),
        recorrente=bool(linha["recorrente"]),
        oculta=bool(linha["oculta"]),
        fonte=linha["fonte"],
    )
