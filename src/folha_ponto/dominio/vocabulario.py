"""Vocabulário do domínio (linguagem ubíqua): tipos de dia, status e marcações.

Fonte única desses termos. Substitui o contracts/time_record.json da v1, que
só existia para três linguagens lerem o mesmo vocabulário (ADR-002).
"""

from __future__ import annotations

from enum import StrEnum


class TipoDia(StrEnum):
    TRABALHO = "trabalho"
    ATIVIDADE_TEORICA = "atividade_teorica"
    FOLGA = "folga"
    COMPENSACAO = "compensacao"
    FERIADO = "feriado"
    FALTA = "falta"
    OUTRO = "outro"

    @property
    def rotulo(self) -> str:
        return _ROTULOS_TIPO[self][0]

    @property
    def rotulo_curto(self) -> str:
        return _ROTULOS_TIPO[self][1]

    @property
    def trabalhado(self) -> bool:
        """Só o dia de trabalho espera marcações; os demais são "não trabalhados"."""
        return self is TipoDia.TRABALHO


_ROTULOS_TIPO = {
    TipoDia.TRABALHO: ("Trabalho", "Trabalho"),
    TipoDia.ATIVIDADE_TEORICA: ("Atividade teórica", "Teórica"),
    TipoDia.FOLGA: ("Folga", "Folga"),
    TipoDia.COMPENSACAO: ("Compensação", "Comp."),
    TipoDia.FERIADO: ("Feriado", "Feriado"),
    TipoDia.FALTA: ("Falta", "Falta"),
    TipoDia.OUTRO: ("Outro", "Outro"),
}


class Status(StrEnum):
    """Situação do lançamento. Sempre derivada (RN03), nunca digitada."""

    COMPLETO = "completo"
    INCOMPLETO = "incompleto"
    NAO_TRABALHADO = "nao_trabalhado"

    @property
    def rotulo(self) -> str:
        return {"completo": "Completo", "incompleto": "Incompleto", "nao_trabalhado": "Não trabalhado"}[self]


class Marcacao(StrEnum):
    """Os horários de um dia, na ordem em que acontecem e na ordem da folha de papel:
    Manhã (entrada/saída), Tarde (entrada/saída) e Extra (entrada/saída)."""

    ENTRADA = "entrada"
    SAIDA_ALMOCO = "saida_almoco"
    VOLTA_ALMOCO = "volta_almoco"
    SAIDA = "saida"
    ENTRADA_EXTRA = "entrada_extra"
    SAIDA_EXTRA = "saida_extra"

    @property
    def rotulo(self) -> str:
        return _ROTULOS_MARCACAO[self]

    @property
    def extra(self) -> bool:
        return self in (Marcacao.ENTRADA_EXTRA, Marcacao.SAIDA_EXTRA)


_ROTULOS_MARCACAO = {
    Marcacao.ENTRADA: "Entrada",
    Marcacao.SAIDA_ALMOCO: "Saída almoço",
    Marcacao.VOLTA_ALMOCO: "Volta almoço",
    Marcacao.SAIDA: "Saída",
    Marcacao.ENTRADA_EXTRA: "Entrada extra",
    Marcacao.SAIDA_EXTRA: "Saída extra",
}

MARCACOES_NORMAIS = tuple(m for m in Marcacao if not m.extra)
