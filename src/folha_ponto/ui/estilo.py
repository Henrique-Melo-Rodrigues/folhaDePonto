"""Paleta (a mesma do web da v1, RNF06) e textos de data em português."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from folha_ponto.dominio import Natureza, Status
from folha_ponto.exportacao.folha import MESES

DIAS_DA_SEMANA = ("Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo")
DIAS_CURTOS = ("S", "T", "Q", "Q", "S", "S", "D")


@dataclass(frozen=True)
class Paleta:
    primaria: str
    contraste: str
    perigo: str
    fundo: str
    superficie: str
    texto: str
    texto_fraco: str
    borda: str
    ok_fundo: str
    ok_texto: str
    aviso_fundo: str
    aviso_texto: str
    neutro_fundo: str

    def fundo_do_status(self, status: Status | None) -> str:
        return {Status.COMPLETO: self.ok_fundo, Status.INCOMPLETO: self.aviso_fundo,
                Status.NAO_TRABALHADO: self.neutro_fundo}.get(status, self.superficie)

    def cor_da_natureza(self, natureza: Natureza | None) -> str:
        """Borda do dia no mês: feriado/emenda = primária; possível emenda = aviso."""
        if natureza is Natureza.EMENDA_SUGERIDA:
            return self.aviso_texto
        if natureza is not None:
            return self.primaria
        return self.borda


CLARO = Paleta(
    primaria="#1e5cb3", contraste="#ffffff", perigo="#b3261e", fundo="#f4f6f9", superficie="#ffffff",
    texto="#1c1f26", texto_fraco="#5b6472", borda="#d8dee7", ok_fundo="#e0f2e6", ok_texto="#1c6b34",
    aviso_fundo="#fdf0d7", aviso_texto="#8a5b00", neutro_fundo="#e8ebf0",
)
ESCURO = Paleta(
    primaria="#5b9dff", contraste="#0d1117", perigo="#ff9d94", fundo="#14161a", superficie="#1e2126",
    texto="#e6e9ee", texto_fraco="#9aa3b0", borda="#333a44", ok_fundo="#1d3826", ok_texto="#8ed6a4",
    aviso_fundo="#3b2f10", aviso_texto="#e8c76a", neutro_fundo="#262b33",
)


def paleta(tema: str) -> Paleta:
    return ESCURO if tema == "escuro" else CLARO


def nome_do_mes(ano: int, mes: int) -> str:
    return f"{MESES[mes - 1]} {ano}"


def data_por_extenso(dia: date) -> str:
    """Ex.: "Quarta, 22/04/2026"."""
    return f"{DIAS_DA_SEMANA[dia.weekday()]}, {dia:%d/%m/%Y}"


def mes_vizinho(ano: int, mes: int, passo: int) -> tuple[int, int]:
    total = ano * 12 + (mes - 1) + passo
    return total // 12, total % 12 + 1
