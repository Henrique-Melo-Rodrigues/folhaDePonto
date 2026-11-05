"""Preferências do Trabalhador (UC11)."""

from __future__ import annotations

from dataclasses import dataclass

from folha_ponto.dominio.lancamento import JORNADA_PADRAO, Jornada
from folha_ponto.dominio.marcacoes import ErroDeValidacao

TEMAS = ("claro", "escuro")


@dataclass(frozen=True)
class Preferencias:
    uf: str = "SP"
    municipio: str = "Cubatão"
    jornada: Jornada = JORNADA_PADRAO
    facultativo_e_folga: bool = True  # ponto facultativo é folga (decisão de 05/11/2026)
    tema: str = "claro"

    def __post_init__(self) -> None:
        uf = (self.uf or "").strip().upper()
        if len(uf) != 2 or not uf.isalpha():
            raise ErroDeValidacao("UF deve ter duas letras (ex.: SP).")
        if self.tema not in TEMAS:
            raise ErroDeValidacao(f"Tema deve ser um de: {', '.join(TEMAS)}.")
        object.__setattr__(self, "uf", uf)
        object.__setattr__(self, "municipio", (self.municipio or "").strip())
