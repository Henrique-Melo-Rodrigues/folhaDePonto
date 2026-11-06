"""O lançamento de um dia: status (RN03), horas e saldo (RN08), jornada."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from folha_ponto.dominio.marcacoes import ErroDeValidacao, Marcacoes
from folha_ponto.dominio.vocabulario import Status, TipoDia


def _duracao(inicio: time, fim: time) -> timedelta:
    return datetime.combine(date.min, fim) - datetime.combine(date.min, inicio)


def calcular_status(tipo: TipoDia, marcacoes: Marcacoes) -> Status:
    """RN03. A hora extra não influi no status."""
    if not tipo.trabalhado and marcacoes.vazia:
        return Status.NAO_TRABALHADO
    if marcacoes.normais_completas:
        return Status.COMPLETO
    return Status.INCOMPLETO


def calcular_horas(marcacoes: Marcacoes) -> timedelta | None:
    """RN08: manhã + tarde (+ extra, se tiver as duas pontas). Só com as quatro normais."""
    m = marcacoes
    if not m.normais_completas:
        return None
    total = _duracao(m.entrada, m.saida_almoco) + _duracao(m.volta_almoco, m.saida)
    if m.entrada_extra and m.saida_extra:
        total += _duracao(m.entrada_extra, m.saida_extra)
    return total


@dataclass(frozen=True)
class Jornada:
    """Horário contratual. Padrão = o impresso na folha oficial (6 h, segunda a sexta)."""

    entrada: time = time(7, 45)
    saida_almoco: time = time(12, 0)
    volta_almoco: time = time(13, 0)
    saida: time = time(14, 45)

    def marcacoes(self) -> Marcacoes:
        return Marcacoes(self.entrada, self.saida_almoco, self.volta_almoco, self.saida)

    @property
    def duracao(self) -> timedelta:
        return calcular_horas(self.marcacoes())


JORNADA_PADRAO = Jornada()


@dataclass(frozen=True)
class Lancamento:
    """O registro de um dia. Um lançamento por data (RN04)."""

    data: date
    tipo: TipoDia
    marcacoes: Marcacoes = field(default_factory=Marcacoes)
    observacao: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.data, date) or isinstance(self.data, datetime):
            raise ErroDeValidacao("A data do lançamento deve ser um dia (date).")
        object.__setattr__(self, "tipo", TipoDia(self.tipo))
        object.__setattr__(self, "observacao", (self.observacao or "").strip())

    @property
    def status(self) -> Status:
        return calcular_status(self.tipo, self.marcacoes)

    @property
    def horas(self) -> timedelta | None:
        return calcular_horas(self.marcacoes)

    def saldo(self, jornada: Jornada = JORNADA_PADRAO) -> timedelta | None:
        """Dia de trabalho: horas − jornada. Outro tipo com horas (ex.: trabalhou na folga):
        todas as horas são saldo. Sem horas completas: sem saldo."""
        if self.horas is None:
            return None
        return self.horas - jornada.duracao if self.tipo.trabalhado else self.horas
