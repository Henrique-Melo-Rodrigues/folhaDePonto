"""GERADO por contracts/generate.py a partir de contracts/time_record.json. Nao edite a mao."""

from __future__ import annotations

DAY_TYPES = (
    "trabalho",
    "atividade_teorica",
    "folga",
    "compensacao",
    "feriado",
    "falta",
    "outro",
)

NOT_WORKED_DAY_TYPES = frozenset({
    "atividade_teorica",
    "folga",
    "compensacao",
    "feriado",
    "falta",
    "outro",
})

STATUSES = (
    "complete",
    "incomplete",
    "not_worked",
)

TIME_FIELDS = (
    "arrival",
    "lunch_start",
    "lunch_end",
    "departure",
)

TIME_PATTERN = r"^\d{2}:\d{2}$"
