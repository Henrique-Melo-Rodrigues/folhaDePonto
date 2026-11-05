"""Aba Ajustes: preferências (UC11) e calendário do ano (UC10, UC06 1')."""

from __future__ import annotations

import flet as ft

from folha_ponto.dados import DataDoCalendario, Origem
from folha_ponto.dominio import MARCACOES_NORMAIS, ErroDeValidacao, Marcacao, Natureza, escrever_horario
from folha_ponto.exportacao import Backup, ErroDeBackup
from folha_ponto.ui.telas.base import Contexto, Tela, quando_clicar

_NATUREZAS_MANUAIS = ((Natureza.FERIADO, "Feriado (ex.: municipal)"),
                      (Natureza.EMENDA, "Emenda dada pela empresa"),
                      (Natureza.FACULTATIVO, "Ponto facultativo"))
_ROTULO_NATUREZA = {Natureza.FERIADO: "Feriado", Natureza.FACULTATIVO: "Ponto facultativo",
                    Natureza.EMENDA: "Emenda", Natureza.EMENDA_SUGERIDA: "Possível emenda"}
_ROTULO_ORIGEM = {Origem.NACIONAL: "nacional", Origem.ESTADUAL: "estadual", Origem.FACULTATIVO: "facultativo",
                  Origem.REGRA_EMENDA: "regra de emenda", Origem.MANUAL: "cadastrada por você"}


