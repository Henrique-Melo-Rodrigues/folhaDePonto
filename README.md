# Folha de Ponto Pessoal

## A origem do projeto

Todo mês eu enfrento o mesmo problema: preciso preencher a folha de ponto oficial, mas os meus horários estão espalhados em mensagens do WhatsApp ao longo de semanas. Entrada, saída para o almoço, retorno, saída final — tudo anotado em conversas, sem organização, sem histórico estruturado.

No final do mês, juntar essas informações vira um trabalho à parte: rolar o histórico do WhatsApp, tentar lembrar o dia certo, tentar identificar qual mensagem corresponde a qual horário. É repetitivo, cansativo e fácil de errar.

Foi desse problema real que surgiu a ideia deste projeto.

## O que é (v2)

Um **app para o celular, 100% offline**, que:

- registra cada marcação **na hora, com um toque** (entrada, saída almoço, volta, saída e hora extra);
- já sabe os **feriados** (nacionais e de SP), os **pontos facultativos** e sugere as **emendas**;
- aponta as **pendências do mês** (dia útil sem lançamento, dia incompleto);
- mostra o mês **na ordem da folha de papel** (dias 01–31; Manhã, Tarde, Extra), pronto para copiar à mão;
- faz **backup** num arquivo que você guarda onde quiser.

Sem servidor, sem internet, sem conta: os dados ficam num SQLite dentro do app.

## Por que esse projeto

Além de resolver um problema real do dia a dia, este projeto é um ambiente deliberado de aprendizado: arquitetura documentada (TOGAF ADM + ArchiMate), casos de uso, DDD e testes, usando IA como par de programação. A v1 cresceu demais (três pilhas e um orquestrador de agentes); a v2 volta ao essencial. O porquê está no [ADR-002](docs/decisions/ADR-002-app-python-offline-no-celular.md).

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem e pacotes | Python ≥ 3.12 com **uv** |
| Banco | SQLite (`sqlite3` da biblioteca padrão) |
| Feriados | lib [`holidays`](https://pypi.org/project/holidays/), offline |
| Interface | [Flet](https://flet.dev), que gera o APK Android a partir do Python |
| Testes | pytest |

## Documentação

| Documento | Conteúdo |
|---|---|
| [docs/casos-de-uso.md](docs/casos-de-uso.md) | casos de uso UC01–UC11, regras de negócio, requisitos não funcionais |
| [docs/arquitetura/](docs/arquitetura/README.md) | modelo ArchiMate (Archi) com as views de cada fase do ADM e o roadmap |
| [docs/decisions/](docs/decisions/) | ADRs |

## Como rodar

```bash
uv sync          # cria o .venv com as dependências travadas no uv.lock
uv run pytest    # testes
```

## Andamento (roadmap)

- [x] **WP1** Limpar o repositório + ADR-002
- [x] **WP2** Domínio + contrato em Python
- [x] **WP3** Repositório SQLite
- [x] **WP4** Calendário (feriados, facultativos, emendas, Cubatão)
- [ ] **WP5** Telas Flet (Hoje, Mês, Folha, Ajustes)
- [ ] **WP6** Exportação e backup
- [ ] **WP7** APK e CI
