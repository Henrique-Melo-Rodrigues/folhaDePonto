"""Persistência local em SQLite (subdomínio Generic): o único módulo que fala SQL."""

from folha_ponto.dados.esquema import VERSAO_ATUAL, BancoMaisNovoQueOApp
from folha_ponto.dados.repositorio import (
    CalendarioDoMes,
    Carimbos,
    DataDoCalendario,
    Instantaneo,
    LancamentoCarimbado,
    Origem,
    Repositorio,
    ResultadoDaImportacao,
    caminho_do_banco,
)

__all__ = ["VERSAO_ATUAL", "BancoMaisNovoQueOApp", "CalendarioDoMes", "Carimbos", "DataDoCalendario",
           "Instantaneo", "LancamentoCarimbado", "Origem", "Repositorio", "ResultadoDaImportacao",
           "caminho_do_banco"]