class TelaAjustes(Tela):
    def __init__(self, ctx: Contexto) -> None:
        super().__init__(ctx)
        self.ano_do_calendario = ctx.servicos.hoje().year
        self._montar_campos()

    def _montar_campos(self) -> None:
        p = self.servicos.preferencias
        self.uf = ft.TextField(label="UF", value=p.uf, max_length=2, width=90,
                               capitalization=ft.TextCapitalization.CHARACTERS)
        self.municipio = ft.TextField(label="Município", value=p.municipio, expand=True)
        self.jornada = {m: ft.TextField(label=m.rotulo, value=escrever_horario(p.jornada.marcacoes()[m]),
                                        hint_text="HH:MM", dense=True, expand=True) for m in MARCACOES_NORMAIS}
        self.facultativo = ft.Switch(label="Ponto facultativo é folga", value=p.facultativo_e_folga)
        self.escuro = ft.Switch(label="Tema escuro", value=p.tema == "escuro")
        self.erro = ft.Text("", color=self.ctx.paleta.perigo, visible=False)
        # UC10: nova data
        self.nova_data = ft.TextField(label="Data", hint_text="DD/MM/AAAA", width=140,
                                      keyboard_type=ft.KeyboardType.DATETIME)
        self.novo_nome = ft.TextField(label="Nome", expand=True)
        self.nova_natureza = ft.Dropdown(label="Tipo", value=Natureza.FERIADO.value, expand=True,
                                         options=[ft.DropdownOption(key=n.value, text=t) for n, t in _NATUREZAS_MANUAIS])
        self.recorrente = ft.Checkbox(label="Repete todo ano", value=False)

    def construir(self) -> list[ft.Control]:
        paleta = self.ctx.paleta
        controles: list[ft.Control] = [
            ft.Text("Preferências", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.uf, self.municipio]),
            ft.Text("Jornada padrão", weight=ft.FontWeight.BOLD),
            ft.Row([self.jornada[Marcacao.ENTRADA], self.jornada[Marcacao.SAIDA_ALMOCO]]),
            ft.Row([self.jornada[Marcacao.VOLTA_ALMOCO], self.jornada[Marcacao.SAIDA]]),
            self.facultativo, self.escuro, self.erro,
            ft.Row([ft.FilledButton("Salvar preferências", icon=ft.Icons.CHECK, expand=True,
                                    on_click=quando_clicar(self.salvar_preferencias))]),
            ft.Divider(),
            ft.Text("Backup", size=20, weight=ft.FontWeight.BOLD),   # UC09
            ft.Text("Guarde o arquivo fora do celular (Drive, e-mail): sem ele, trocar de aparelho perde o histórico.",
                    size=12, color=paleta.texto_fraco),
            ft.Row([ft.Button("Fazer backup", icon=ft.Icons.BACKUP, on_click=quando_clicar(self.fazer_backup)),
                    ft.TextButton("Restaurar", icon=ft.Icons.RESTORE, on_click=quando_clicar(self.pedir_backup))],
                   wrap=True),
            ft.Divider(),
            ft.Row([
                ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=quando_clicar(lambda: self.trocar_ano(-1))),
                ft.Text(f"Calendário de {self.ano_do_calendario}", size=20, weight=ft.FontWeight.BOLD),
                ft.IconButton(ft.Icons.CHEVRON_RIGHT, on_click=quando_clicar(lambda: self.trocar_ano(1))),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Text("Adicionar data (feriado municipal ou emenda da empresa)", weight=ft.FontWeight.BOLD),
            ft.Row([self.nova_data, self.novo_nome]),
            ft.Row([self.nova_natureza]),
            self.recorrente,
            ft.Row([ft.Button("Adicionar data", icon=ft.Icons.ADD, on_click=quando_clicar(self.adicionar_data)),
                    ft.TextButton("Recalcular calendário", icon=ft.Icons.REFRESH,
                                  on_click=quando_clicar(self.recalcular))], wrap=True),
        ]
        for d in self.servicos.datas_do_ano(self.ano_do_calendario):
            controles.append(self._data(d, paleta))
        return controles

    def _data(self, d: DataDoCalendario, paleta) -> ft.Control:
        if d.origem is Origem.MANUAL:   # UC10 1': manual pode ser apagada
            acao = ft.IconButton(ft.Icons.DELETE, tooltip="Remover", icon_color=paleta.perigo,
                                 on_click=quando_clicar(lambda: self.remover(d)))
        else:                           # da lib (ou sugestão): só ocultar
            acao = ft.IconButton(ft.Icons.VISIBILITY_OFF if d.oculta else ft.Icons.VISIBILITY,
                                 tooltip="Mostrar" if d.oculta else "Ocultar",
                                 on_click=quando_clicar(lambda: self.alternar_oculta(d)))
        recorre = " · todo ano" if d.recorrente else ""
        return ft.ListTile(
            title=ft.Text(f"{d.data:%d/%m} · {d.nome}", color=paleta.texto_fraco if d.oculta else None),
            subtitle=ft.Text(f"{_ROTULO_NATUREZA[d.natureza]} · {_ROTULO_ORIGEM[d.origem]}{recorre}"
                             + (" · oculta" if d.oculta else "")),
            trailing=acao, dense=True)

    # ---- ações --------------------------------------------------------------------
    def _mostrar_erro(self, e: Exception) -> None:
        self.erro.value, self.erro.visible = str(e), True
        self.ctx.redesenhar()

    def salvar_preferencias(self) -> None:
        self.erro.visible = False
        try:
            avisos = self.servicos.salvar_preferencias(
                uf=self.uf.value, municipio=self.municipio.value,
                jornada={m.value: c.value for m, c in self.jornada.items()},
                facultativo_e_folga=bool(self.facultativo.value), tema="escuro" if self.escuro.value else "claro")
        except ErroDeValidacao as e:
            self._mostrar_erro(e)
            return
        self.ctx.aplicar_tema()
        self._montar_campos()
        self.atualizar()
        self.ctx.redesenhar()
        self.ctx.avisar(" ".join(avisos) or "Preferências salvas.", erro=bool(avisos))

    def trocar_ano(self, passo: int) -> None:
        self.ano_do_calendario += passo
        self.atualizar()
        self.ctx.redesenhar()

    def adicionar_data(self) -> None:
        try:
            d = self.servicos.cadastrar_data(self.nova_data.value, self.novo_nome.value,
                                             self.nova_natureza.value, bool(self.recorrente.value))
        except ErroDeValidacao as e:
            self.ctx.avisar(str(e), erro=True)
            return
        self.ano_do_calendario = d.data.year
        self.nova_data.value = self.novo_nome.value = ""
        self.recorrente.value = False
        self.atualizar()
        self.ctx.redesenhar()
        self.ctx.avisar(f"{d.nome} ({d.data:%d/%m/%Y}) adicionada.")

    def remover(self, d: DataDoCalendario) -> None:
        self.servicos.remover_data(d.data, d.nome)
        self.atualizar()
        self.ctx.redesenhar()

    def alternar_oculta(self, d: DataDoCalendario) -> None:
        self.servicos.ocultar_data(d.data, d.nome, not d.oculta)
        self.atualizar()
        self.ctx.redesenhar()

    def recalcular(self) -> None:
        avisos = self.servicos.recalcular_calendario()
        self.atualizar()
        self.ctx.redesenhar()
        self.ctx.avisar(" ".join(avisos) or "Calendário recalculado.", erro=bool(avisos))

    # ---- UC09 ---------------------------------------------------------------------
    def fazer_backup(self) -> None:
        nome, conteudo = self.servicos.gerar_backup()
        dados = conteudo.encode("utf-8")

        def enviar(acao) -> None:
            self.ctx.fechar_dialogo()
            acao(nome, dados)

        self.ctx.abrir_dialogo(ft.AlertDialog(
            title=ft.Text("Backup pronto"),
            content=ft.Text(f"{nome}: compartilhe (Drive, e-mail, WhatsApp) ou salve numa pasta."),
            actions=[ft.TextButton("Cancelar", on_click=quando_clicar(self.ctx.fechar_dialogo)),
                     ft.TextButton("Salvar arquivo", on_click=quando_clicar(lambda: enviar(self.ctx.salvar_arquivo))),
                     ft.FilledButton("Compartilhar", on_click=quando_clicar(
                         lambda: enviar(lambda n, d: self.ctx.compartilhar_arquivo(n, d, "application/json"))))]))

    def pedir_backup(self) -> None:
        self.ctx.escolher_arquivo(self.confirmar_restauracao, ["json"])

    def confirmar_restauracao(self, conteudo: bytes) -> None:
        """UC09 2': valida e mostra quantos dias serão importados; 3': substituir ou mesclar."""
        try:
            backup = self.servicos.ler_backup(conteudo)
        except ErroDeBackup as e:   # E1: nada é importado
            self.ctx.avisar(str(e), erro=True)
            return
        quando = f" de {backup.gerado_em:%d/%m/%Y %H:%M}" if backup.gerado_em else ""
        self.ctx.abrir_dialogo(ft.AlertDialog(
            title=ft.Text("Restaurar backup?"),
            content=ft.Text(
                f"Backup{quando} com {backup.dias} dia(s) lançado(s) e {len(backup.dados.datas_manuais)} "
                "data(s) cadastrada(s).\n\nSubstituir tudo: o aparelho fica igual ao backup.\n"
                "Mesclar: em cada dia vence o lançamento editado por último; as preferências daqui ficam."),
            actions=[ft.TextButton("Cancelar", on_click=quando_clicar(self.ctx.fechar_dialogo)),
                     ft.TextButton("Substituir tudo", on_click=quando_clicar(lambda: self.restaurar(backup, True))),
                     ft.FilledButton("Mesclar", on_click=quando_clicar(lambda: self.restaurar(backup, False)))]))

    def restaurar(self, backup: Backup, substituir: bool) -> None:
        self.ctx.fechar_dialogo()
        resultado = self.servicos.restaurar(backup, substituir)
        self.ctx.aplicar_tema()       # substituir pode trazer outro tema
        self._montar_campos()
        self.atualizar()
        self.ctx.redesenhar()
        mantidos = f" ({resultado.lancamentos_mantidos} mantido(s) do aparelho)" if resultado.lancamentos_mantidos else ""
        self.ctx.avisar(f"Backup restaurado: {resultado.lancamentos_gravados} dia(s) importado(s){mantidos}.")
