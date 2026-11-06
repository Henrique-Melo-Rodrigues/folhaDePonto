"""Regras de registro: bater o ponto (UC01) e sugerir o tipo do dia (RN06)."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime

from folha_ponto.dominio.dias_especiais import DataEspecial, Natureza
from folha_ponto.dominio.lancamento import Lancamento
from folha_ponto.dominio.marcacoes import ErroDeValidacao
from folha_ponto.dominio.vocabulario import Marcacao, TipoDia

SABADO, DOMINGO = 5, 6


def eh_fim_de_semana(dia: date) -> bool:
    return dia.weekday() in (SABADO, DOMINGO)


def eh_folga_do_calendario(especial: DataEspecial | None, facultativo_e_folga: bool = True) -> bool:
    """Feriado e emenda confirmada são folga; facultativo, se a preferência mandar.
    Emenda sugerida ainda não é folga: espera a confirmação (UC03)."""
    if especial is None:
        return False
    if especial.natureza is Natureza.FACULTATIVO:
        return facultativo_e_folga
    return especial.natureza in (Natureza.FERIADO, Natureza.EMENDA)


def eh_dia_util(dia: date, especial: DataEspecial | None, facultativo_e_folga: bool = True) -> bool:
    """RN07: segunda a sexta que não é folga do calendário."""
    return not eh_fim_de_semana(dia) and not eh_folga_do_calendario(especial, facultativo_e_folga)


def tipo_sugerido(dia: date, especial: DataEspecial | None, facultativo_e_folga: bool = True) -> TipoDia:
    """RN06: o tipo que já vem selecionado ao criar o lançamento de um dia."""
    if especial is not None:
        if especial.natureza is Natureza.FERIADO:
            return TipoDia.FERIADO
        if especial.natureza in (Natureza.EMENDA, Natureza.EMENDA_SUGERIDA):
            return TipoDia.FOLGA  # emenda é folga (D6); a sugerida vem pré-selecionada (UC03)
        if especial.natureza is Natureza.FACULTATIVO and facultativo_e_folga:
            return TipoDia.FOLGA
    return TipoDia.FOLGA if eh_fim_de_semana(dia) else TipoDia.TRABALHO


def bater_ponto(atual: Lancamento | None, agora: datetime, tipo_se_novo: TipoDia) -> tuple[Lancamento, Marcacao]:
    """UC01: grava `agora` (ao minuto) na próxima marcação vazia do dia.

    Sem lançamento, cria um com `tipo_se_novo` (vindo de `tipo_sugerido`).
    Devolve o lançamento novo e a marcação gravada.
    """
    hoje = agora.date()
    if atual is None:
        atual = Lancamento(data=hoje, tipo=tipo_se_novo)
    elif atual.data != hoje:
        raise ErroDeValidacao("Só dá para bater o ponto no lançamento de hoje.")

    marcacao = atual.marcacoes.proxima_vazia()
    if marcacao is None:
        raise ErroDeValidacao("Todas as marcações de hoje já estão preenchidas. Edite o dia para corrigir.")

    horario = agora.time().replace(second=0, microsecond=0)
    return replace(atual, marcacoes=atual.marcacoes.com(marcacao, horario)), marcacao
