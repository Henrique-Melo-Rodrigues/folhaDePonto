# ADR-001: App mobile local-first, com o domínio saindo de um contrato único

## Status

Accepted

## Date

2026-09-01

## Context

O app Flutter em `src/mobile` nasceu como um cliente HTTP fino do backend Django:
toda tela chamava `/api/time-records/...`, e o `API_BASE_URL`/`API_KEY` entravam
em tempo de build via `--dart-define`. Isso trazia três problemas:

- **Depende de servidor no ar.** Para anotar o horário de entrada às 07:45 era
  preciso ter o Django rodando (no PC da mesma rede ou no celular via Termux) e
  o aparelho na rede certa. O uso real é o oposto disso: um aparelho, no bolso,
  em qualquer lugar, para uma anotação de dez segundos.
- **Build acoplado ao ambiente.** O IP da máquina virava parte do APK. Um APK
  publicado pelo CI só servia para quem tivesse aquele IP e aquela chave.
- **Regras de negócio só no backend.** `calculate_status`, a normalização de
  horários em branco e a validação `HH:MM` viviam em `services.py` e
  `serializers.py`. Sem servidor, o app não sabia sequer dizer se o dia estava
  completo.

Ao mesmo tempo, o backend e o web-app continuam existindo e são o caminho
principal do projeto — o mobile não os substitui. Qualquer regra que o app
passasse a executar sozinho precisaria concordar com a do servidor, ou os dois
lados divergiriam em silêncio.

## Decision

Tornar o mobile **local-first e offline por default**, e extrair o vocabulário
do domínio para um **contrato único versionado**.

1. **Offline é o default.** O app roda inteiro no aparelho, com SQLite embarcado
   (`sqflite`). Não há rede no caminho normal de uso.
2. **Portas e adapters.** As telas conhecem só a porta `TimeRecordStore`
   (`lib/data/time_record_store.dart`). Duas implementações:
   `LocalTimeRecordStore` (SQLite, default) e `RemoteTimeRecordStore` (HTTP,
   opt-in). `lib/main.dart` é o composition root: `buildStore()` só devolve o
   adapter remoto quando o build define `API_BASE_URL`.
3. **Regras portadas para `lib/domain/`.** `calculateStatus`, `normalizeTimes` e
   `validateTime` espelham o backend, e o adapter local as executa no aparelho.
4. **Contrato único.** `contracts/time_record.json` é a fonte da verdade do
   vocabulário (tipos de dia, campos de horário, status, padrão de hora).
   `contracts/generate.py` gera três alvos versionados —
   `domain_generated.py` (backend), `domain.generated.ts` (web) e
   `domain.g.dart` (mobile). Nenhum dos três é editado à mão.
5. **Paridade provada por vetores golden.** `contracts/status_cases.json` é
   rodado pelos testes dos dois lados (`tests/test_services.py` no Python e
   `test/domain/status_test.dart` no Dart). Se as implementações divergirem, os
   dois lados não podem passar ao mesmo tempo.

## Alternatives Considered

### Manter o app como cliente HTTP puro (status quo)

- Prós: uma única implementação das regras; zero risco de divergência.
- Contras: inutilizável sem servidor no ar e sem a rede certa — exatamente o
  cenário de uso do app.
- Rejeitado: o problema que o projeto resolve é anotar horário na hora em que
  ele acontece, não quando o servidor está disponível.

### Portar as regras para Dart à mão, sem contrato nem gerador

- Prós: bem mais simples; nada de gerador, JSON de contrato ou CI extra.
- Contras: as listas de tipos de dia e de status passariam a existir em três
  lugares (Python, TypeScript, Dart). O drift seria silencioso: um tipo de dia
  novo no backend não quebraria nada no mobile — só produziria um rótulo errado
  ou um status incoerente meses depois.
- Rejeitado: o custo do gerador é pago uma vez; o custo do drift é pago para
  sempre, e sem aviso.

### Remover a rede de vez (apagar o adapter remoto e a dependência `http`)

- Prós: escopo mínimo e garantia estrutural — sem `package:http` no `pubspec`,
  não há como o app falar rede.
- Contras: jogaria fora o caminho de volta ao servidor. O backend e o web
  continuam sendo o produto principal, e um sync futuro (ou simplesmente usar o
  app contra o Django de casa) exigiria reescrever o adapter do zero.
- Rejeitado: dá para ter as duas coisas. O adapter remoto fica isolado num único
  arquivo, nunca é montado sem `--dart-define`, e `test/no_network_offline_test.dart`
  falha se qualquer outro arquivo de `lib/` mencionar rede.

## Consequences

- **Os dados vivem só no aparelho, sem backup.** Desinstalar o app ou perder o
  celular perde o histórico. **Export/import fica explicitamente fora de escopo
  aqui e é o próximo passo** — é o que transforma "sem backup" em "backup
  manual".
- **Sync entre mobile e servidor está fora de escopo.** Os dois lados guardam o
  mesmo documento (inclusive o mesmo `user_id`, `usuario_001`), o que deixa a
  porta aberta, mas não existe reconciliação: hoje são bancos independentes.
- **As regras existem em duas linguagens.** É uma duplicação assumida, e os
  vetores golden são a rede de segurança que a torna sustentável.
- **Mudar o vocabulário virou um passo deliberado**: editar
  `contracts/time_record.json` e rodar `python3 contracts/generate.py`. O
  workflow `contracts.yml` reprova o PR que esquecer disso.
- **O APK publicado pelo CI é o offline**, sem `--dart-define` e sem secrets de
  API. Quem quiser o modo remoto faz um build local.
- **O schema do SQLite do app é escrito à mão** (`time_record_dao.dart`), fora
  do gerador: mudança de schema é migração deliberada, não efeito colateral de
  uma linha no JSON do contrato.
