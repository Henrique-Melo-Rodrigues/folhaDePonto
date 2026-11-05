"""O mês: pendências (UC07), folha para cópia (UC08, RN10) e resumo (RN08)."""

from __future__ import annotations

import calendar
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, time, timedelta
from enum import StrEnum

from folha_ponto.dominio.dias_especiais import Calendario, DataEspecial, Natureza
from folha_ponto.dominio.lancamento import JORNADA_PADRAO, Jornada, Lancamento
from folha_ponto.dominio.marcacoes import ErroDeValidacao
from folha_ponto.dominio.registro import eh_dia_util, eh_fim_de_semana
from folha_ponto.dominio.vocabulario import MARCACOES_NORMAIS, Status, TipoDia

_NOME_FIM_DE_SEMANA = {5: "Sábado", 6: "Domingo"}


class TipoPendencia(StrEnum):
    SEM_LANCAMENTO = "sem_lancamento"
    INCOMPLETO = "incompleto"
    EMENDA_A_CONFIRMAR = "emenda_a_confirmar"

    @property
    def rotulo(self) -> str:
        return {
            "sem_lancamento": "Dia útil sem lançamento",
            "incompleto": "Lançamento incompleto",
            "emenda_a_confirmar": "Emenda a confirmar",
        }[self]


@dataclass(frozen=True)
class Pendencia:
    data: date
    tipo: TipoPendencia
    descricao: str


@dataclass(frozen=True)
class LinhaDaFolha:
    """Uma linha da folha de papel: DIA · Manhã E/S · Tarde E/S · Extra E/S · observação."""

    data: date
    manha: tuple[time | None, time | None]
    tarde: tuple[time | None, time | None]
    extra: tuple[time | None, time | None]
    observacao: str
    horas: timedelta | None

    @property
    def dia(self) -> int:
        return self.data.day


@dataclass(frozen=True)
class ResumoDoMes:
    dias_uteis: int
    dias_lancados: int
    horas: timedelta
    saldo: timedelta
    pendencias: int


class Mes:
    """Os lançamentos de um mês, vistos contra o calendário."""

    def __init__(
        self,
        ano: int,
        mes: int,
        lancamentos: Iterable[Lancamento],
        calendario: Calendario,
        *,
        facultativo_e_folga: bool = True,
        jornada: Jornada = JORNADA_PADRAO,
    ) -> None:
        self.ano, self.mes = ano, mes
        self.calendario = calendario
        self.facultativo_e_folga = facultativo_e_folga
        self.jornada = jornada
        self.lancamentos: dict[date, Lancamento] = {}
        for lancamento in lancamentos:
            if (lancamento.data.year, lancamento.data.month) != (ano, mes):
                raise ErroDeValidacao(f"O lançamento de {lancamento.data:%d/%m/%Y} não é de {mes:02d}/{ano}.")
            if lancamento.data in self.lancamentos:
                raise ErroDeValidacao(f"Há dois lançamentos para {lancamento.data:%d/%m/%Y} (RN04).")
            self.lancamentos[lancamento.data] = lancamento

    @property
    def dias(self) -> list[date]:
        """Todos os dias do mês, do 1 ao último, inclusive fins de semana (RN10)."""
        total = calendar.monthrange(self.ano, self.mes)[1]
        return [date(self.ano, self.mes, d) for d in range(1, total + 1)]

    def especial(self, dia: date) -> DataEspecial | None:
        return self.calendario.data_especial(dia)

    def eh_dia_util(self, dia: date) -> bool:
        return eh_dia_util(dia, self.especial(dia), self.facultativo_e_folga)

    # ---- UC07 ------------------------------------------------------------
    def pendencias(self, hoje: date) -> list[Pendencia]:
        """O que impede a folha de estar fechada, do dia 1 até `hoje` (inclusive)."""
        encontradas: list[Pendencia] = []
        for dia in self.dias:
            if dia > hoje:
                break
            lancamento = self.lancamentos.get(dia)
            especial = self.especial(dia)
            if lancamento is not None:
                if lancamento.status is Status.INCOMPLETO:
                    falta = [m.rotulo.lower() for m in MARCACOES_NORMAIS if lancamento.marcacoes[m] is None]
                    encontradas.append(Pendencia(dia, TipoPendencia.INCOMPLETO, "Falta: " + ", ".join(falta)))
            elif especial is not None and especial.natureza is Natureza.EMENDA_SUGERIDA and not eh_fim_de_semana(dia):
                encontradas.append(Pendencia(dia, TipoPendencia.EMENDA_A_CONFIRMAR, especial.nome))
            elif self.eh_dia_util(dia):
                encontradas.append(Pendencia(dia, TipoPendencia.SEM_LANCAMENTO, TipoPendencia.SEM_LANCAMENTO.rotulo))
        return encontradas

    # ---- UC08 ------------------------------------------------------------
    def folha(self) -> list[LinhaDaFolha]:
        linhas = []
        for dia in self.dias:
            lancamento = self.lancamentos.get(dia)
            m = lancamento.marcacoes if lancamento else None
            linhas.append(
                LinhaDaFolha(
                    data=dia,
                    manha=(m.entrada, m.saida_almoco) if m else (None, None),
                    tarde=(m.volta_almoco, m.saida) if m else (None, None),
                    extra=(m.entrada_extra, m.saida_extra) if m else (None, None),
                    observacao=self._observacao(dia, lancamento),
                    horas=lancamento.horas if lancamento else None,
                )
            )
        return linhas

    def _observacao(self, dia: date, lancamento: Lancamento | None) -> str:
        especial = self.especial(dia)
        partes: list[str] = []
        if lancamento is None:
            if especial is not None and (
                especial.natureza is not Natureza.FACULTATIVO or self.facultativo_e_folga
            ):
                partes.append(_descrever(especial))
            elif eh_fim_de_semana(dia):
                partes.append(_NOME_FIM_DE_SEMANA[dia.weekday()])
        else:
            if not lancamento.tipo.trabalhado:
                partes.append(lancamento.tipo.rotulo)
                if especial is not None and lancamento.tipo in (TipoDia.FERIADO, TipoDia.FOLGA):
                    partes[-1] += f" — {especial.nome}"
            if lancamento.observacao:
                partes.append(lancamento.observacao)
        return " · ".join(partes)

    # ---- RN08 ------------------------------------------------------------
    def resumo(self, hoje: date) -> ResumoDoMes:
        horas = [l.horas for l in self.lancamentos.values() if l.horas is not None]
        saldos = [s for l in self.lancamentos.values() if (s := l.saldo(self.jornada)) is not None]
        return ResumoDoMes(
            dias_uteis=sum(1 for d in self.dias if self.eh_dia_util(d)),
            dias_lancados=len(self.lancamentos),
            horas=sum(horas, timedelta()),
            saldo=sum(saldos, timedelta()),
            pendencias=len(self.pendencias(hoje)),
        )


def _descrever(especial: DataEspecial) -> str:
    prefixo = {
        Natureza.FERIADO: "Feriado",
        Natureza.FACULTATIVO: "Ponto facultativo",
        Natureza.EMENDA: "Emenda",
        Natureza.EMENDA_SUGERIDA: "Possível emenda",
    }[especial.natureza]
    return especial.nome if especial.nome.startswith(prefixo) else f"{prefixo} — {especial.nome}"
