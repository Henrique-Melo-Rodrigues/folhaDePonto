"""Calendário (subdomínio Supporting): feriados da lib `holidays` (BR/UF),
pontos facultativos, emendas (RN05) e datas manuais (UC10). Offline.

`emendas` é Python puro; `oficial` embrulha a lib; `preparo` grava pelo `Repositorio`.
"""

from folha_ponto.calendario.emendas import EmendaCandidata, emendas_candidatas
from folha_ponto.calendario.oficial import FONTE, CalendarioOficial, DataOficial, calendario_oficial, uf_conhecida
from folha_ponto.calendario.preparo import (
    CalendarioPreparado,
    cadastrar_data,
    confirmar_emenda,
    descartar_emenda,
    garantir_ano,
    ocultar_data,
    preparar_ano,
    remover_data,
)

__all__ = [
    "EmendaCandidata", "emendas_candidatas",
    "FONTE", "CalendarioOficial", "DataOficial", "calendario_oficial", "uf_conhecida",
    "CalendarioPreparado", "cadastrar_data", "confirmar_emenda", "descartar_emenda",
    "garantir_ano", "ocultar_data", "preparar_ano", "remover_data",
]
