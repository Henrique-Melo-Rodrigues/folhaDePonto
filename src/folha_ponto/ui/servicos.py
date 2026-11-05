"""Serviços de aplicação: o que as telas chamam. Sem Flet, sem SQL.

Orquestra domínio, calendário e repositório para cada caso de uso, para que as
telas (ui/telas) fiquem finas e as regras continuem testáveis sem UI (RNF05).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta

from folha_ponto import calendario, exportacao
from folha_ponto.dados import CalendarioDoMes, DataDoCalendario, Origem, Repositorio, ResultadoDaImportacao
from folha_ponto.dominio import (
    DataEspecial,
    ErroDeValidacao,
    Lancamento,
    Marcacao,
    Marcacoes,
    Mes,
    Natureza,
    TipoDia,
    bater_ponto,
    ler_horario,
    tipo_sugerido,
)
from folha_ponto.dominio.lancamento import Jornada
from folha_ponto.dominio.preferencias import Preferencias
from folha_ponto.exportacao import Backup
from folha_ponto.exportacao import backup as arquivo_de_backup
from folha_ponto.exportacao import folha as arquivo_da_folha

OBSERVACAO_DE_EMENDA = "Emenda"  # RN06

_PREFIXO_DO_AVISO = {
    Natureza.FERIADO: "Feriado",
    Natureza.FACULTATIVO: "Ponto facultativo",
    Natureza.EMENDA: "Emenda",
    Natureza.EMENDA_SUGERIDA: "Possível emenda",
}


def aviso_do_dia(especial: DataEspecial | None) -> str:
    """UC03 passo 1: "Feriado: Tiradentes", "Possível emenda: Tiradentes (terça, 21/04)"."""
    return f"{_PREFIXO_DO_AVISO[especial.natureza]}: {especial.nome}" if especial else ""


@dataclass(frozen=True)
class PainelDeHoje:
    """O que a aba Hoje mostra (UC01)."""

    data: date
    lancamento: Lancamento | None
    aviso: str
    proxima: Marcacao | None          # o botão "Registrar …"; None = todas preenchidas (E2)

    @property
    def marcacoes(self) -> Marcacoes:
        return self.lancamento.marcacoes if self.lancamento else Marcacoes()


@dataclass(frozen=True)
class FormularioDoDia:
    """O formulário do UC02, já preenchido com o lançamento ou com a sugestão (RN06)."""

    data: date
    tipo: TipoDia
    textos: dict[str, str]
    observacao: str
    existe: bool
    aviso: str


class Servicos:
    def __init__(self, repo: Repositorio, relogio: Callable[[], datetime] = datetime.now) -> None:
        self.repo = repo
        self._relogio = relogio
        self.preferencias = repo.preferencias()
        self.avisos: list[str] = []   # avisos do calendário (UC06 E1) para a tela mostrar uma vez

    # ---- tempo e calendário ----------------------------------------------------
    def agora(self) -> datetime:
        return self._relogio()

    def hoje(self) -> date:
        return self.agora().date()

    def calendario_do_mes(self, ano: int, mes: int) -> CalendarioDoMes:
        """UC05 → UC06: o ano sem calendário é preparado na primeira visita."""
        preparado = calendario.garantir_ano(self.repo, ano, self.preferencias)
        if preparado and preparado.aviso:
            self.avisos.append(preparado.aviso)
        return self.repo.calendario_do_mes(ano, mes)

    def especial(self, dia: date) -> DataEspecial | None:
        return self.calendario_do_mes(dia.year, dia.month).data_especial(dia)

    def tipo_sugerido(self, dia: date) -> TipoDia:
        return tipo_sugerido(dia, self.especial(dia), self.preferencias.facultativo_e_folga)

    def tirar_avisos(self) -> list[str]:
        avisos, self.avisos = self.avisos, []
        return avisos

    # ---- UC01 ------------------------------------------------------------------
    def painel_de_hoje(self) -> PainelDeHoje:
        hoje = self.hoje()
        lancamento = self.repo.obter(hoje)
        proxima = (lancamento.marcacoes if lancamento else Marcacoes()).proxima_vazia()
        return PainelDeHoje(hoje, lancamento, aviso_do_dia(self.especial(hoje)), proxima)

    def _novo_lancamento_de_hoje(self) -> Lancamento:
        """Marcar horário numa emenda candidata mostra que ela não foi dada: o dia
        nasce como Trabalho e a sugestão é descartada (UC03 passo 3)."""
        hoje = self.hoje()
        especial = self.especial(hoje)
        if especial is not None and especial.natureza is Natureza.EMENDA_SUGERIDA:
            calendario.descartar_emenda(self.repo, hoje)
            return Lancamento(hoje, TipoDia.TRABALHO)
        return Lancamento(hoje, self.tipo_sugerido(hoje))  # UC01 4' (RN06)

    def bater_ponto(self) -> tuple[Lancamento, Marcacao]:
        """UC01: grava a hora atual na próxima marcação vazia de hoje."""
        agora = self.agora()
        atual = self.repo.obter(agora.date())
        if atual is None:
            novo = self._novo_lancamento_de_hoje()
            lancamento, marcacao = bater_ponto(None, agora, novo.tipo)
        else:
            lancamento, marcacao = bater_ponto(atual, agora, atual.tipo)
        self.repo.salvar(lancamento)
        return lancamento, marcacao

    def ajustar_marcacao(self, marcacao: Marcacao, texto: str) -> Lancamento:
        """UC01 3': esqueceu de bater na hora e informa a hora (ex.: 07:45). E1 = RN02."""
        horario = ler_horario(texto, marcacao)
        atual = self.repo.obter(self.hoje()) or self._novo_lancamento_de_hoje()
        return self.repo.salvar(replace(atual, marcacoes=atual.marcacoes.com(marcacao, horario)))

    # ---- UC02, UC03, UC04 --------------------------------------------------------
    def formulario_do_dia(self, dia: date) -> FormularioDoDia:
        especial = self.especial(dia)
        lancamento = self.repo.obter(dia)
        if lancamento is not None:
            return FormularioDoDia(dia, lancamento.tipo, lancamento.marcacoes.como_textos(),
                                   lancamento.observacao, True, aviso_do_dia(especial))
        emenda = especial is not None and especial.natureza in (Natureza.EMENDA, Natureza.EMENDA_SUGERIDA)
        return FormularioDoDia(dia, self.tipo_sugerido(dia), Marcacoes().como_textos(),
                               OBSERVACAO_DE_EMENDA if emenda else "", False, aviso_do_dia(especial))

    def jornada_padrao(self) -> dict[str, str]:
        """UC02 2': Manhã e Tarde com a jornada configurada; Extra vazia."""
        return self.preferencias.jornada.marcacoes().como_textos()

    def salvar_dia(self, dia: date, tipo: TipoDia | str, textos: Mapping[str, str | None],
                   observacao: str = "") -> Lancamento:
        """UC02. Numa emenda candidata, salvar como Folga confirma a emenda e salvar
        com outro tipo a descarta (UC03)."""
        lancamento = Lancamento(dia, TipoDia(tipo), Marcacoes.de_textos(textos), observacao)
        self.repo.salvar(lancamento)
        especial = self.especial(dia)
        if especial is not None and especial.natureza is Natureza.EMENDA_SUGERIDA:
            if lancamento.tipo is TipoDia.FOLGA:
                calendario.confirmar_emenda(self.repo, dia)
            else:
                calendario.descartar_emenda(self.repo, dia)
        return lancamento

    def excluir_dia(self, dia: date) -> bool:
        """UC04. Feriados e emendas ficam: pertencem ao calendário, não ao lançamento."""
        return self.repo.apagar(dia)

    # ---- UC05, UC07, UC08 --------------------------------------------------------
    def mes(self, ano: int, mes: int) -> Mes:
        return Mes(ano, mes, self.repo.listar_mes(ano, mes), self.calendario_do_mes(ano, mes),
                   facultativo_e_folga=self.preferencias.facultativo_e_folga,
                   jornada=self.preferencias.jornada)

    # ---- UC10 --------------------------------------------------------------------
    def datas_manuais(self, ano: int) -> list[DataDoCalendario]:
        datas = self.repo.datas_do_periodo(date(ano, 1, 1), date(ano, 12, 31), incluir_ocultas=True)
        return [d for d in datas if d.origem is Origem.MANUAL]

    def datas_do_ano(self, ano: int) -> list[DataDoCalendario]:
        self.calendario_do_mes(ano, 1)
        return self.repo.datas_do_periodo(date(ano, 1, 1), date(ano, 12, 31), incluir_ocultas=True)

    def cadastrar_data(self, texto_da_data: str, nome: str, natureza: Natureza | str = Natureza.FERIADO,
                       recorrente: bool = False) -> DataDoCalendario:
        return calendario.cadastrar_data(self.repo, ler_data(texto_da_data), nome, Natureza(natureza), recorrente)

    def remover_data(self, dia: date, nome: str) -> bool:
        return calendario.remover_data(self.repo, dia, nome)

    def ocultar_data(self, dia: date, nome: str, oculta: bool = True) -> bool:
        return calendario.ocultar_data(self.repo, dia, nome, oculta)

    # ---- UC06 1', UC11 -----------------------------------------------------------
    def recalcular_calendario(self) -> list[str]:
        """Refaz todos os anos já preparados (ex.: depois de trocar a UF). Devolve os avisos."""
        avisos = []
        for ano in sorted(self.repo.anos_com_calendario()):
            preparado = calendario.preparar_ano(self.repo, ano, self.preferencias)
            if preparado.aviso:
                avisos.append(preparado.aviso)
        return sorted(set(avisos))

    def salvar_preferencias(self, *, uf: str, municipio: str, jornada: Mapping[str, str],
                            facultativo_e_folga: bool, tema: str) -> list[str]:
        """UC11. Trocar a UF ou o facultativo muda o calendário: recalcula na hora."""
        horarios = {m: ler_horario(jornada.get(m.value), m) for m in (
            Marcacao.ENTRADA, Marcacao.SAIDA_ALMOCO, Marcacao.VOLTA_ALMOCO, Marcacao.SAIDA)}
        if any(h is None for h in horarios.values()):
            raise ErroDeValidacao("Preencha os quatro horários da jornada.")
        Marcacoes(**{m.value: h for m, h in horarios.items()})  # RN02 na jornada também
        nova = Preferencias(uf=uf, municipio=municipio, facultativo_e_folga=facultativo_e_folga, tema=tema,
                            jornada=Jornada(**{m.value: h for m, h in horarios.items()}))
        anterior, self.preferencias = self.preferencias, nova
        self.repo.salvar_preferencias(nova)
        if (anterior.uf, anterior.facultativo_e_folga) != (nova.uf, nova.facultativo_e_folga):
            return self.recalcular_calendario()
        return []

    # ---- UC08 2': exportar a folha ------------------------------------------------
    def folha_em_texto(self, ano: int, mes: int) -> tuple[str, str]:
        """(nome do arquivo, conteúdo) da folha em texto."""
        m = self.mes(ano, mes)
        return arquivo_da_folha.nome_do_arquivo(m, "txt"), exportacao.folha_em_texto(m, self.hoje())

    def folha_em_csv(self, ano: int, mes: int) -> tuple[str, str]:
        m = self.mes(ano, mes)
        return arquivo_da_folha.nome_do_arquivo(m, "csv"), exportacao.folha_em_csv(m)

    # ---- UC09 -----------------------------------------------------------------------
    def gerar_backup(self) -> tuple[str, str]:
        """(nome do arquivo, JSON) com tudo o que é do usuário."""
        agora = self.agora().astimezone()
        return arquivo_de_backup.nome_do_arquivo(agora.date()), exportacao.gerar_backup(self.repo.exportar(), agora)

    def ler_backup(self, conteudo: str | bytes) -> Backup:
        """UC09 2': valida e diz quantos dias serão importados. Nada é gravado aqui."""
        return exportacao.ler_backup(conteudo)

    def restaurar(self, backup: Backup, substituir: bool) -> ResultadoDaImportacao:
        """UC09 3'-4'. Depois da importação (atômica), refaz o calendário automático dos
        anos que estavam preparados e dos que o backup menciona."""
        anos = self.repo.anos_com_calendario()
        resultado = self.repo.importar(backup.dados, substituir)
        self.preferencias = self.repo.preferencias()
        anos |= {d.data.year for d in backup.dados.datas_ocultas}
        anos |= {d.data.year for d in backup.dados.datas_manuais if not d.recorrente}
        for ano in sorted(anos):
            preparado = calendario.preparar_ano(self.repo, ano, self.preferencias)
            if preparado.aviso:
                self.avisos.append(preparado.aviso)
        return resultado


def ler_data(texto: str) -> date:
    """DD/MM/AAAA (como o usuário digita) ou AAAA-MM-DD."""
    valor = (texto or "").strip()
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(valor, formato).date()
        except ValueError:
            continue
    raise ErroDeValidacao("Use a data no formato DD/MM/AAAA.")


def escrever_duracao(duracao: timedelta | None) -> str:
    """timedelta → "6h00" (com sinal se negativo, para o saldo)."""
    if duracao is None:
        return ""
    minutos = round(duracao.total_seconds() / 60)
    sinal = "−" if minutos < 0 else ""
    minutos = abs(minutos)
    return f"{sinal}{minutos // 60}h{minutos % 60:02d}"


__all__ = ["FormularioDoDia", "PainelDeHoje", "Servicos", "aviso_do_dia", "escrever_duracao", "ler_data"]
