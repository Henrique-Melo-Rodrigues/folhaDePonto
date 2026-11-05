"""RN05: emendas candidatas. Python puro, sem lib e sem banco.

Feriado na terça → a segunda anterior. Feriado na quinta → a sexta seguinte.
Só se o dia candidato for útil. É sugestão: vira emenda quando confirmada (UC03).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta

from folha_ponto.dominio import DataEspecial, Natureza
from folha_ponto.dominio.registro import eh_folga_do_calendario, eh_fim_de_semana

TERCA, QUINTA = 1, 3
_NOME_DO_DIA = ("segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo")


@dataclass(frozen=True)
class EmendaCandidata:
    data: date          # o dia que seria a emenda (segunda ou sexta)
    motivo: date        # o feriado que a justifica
    nome_do_motivo: str

    @property
    def nome(self) -> str:
        """Ex.: "Tiradentes (terça, 21/04)". A UI prefixa "Possível emenda" ou "Emenda"."""
        return f"{self.nome_do_motivo} ({_NOME_DO_DIA[self.motivo.weekday()]}, {self.motivo:%d/%m})"

    @property
    def especial(self) -> DataEspecial:
        return DataEspecial(self.nome, Natureza.EMENDA_SUGERIDA)


def emendas_candidatas(
    datas: Iterable[tuple[date, DataEspecial]], facultativo_e_folga: bool = True
) -> list[EmendaCandidata]:
    """Calcula as emendas a partir das datas do calendário (lib + manuais).

    Ponto facultativo só justifica emenda se for folga (preferência ligada), e
    emenda sugerida nunca justifica outra emenda.
    """
    folgas: dict[date, list[str]] = {}
    for dia, especial in datas:
        if eh_folga_do_calendario(especial, facultativo_e_folga):
            folgas.setdefault(dia, []).append(especial.nome)

    candidatas: dict[date, EmendaCandidata] = {}
    for motivo in sorted(folgas):
        if motivo.weekday() == TERCA:
            dia = motivo - timedelta(days=1)
        elif motivo.weekday() == QUINTA:
            dia = motivo + timedelta(days=1)
        else:
            continue
        if dia in folgas or eh_fim_de_semana(dia):
            continue  # o candidato já não é útil
        candidatas.setdefault(dia, EmendaCandidata(dia, motivo, " / ".join(folgas[motivo])))
    return sorted(candidatas.values(), key=lambda c: c.data)
