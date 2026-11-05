"""Horários de um dia (RN01, RN02)."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, fields, replace
from datetime import time

from folha_ponto.dominio.vocabulario import MARCACOES_NORMAIS, Marcacao

_HORARIO_RE = re.compile(r"^\d{2}:\d{2}$")


class ErroDeValidacao(ValueError):
    """Entrada inválida do usuário. `campo` diz qual marcação destacar na tela."""

    def __init__(self, mensagem: str, campo: Marcacao | None = None) -> None:
        super().__init__(mensagem)
        self.campo = campo


def ler_horario(texto: str | None, campo: Marcacao | None = None) -> time | None:
    """RN01: `HH:MM` entre 00:00 e 23:59. Vazio (ou só espaços) = sem horário."""
    valor = (texto or "").strip()
    if not valor:
        return None
    if not _HORARIO_RE.fullmatch(valor):
        raise ErroDeValidacao("Use horários no formato HH:MM.", campo)
    hora, minuto = int(valor[:2]), int(valor[3:])
    if hora > 23 or minuto > 59:
        raise ErroDeValidacao("Use horários válidos entre 00:00 e 23:59.", campo)
    return time(hora, minuto)


def escrever_horario(horario: time | None) -> str:
    return horario.strftime("%H:%M") if horario else ""


@dataclass(frozen=True)
class Marcacoes:
    """As seis marcações do dia. Um objeto inválido não chega a existir:
    a ordem (RN02) é conferida na criação."""

    entrada: time | None = None
    saida_almoco: time | None = None
    volta_almoco: time | None = None
    saida: time | None = None
    entrada_extra: time | None = None
    saida_extra: time | None = None

    def __post_init__(self) -> None:
        for marcacao, horario in self.preenchidas():
            if horario.second or horario.microsecond:
                raise ErroDeValidacao("Marcações têm precisão de minuto.", marcacao)

        # RN02: as marcações preenchidas seguem a ordem do dia (vazias no meio são aceitas).
        anterior: tuple[Marcacao, time] | None = None
        for marcacao, horario in self.preenchidas():
            if anterior and horario <= anterior[1]:
                raise ErroDeValidacao(
                    f"{marcacao.rotulo} ({escrever_horario(horario)}) precisa ser depois de "
                    f"{anterior[0].rotulo.lower()} ({escrever_horario(anterior[1])}).",
                    marcacao,
                )
            anterior = (marcacao, horario)

        # A saída extra só existe se houver a entrada extra. O contrário é válido:
        # é a hora extra em andamento (UC01, fluxo 3'').
        if self.saida_extra and not self.entrada_extra:
            raise ErroDeValidacao("Informe a entrada extra antes da saída extra.", Marcacao.SAIDA_EXTRA)

    @classmethod
    def de_textos(cls, textos: Mapping[str, str | None]) -> Marcacoes:
        """Monta a partir do formulário: {"entrada": "07:45", "saida": "", ...}."""
        desconhecidas = set(textos) - {m.value for m in Marcacao}
        if desconhecidas:
            raise ErroDeValidacao(f"Marcação desconhecida: {', '.join(sorted(desconhecidas))}.")
        return cls(**{m.value: ler_horario(textos.get(m.value), m) for m in Marcacao})

    def __getitem__(self, marcacao: Marcacao) -> time | None:
        return getattr(self, Marcacao(marcacao).value)

    def como_textos(self) -> dict[str, str]:
        return {f.name: escrever_horario(getattr(self, f.name)) for f in fields(self)}

    def preenchidas(self) -> list[tuple[Marcacao, time]]:
        return [(m, h) for m in Marcacao if (h := self[m]) is not None]

    @property
    def vazia(self) -> bool:
        return not self.preenchidas()

    @property
    def normais_completas(self) -> bool:
        return all(self[m] for m in MARCACOES_NORMAIS)

    def com(self, marcacao: Marcacao, horario: time | None) -> Marcacoes:
        """Cópia com uma marcação trocada (revalida a ordem)."""
        return replace(self, **{Marcacao(marcacao).value: horario})

    def proxima_vazia(self) -> Marcacao | None:
        """A próxima marcação a bater (UC01): a primeira vazia depois da última preenchida.
        Depois da saída, oferece a hora extra."""
        preenchidas = self.preenchidas()
        ordem = list(Marcacao)
        inicio = ordem.index(preenchidas[-1][0]) + 1 if preenchidas else 0
        return next((m for m in ordem[inicio:] if self[m] is None), None)
