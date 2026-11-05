"""O que toda tela recebe (o contexto) e a base comum.

As telas não conhecem a `Page` do Flet: recebem um `Contexto`. Assim dá para
montá-las e acionar os botões nos testes, sem abrir janela.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Protocol

import flet as ft

from folha_ponto.dominio import Marcacao
from folha_ponto.ui.estilo import Paleta
from folha_ponto.ui.servicos import Servicos

ABAS = ("hoje", "mes", "folha", "ajustes")

# As colunas da folha de papel (D5): Manhã, Tarde e Extra, cada uma com entrada e saída.
GRUPOS = (("Manhã", Marcacao.ENTRADA, Marcacao.SAIDA_ALMOCO),
          ("Tarde", Marcacao.VOLTA_ALMOCO, Marcacao.SAIDA),
          ("Extra", Marcacao.ENTRADA_EXTRA, Marcacao.SAIDA_EXTRA))


class Contexto(Protocol):
    servicos: Servicos
    ano: int                 # mês aberto nas abas Mês e Folha (compartilhado)
    mes: int

    @property
    def paleta(self) -> Paleta: ...
    def redesenhar(self) -> None: ...
    def abrir_dialogo(self, dialogo: ft.AlertDialog) -> None: ...
    def fechar_dialogo(self) -> None: ...
    def avisar(self, texto: str, erro: bool = False) -> None: ...
    def ir_para(self, aba: str) -> None: ...
    def abrir_dia(self, dia: date) -> None: ...
    def aplicar_tema(self) -> None: ...
    # UC08 2' e UC09: menu Compartilhar, arquivos e área de transferência do aparelho
    def compartilhar_texto(self, texto: str, assunto: str) -> None: ...
    def compartilhar_arquivo(self, nome: str, conteudo: bytes, mime: str) -> None: ...
    def salvar_arquivo(self, nome: str, conteudo: bytes) -> None: ...
    def copiar(self, texto: str) -> None: ...
    def escolher_arquivo(self, ao_escolher: Callable[[bytes], None], extensoes: list[str]) -> None: ...


class Tela:
    """Uma aba. `raiz` é o controle que o app mostra; `atualizar` refaz o conteúdo."""

    def __init__(self, ctx: Contexto) -> None:
        self.ctx = ctx
        self.raiz = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=12)

    @property
    def servicos(self) -> Servicos:
        return self.ctx.servicos

    def construir(self) -> list[ft.Control]:
        raise NotImplementedError

    def atualizar(self) -> None:
        self.raiz.controls = self.construir()


def faixa(texto: str, fundo: str, cor: str) -> ft.Container:
    """Aviso destacado (feriado, emenda, pendências)."""
    return ft.Container(ft.Text(texto, color=cor, weight=ft.FontWeight.W_600), bgcolor=fundo,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=8), border_radius=10)


def quando_clicar(acao: Callable[[], object]) -> Callable[[object], None]:
    """Handler de evento que ignora o argumento do Flet (e aceita ser chamado sem ele nos testes)."""
    def handler(_evento: object = None) -> None:
        acao()
    return handler
