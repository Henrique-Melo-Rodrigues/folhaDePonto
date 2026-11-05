"""O ator "Calendário oficial do Brasil" (D3): a lib `holidays`, embarcada e offline.

Traz os feriados nacionais e estaduais (categoria `public`) e os pontos
facultativos (categoria `optional`). Municipais e emendas da empresa não
existem na lib: entram à mão (UC10).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import holidays

from folha_ponto.dominio import Natureza

PAIS = "BR"
FONTE = f"holidays {holidays.__version__}"  # RN09: dá para explicar de onde veio a data


@dataclass(frozen=True)
class DataOficial:
    data: date
    nome: str
    natureza: Natureza   # FERIADO ou FACULTATIVO
    origem: str          # "nacional" | "estadual" | "facultativo" (valores de dados.Origem)


@dataclass(frozen=True)
class CalendarioOficial:
    datas: list[DataOficial]
    aviso: str = ""                          # UC06 E1: UF desconhecida
    fonte: str = FONTE
    anos: tuple[int, ...] = field(default=())


def uf_conhecida(uf: str) -> bool:
    return uf.upper() in holidays.country_holidays(PAIS).subdivisions


def calendario_oficial(anos: int | list[int] | tuple[int, ...], uf: str = "SP") -> CalendarioOficial:
    """UC06 passo 2. UF que a lib não conhece: só os nacionais, com aviso (E1)."""
    anos = (anos,) if isinstance(anos, int) else tuple(anos)
    uf = (uf or "").strip().upper()
    aviso = ""
    if not uf_conhecida(uf):
        aviso = f"A UF {uf or '(vazia)'} não foi encontrada; usei só os feriados nacionais. Revise a UF nas preferências."
        uf = ""

    nacionais = holidays.country_holidays(PAIS, years=anos, categories=("public",), language="pt_BR")
    do_estado = (holidays.country_holidays(PAIS, subdiv=uf, years=anos, categories=("public",), language="pt_BR")
                 if uf else nacionais)
    facultativos = holidays.country_holidays(PAIS, years=anos, categories=("optional",), language="pt_BR")

    datas: list[DataOficial] = []
    for dia, nomes in sorted(do_estado.items()):
        nacionais_do_dia = set(_separar(nacionais.get(dia, "")))
        for nome in _separar(nomes):
            origem = "nacional" if nome in nacionais_do_dia else "estadual"
            datas.append(DataOficial(dia, nome, Natureza.FERIADO, origem))
    for dia, nomes in sorted(facultativos.items()):
        datas.extend(DataOficial(dia, nome, Natureza.FACULTATIVO, "facultativo") for nome in _separar(nomes))
    datas.sort(key=lambda d: (d.data, d.natureza != Natureza.FERIADO, d.nome))
    return CalendarioOficial(datas, aviso, anos=anos)


def _separar(nomes: str) -> list[str]:
    """A lib junta dois nomes no mesmo dia com "; "."""
    return [n.strip() for n in nomes.split(";") if n.strip()]
