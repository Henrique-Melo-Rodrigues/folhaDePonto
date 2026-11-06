"""Aba Hoje: bater o ponto com um toque (UC01, RNF04)."""

from __future__ import annotations

import flet as ft

from folha_ponto.dominio import ErroDeValidacao, Marcacao, escrever_horario
from folha_ponto.ui.estilo import data_por_extenso
from folha_ponto.ui.servicos import escrever_duracao
from folha_ponto.ui.telas.base import GRUPOS, Tela, faixa, quando_clicar


class TelaHoje(Tela):
    def construir(self) -> list[ft.Control]:
        painel = self.servicos.painel_de_hoje()
        paleta = self.ctx.paleta
        controles: list[ft.Control] = [ft.Text(data_por_extenso(painel.data), size=22, weight=ft.FontWeight.BOLD)]
        if painel.aviso:
            controles.append(faixa(painel.aviso, paleta.aviso_fundo, paleta.aviso_texto))

        if painel.proxima is not None:
            controles.append(ft.Row([ft.FilledButton(  # botão grande, largura toda (RNF04, RNF06)
                f"Registrar {painel.proxima.rotulo}", icon=ft.Icons.FINGERPRINT, height=72, expand=True,
                on_click=quando_clicar(self.bater_ponto))]))
        else:  # UC01 E2: tudo preenchido
            controles.append(ft.Text("Todas as marcações de hoje estão preenchidas.", color=paleta.texto_fraco))

        marcacoes = painel.marcacoes
        for rotulo, ida, volta in GRUPOS:
            if ida.extra and marcacoes.entrada_extra is None and painel.proxima not in (ida, volta):
                continue  # a Extra só aparece quando há hora extra (UC01 3'')
            controles.append(ft.Text(rotulo, weight=ft.FontWeight.BOLD, color=paleta.texto_fraco))
            controles.append(ft.Row([self._marcacao(m, escrever_horario(marcacoes[m]), m is painel.proxima)
                                     for m in (ida, volta)]))

        if painel.lancamento is not None:
            l = painel.lancamento
            detalhe = f"{l.tipo.rotulo} · {l.status.rotulo}"
            if l.horas is not None:
                detalhe += f" · {escrever_duracao(l.horas)} (saldo {escrever_duracao(l.saldo(self.servicos.preferencias.jornada))})"
            controles.append(ft.Text(detalhe, color=paleta.texto_fraco))
        controles.append(ft.TextButton("Editar dia", icon=ft.Icons.EDIT,
                                       on_click=quando_clicar(lambda: self.ctx.abrir_dia(painel.data))))
        return controles

    def _marcacao(self, marcacao: Marcacao, texto: str, destaque: bool) -> ft.Container:
        """Toque numa marcação = ajustar a hora (UC01 3')."""
        paleta = self.ctx.paleta
        return ft.Container(
            ft.Column([ft.Text(marcacao.rotulo, size=12, color=paleta.texto_fraco),
                       ft.Text(texto or "--:--", size=24, weight=ft.FontWeight.BOLD)], spacing=2, tight=True),
            expand=True, padding=12, border_radius=10, bgcolor=paleta.superficie,
            border=ft.Border.all(2 if destaque else 1, paleta.primaria if destaque else paleta.borda),
            on_click=quando_clicar(lambda: self.pedir_horario(marcacao, texto)))

    def bater_ponto(self) -> None:
        try:
            lancamento, marcacao = self.servicos.bater_ponto()
        except ErroDeValidacao as e:
            self.ctx.avisar(str(e), erro=True)
            return
        self.atualizar()
        self.ctx.redesenhar()
        self.ctx.avisar(f"{marcacao.rotulo} registrada às {escrever_horario(lancamento.marcacoes[marcacao])}.")

    def pedir_horario(self, marcacao: Marcacao, atual: str) -> None:
        campo = ft.TextField(label=marcacao.rotulo, hint_text="HH:MM", autofocus=True,
                             value=atual or self.servicos.agora().strftime("%H:%M"),
                             keyboard_type=ft.KeyboardType.DATETIME)

        def salvar() -> None:
            try:
                self.servicos.ajustar_marcacao(marcacao, campo.value)
            except ErroDeValidacao as e:  # UC01 E1: nada é gravado; mostra o conflito
                campo.error = str(e)
                self.ctx.redesenhar()
                return
            self.ctx.fechar_dialogo()
            self.atualizar()
            self.ctx.redesenhar()

        self.ctx.abrir_dialogo(ft.AlertDialog(
            title=ft.Text(f"Ajustar {marcacao.rotulo.lower()}"),
            content=ft.Column([campo, ft.Text("Deixe vazio para apagar a marcação.", size=12)], tight=True),
            actions=[ft.TextButton("Cancelar", on_click=quando_clicar(self.ctx.fechar_dialogo)),
                     ft.FilledButton("Salvar", on_click=quando_clicar(salvar))]))
