"""O app: abas Hoje · Mês · Folha · Ajustes (RNF06) sobre a `Page` do Flet.

Rodar no PC:  uv run folha-ponto
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import date
from pathlib import Path

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
        self._servicos_do_aparelho: dict[type, object] = {}
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

    # ---- serviços do aparelho (assíncronos no Flet 1.x) ---------------------------
    def _servico(self, tipo):
        """Uma instância de cada serviço (ao ser criado, ele se registra na página)."""
        if tipo not in self._servicos_do_aparelho:
            self._servicos_do_aparelho[tipo] = tipo()
        return self._servicos_do_aparelho[tipo]

    def _em_segundo_plano(self, tarefa: Callable[[], Awaitable[None]], falha: str) -> None:
        async def executar() -> None:
            try:
                await tarefa()
            except Exception as e:  # ex.: plataforma sem menu Compartilhar
                self.avisar(f"{falha}: {e}", erro=True)
        self.page.run_task(executar)

    def compartilhar_texto(self, texto: str, assunto: str) -> None:
        self._em_segundo_plano(lambda: self._servico(ft.Share).share_text(texto, subject=assunto), "Não deu para compartilhar")

    def compartilhar_arquivo(self, nome: str, conteudo: bytes, mime: str) -> None:
        arquivo = ft.ShareFile.from_bytes(conteudo, mime_type=mime, name=nome)
        self._em_segundo_plano(lambda: self._servico(ft.Share).share_files([arquivo], subject=nome), "Não deu para compartilhar")

    def salvar_arquivo(self, nome: str, conteudo: bytes) -> None:
        async def salvar() -> None:
            caminho = await self._servico(ft.FilePicker).save_file(file_name=nome, src_bytes=conteudo)
            if caminho:
                self.avisar(f"Salvo em {caminho}.")
        self._em_segundo_plano(salvar, "Não deu para salvar")

    def copiar(self, texto: str) -> None:
        async def copiar() -> None:
            await self._servico(ft.Clipboard).set(texto)
            self.avisar("Copiado.")
        self._em_segundo_plano(copiar, "Não deu para copiar")

    def escolher_arquivo(self, ao_escolher: Callable[[bytes], None], extensoes: list[str]) -> None:
        async def escolher() -> None:
            arquivos = await self._servico(ft.FilePicker).pick_files(
                file_type=ft.FilePickerFileType.CUSTOM, allowed_extensions=extensoes, with_data=True)
            if not arquivos:
                return  # cancelou
            arquivo = arquivos[0]
            conteudo = arquivo.bytes if arquivo.bytes is not None else Path(arquivo.path).read_bytes()
            ao_escolher(conteudo)
            self.redesenhar()
        self._em_segundo_plano(escolher, "Não deu para abrir o arquivo")

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
