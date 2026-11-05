# ADR-002: Um só app Python, offline, rodando no celular

## Status

Accepted. Substitui o [ADR-001](ADR-001-mobile-local-first.md).

## Date

2026-11-05

## Context

O ADR-001 tornou o app Flutter offline, mas manteve o Django + React como
"caminho principal". O resultado foram três pilhas para um app de uma pessoa:

- **Django + DRF + React**, servido por um celular velho com Termux. Só funciona
  na Wi-Fi de casa, e a rede da empresa bloqueia o acesso.
- **Flutter + sqflite**, com as regras de status reescritas em Dart. O Flutter nem
  está instalado na máquina de desenvolvimento, então o app só era verificado no CI.
- Um **gerador de contratos** para três linguagens, vetores golden para provar
  que Python e Dart concordam, um **orquestrador multi-CLI** com 23 skills
  copiadas, e restos de um plano com MongoDB/Docker que nunca foi usado.

Enquanto isso, o problema real (README) continuava sem solução: no fim do mês,
os horários e os feriados ainda precisavam ser garimpados para preencher a
**folha de papel**, preenchida à mão (dias 01–31; Manhã, Tarde e Extra).

## Decision

1. **Um app só, no celular, sem servidor.** Dados num SQLite local; nenhum
   caminho de uso depende de rede (RNF01: um teste reprova import de rede).
2. **Python com uv** em tudo: domínio, calendário, persistência e interface.
   `pyproject.toml` + `uv.lock` na raiz; layout `src/folha_ponto/`.
3. **Interface em Flet**, que gera o APK a partir do Python. A troca fica
   restrita a `folha_ponto/ui/`: as regras não dependem dela.
4. **Calendário offline** pela lib `holidays` (BR + SP, incluindo os pontos
   facultativos). Feriados de Cubatão e emendas da empresa são cadastrados pelo
   usuário. **Emenda = folga. Ponto facultativo = folga por padrão**, com uma
   preferência para desligar.
5. **O contrato fica** (`contracts/time_record.json` + `status_cases.json`),
   mas passa a ser lido direto pelo Python. O gerador de 3 linguagens sai.
6. **Arquitetura documentada em ArchiMate** (`docs/arquitetura/`), seguindo o
   TOGAF ADM, com casos de uso em `docs/casos-de-uso.md`.

## Alternatives Considered

### Manter o Django e rodar o servidor no próprio celular (localhost + PWA)
- Prós: reaproveita backend e layout React.
- Contras: continua com duas linguagens (Python + TypeScript), exige Termux
  aberto e um servidor rodando para anotar um horário.
- Rejeitado: o usuário quer um app que simplesmente abra e funcione.

### Manter o Flutter offline e usar Python só no tooling
- Prós: o app offline já existia e tinha testes.
- Contras: as regras ficam em Dart (fora do Python + uv pedido), e o Flutter
  não está instalado na máquina de desenvolvimento.
- Rejeitado.

### BrasilAPI para os feriados
- Prós: dados oficiais atualizados.
- Contras: precisa de internet (bloqueada na empresa) e só traz feriados
  nacionais, sem pontos facultativos nem emendas.
- Rejeitado como fonte principal; a lib `holidays` calcula tudo offline.

## Consequences

- Removidos: `src/backend`, `src/web`, `src/mobile`, `contracts/generate.py`,
  orquestrador (`orchestrator.sh`, `scripts/`, `GEMINI.md`, `gemini-code.md`,
  `antigravity.rules.md`, `AGENTS.md`, `agents/`), `skills/`, `.claude-plugin/`,
  `.claude/commands/`, os 3 workflows do CI, `DEPLOY.md` e os documentos do plano
  MongoDB. Tudo continua recuperável pelo histórico do git (último commit da v1:
  `cd0760a`).
- **Não há migração de dados** da v1: os bancos do servidor e do Flutter não
  existem nesta máquina. Se algum aparecer, um importador JSON entra pelo UC09.
- O backup deixa de ser "próximo passo" e vira caso de uso (UC09).
- A regra de status volta a existir **numa linguagem só**; os vetores golden
  continuam como teste de regressão.
- O CI volta no WP7 (pytest + build do APK), num workflow só.
- Risco: o `flet build apk` precisa do SDK Android/Flutter na máquina ou no CI.
  O plano (`docs/arquitetura/README.md`) mitiga isso: as transições 1 e 2
  funcionam no PC antes do APK existir.
