"""O app: abas Hoje · Mês · Folha · Ajustes (RNF06) sobre a `Page` do Flet.

Rodar no PC:  uv run folha-ponto
"""

from __future__ import annotations

from datetime import date

import flet as ft

from folha_ponto.dados import Repositorio
from folha_ponto.ui.estilo import Paleta, paleta
from folha_ponto.ui.servicos import Servicos
from folha_ponto.ui.telas.ajustes import TelaAjustes
from folha_ponto.ui.telas.base import ABAS, Tela
from folha_ponto.ui.telas.dia import FormularioDoDia
from folha_ponto.ui.telas.folha import TelaFolha
from folha_ponto.ui.telas.hoje import TelaHoje
from folha_ponto.ui.telas.mes import TelaMes

_DESTINOS = (("Hoje", ft.Icons.TODAY), ("Mês", ft.Icons.CALENDAR_MONTH),
             ("Folha", ft.Icons.TABLE_ROWS), ("Ajustes", ft.Icons.SETTINGS))


class App:
    """Implementa o `Contexto` das telas."""

    def __init__(self, page: ft.Page, servicos: Servicos) -> None:
        self.page, self.servicos = page, servicos
        hoje = servicos.hoje()
        self.ano, self.mes = hoje.year, hoje.month
        self.telas: dict[str, Tela] = {"hoje": TelaHoje(self), "mes": TelaMes(self),
                                       "folha": TelaFolha(self), "ajustes": TelaAjustes(self)}
        self.aba = "hoje"
        self.corpo = ft.Container(expand=True, padding=12)

        page.title = "Folha de Ponto"
        page.navigation_bar = ft.NavigationBar(
            destinations=[ft.NavigationBarDestination(icon=icone, label=rotulo) for rotulo, icone in _DESTINOS],
            selected_index=0, on_change=self._ao_trocar_aba)
        self.aplicar_tema()
        page.add(ft.SafeArea(self.corpo, expand=True))
        self.ir_para("hoje")

    # ---- Contexto -------------------------------------------------------------
    @property
    def paleta(self) -> Paleta:
        return paleta(self.servicos.preferencias.tema)

    def redesenhar(self) -> None:
        self.page.update()

    def abrir_dialogo(self, dialogo: ft.AlertDialog) -> None:
        self.page.show_dialog(dialogo)

    def fechar_dialogo(self) -> None:
        self.page.pop_dialog()

    def avisar(self, texto: str, erro: bool = False) -> None:
        p = self.paleta
        self.page.show_dialog(ft.SnackBar(ft.Text(texto, color=p.contraste if not erro else None),
                                          bgcolor=p.perigo if erro else p.primaria))

    def ir_para(self, aba: str) -> None:
        self.aba = aba
        self.page.navigation_bar.selected_index = ABAS.index(aba)
        tela = self.telas[aba]
        tela.atualizar()
        self.corpo.content = tela.raiz
        self.redesenhar()
        for aviso in self.servicos.tirar_avisos():  # UC06 E1: UF desconhecida
            self.avisar(aviso, erro=True)

    def abrir_dia(self, dia: date) -> None:
        self.abrir_dialogo(FormularioDoDia(self, dia, ao_mudar=self._recarregar_aba).dialogo)

    def aplicar_tema(self) -> None:
        p = self.paleta
        self.page.theme_mode = ft.ThemeMode.DARK if self.servicos.preferencias.tema == "escuro" else ft.ThemeMode.LIGHT
        self.page.theme = ft.Theme(color_scheme_seed=p.primaria)
        self.page.dark_theme = ft.Theme(color_scheme_seed=p.primaria)
        self.page.bgcolor = p.fundo

    # ---- internos ---------------------------------------------------------------
    def _recarregar_aba(self) -> None:
        self.telas[self.aba].atualizar()
        self.redesenhar()

    def _ao_trocar_aba(self, evento) -> None:
        self.ir_para(ABAS[int(evento.control.selected_index)])


def main(page: ft.Page) -> None:
    App(page, Servicos(Repositorio()))


def executar() -> None:
    ft.run(main)


if __name__ == "__main__":
    executar()
