"""Formulário do dia: UC02 (lançar), UC03 (feriado/emenda sugeridos), UC04 (excluir)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

import flet as ft

from folha_ponto.dominio import ErroDeValidacao, Marcacao, TipoDia
from folha_ponto.ui.estilo import data_por_extenso
from folha_ponto.ui.telas.base import GRUPOS, Contexto, faixa, quando_clicar

class FormularioDoDia:
    def __init__(self, ctx: Contexto, dia: date, ao_mudar: Callable[[], None]) -> None:
        self.ctx, self.dia, self.ao_mudar = ctx, dia, ao_mudar
        form = ctx.servicos.formulario_do_dia(dia)
        self.existe = form.existe
        paleta = ctx.paleta

        self.tipo = ft.Dropdown(label="Tipo do dia", value=form.tipo.value, expand=True,
                                options=[ft.DropdownOption(key=t.value, text=t.rotulo) for t in TipoDia])
        self.campos = {m: ft.TextField(label=m.rotulo, value=form.textos[m.value], hint_text="HH:MM",
                                       keyboard_type=ft.KeyboardType.DATETIME, dense=True, expand=True)
                       for m in Marcacao}
        self.observacao = ft.TextField(label="Observação", value=form.observacao, multiline=True, dense=True)
        self.erro = ft.Text("", color=paleta.perigo, visible=False)

        linhas: list[ft.Control] = []
        if form.aviso:
            linhas.append(faixa(form.aviso, paleta.aviso_fundo, paleta.aviso_texto))
        linhas.append(ft.Row([self.tipo]))
        for rotulo, ida, volta in GRUPOS:
            linhas.append(ft.Text(rotulo, weight=ft.FontWeight.BOLD))
            linhas.append(ft.Row([self.campos[ida], self.campos[volta]]))
        linhas += [ft.TextButton("Usar jornada padrão", icon=ft.Icons.SCHEDULE,
                                 on_click=quando_clicar(self.usar_jornada_padrao)),
                   self.observacao, self.erro]

        acoes: list[ft.Control] = []
        if self.existe:
            acoes.append(ft.TextButton("Excluir", icon=ft.Icons.DELETE, style=ft.ButtonStyle(color=paleta.perigo),
                                       on_click=quando_clicar(self.pedir_exclusao)))
        acoes += [ft.TextButton("Cancelar", on_click=quando_clicar(ctx.fechar_dialogo)),
                  ft.FilledButton("Salvar", on_click=quando_clicar(self.salvar))]
        self.dialogo = ft.AlertDialog(title=ft.Text(data_por_extenso(dia)), scrollable=True,
                                      content=ft.Column(linhas, tight=True, spacing=8, width=420), actions=acoes)

    def usar_jornada_padrao(self) -> None:
        """UC02 2'."""
        for m, texto in self.ctx.servicos.jornada_padrao().items():
            self.campos[Marcacao(m)].value = texto
        self.tipo.value = TipoDia.TRABALHO.value
        self.ctx.redesenhar()

    def salvar(self) -> None:
        for campo in self.campos.values():
            campo.error = None
        self.erro.visible = False
        try:
            self.ctx.servicos.salvar_dia(self.dia, self.tipo.value,
                                         {m.value: c.value for m, c in self.campos.items()}, self.observacao.value)
        except ErroDeValidacao as e:   # UC02 E1/E2: o formulário fica aberto, campo destacado
            if e.campo is not None:
                self.campos[e.campo].error = str(e)
            self.erro.value, self.erro.visible = str(e), True
            self.ctx.redesenhar()
            return
        self.ctx.fechar_dialogo()
        self.ao_mudar()
        self.ctx.avisar(f"Dia {self.dia:%d/%m} salvo.")

    def pedir_exclusao(self) -> None:
        """UC04: pede confirmação mostrando a data."""
        self.ctx.fechar_dialogo()
        self.ctx.abrir_dialogo(ft.AlertDialog(
            title=ft.Text("Excluir lançamento?"),
            content=ft.Text(f"O lançamento de {data_por_extenso(self.dia)} será apagado. "
                            "Feriados e emendas continuam no calendário."),
            actions=[ft.TextButton("Cancelar", on_click=quando_clicar(self.ctx.fechar_dialogo)),
                     ft.FilledButton("Excluir", on_click=quando_clicar(self.excluir))]))

    def excluir(self) -> None:
        self.ctx.servicos.excluir_dia(self.dia)
        self.ctx.fechar_dialogo()
        self.ao_mudar()
        self.ctx.avisar(f"Lançamento de {self.dia:%d/%m} excluído.")
