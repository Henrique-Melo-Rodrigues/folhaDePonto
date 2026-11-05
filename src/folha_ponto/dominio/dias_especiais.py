"""Porta do calendário: o que o domínio precisa saber sobre um dia especial.

O domínio não sabe de onde vêm os feriados. Quem implementa a porta é o
módulo `folha_ponto.calendario` (WP4: lib holidays + datas manuais + emendas).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Protocol


class Natureza(StrEnum):
    FERIADO = "feriado"              # nacional, estadual ou municipal
    FACULTATIVO = "facultativo"      # ponto facultativo (folga por padrão)
    EMENDA = "emenda"                # emenda confirmada: é folga (D6)
    EMENDA_SUGERIDA = "emenda_sugerida"  # candidata da RN05, ainda não confirmada


@dataclass(frozen=True)
class DataEspecial:
    nome: str          # ex.: "Tiradentes", "Carnaval", "Emenda de Tiradentes"
    natureza: Natureza


class Calendario(Protocol):
    def data_especial(self, dia: date) -> DataEspecial | None: ...


class SemCalendario:
    """Calendário vazio: só fins de semana contam como folga."""

    def data_especial(self, dia: date) -> DataEspecial | None:
        return None
