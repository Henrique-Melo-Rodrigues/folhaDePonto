# Casos de uso: Folha de Ponto Pessoal (v2, app offline)

Especificação dos casos de uso da refatoração. Formato segundo as notas
*Casos de uso* e *Especificação de requisitos* do vault (ISO/IEC 29148, slide 50
do Tópico 4): diagrama para a visão geral e especificação textual para os detalhes.
O fonte do diagrama em PlantUML está em [`casos-de-uso.puml`](casos-de-uso.puml).

## 0. Contexto e decisões já tomadas

**Problema (análise de negócio / ConOps):** os horários do dia (entrada, saída
para o almoço, volta, saída) ficam espalhados em mensagens do WhatsApp. No fim do
mês, preencher a folha de ponto oficial vira um garimpo, e é fácil errar.
Feriados e emendas pioram a situação: é preciso lembrar quais dias não eram úteis.

| # | Decisão | Origem |
|---|---|---|
| D1 | O app roda **inteiro no celular**, com banco **SQLite local**. Sem servidor, sem celular velho, sem rede. | usuário, 05/11/2026 |
| D2 | O projeto é em **Python, gerenciado com uv**. | usuário |
| D3 | O calendário do Brasil vem de uma fonte **offline**: a biblioteca `holidays` (testada na v0.108). Ela traz os feriados nacionais e estaduais (`subdiv="SP"`) e, na categoria `optional`, os pontos facultativos: Carnaval, Quarta de Cinzas, Corpus Christi, Dia do Servidor e as vésperas de Natal e Ano-Novo. | a rede da empresa bloqueia APIs externas |
| D4 | **Feriados municipais (Cubatão/SP) e emendas da empresa** não existem em nenhuma fonte pronta, então o usuário os cadastra à mão (UC10). | a lib cobre só nação e estado |
| D5 | A **folha oficial é de papel, preenchida à mão**. Tem uma linha por dia (01 a 31 corridos) e as colunas **Manhã** (entrada/saída), **Tarde** (entrada/saída) e **Extra** (entrada/saída). O layout do app importa pouco: o valor está em ter tudo junto, na ordem da folha. | usuário + PDF de exemplo (ignorado no git) |
| D6 | **Emenda é folga.** Não existe tipo de dia novo: uma emenda confirmada vira um lançamento *Folga* com a observação "Emenda (feriado …)". | usuário, 05/11/2026 |
| D7 | **Jornada padrão** da folha: 07:45–12:00 e 13:00–14:45, de segunda a sexta (6 h/dia). | PDF de exemplo |

> **Proposta de tecnologia para a UI (a confirmar na Fase D do ArchiMate):**
> [Flet](https://flet.dev), um framework Python que gera APK Android com
> `flet build apk` e funciona com projetos uv. `sqlite3` e `holidays` são Python
> puro ou da biblioteca padrão, e rodam dentro do APK.

## 1. Atores

| Ator | Tipo | Papel |
|---|---|---|
| **Trabalhador** | primário, humano | anota os próprios horários e no fim do mês passa tudo para a folha oficial. É o único usuário: não há login. |
| **Calendário oficial do Brasil** | secundário, sistema | fornece os feriados nacionais e estaduais e os pontos facultativos de um ano. Implementado pela lib `holidays`, embarcada e offline. |
| **Tempo** | primário, convenção UML | dispara o preparo do calendário na virada do ano, ou quando o app abre num ano ainda não preparado. |

## 2. Diagrama

```
                 ┌──────────────────── Folha de Ponto (app no celular) ────────────────────┐
                 │                                                                         │
                 │   (UC01 Bater ponto agora)                                              │
                 │   (UC02 Lançar dia manualmente) ◄┄┄«extend»┄┄ (UC03 Classificar dia     │
                 │            ▲                                     como feriado/emenda)  │
                 │            ┆«extend» (dia já lançado)                                    │
                 │   (UC04 Excluir lançamento)                                             │
  Trabalhador ───┼── (UC05 Consultar mês) ◄┄┄┄«extend»┄┄┄ (UC06 Preparar calendário ──────┼──► Calendário
      │          │        │                    (ano sem calendário)  do ano)           │    oficial do
      │          │        └┄┄«include»┄┄► (UC07 Conferir pendências do mês)              │    Brasil
      │          │   (UC08 Ver folha p/ cópia)    ┄┄«include»┄┄► (UC07)                    │
      │          │   (UC09 Fazer backup / restaurar)                                       │
      │          │   (UC10 Cadastrar feriado local ou emenda)                               │
      │          │   (UC11 Configurar preferências)                                        │
                 │                          ▲                                              │
     Tempo ──────┼──────────────────────────┘ (UC06, na virada do ano)                     │
                 └─────────────────────────────────────────────────────────────────────────┘
```

Todos os casos, exceto UC06 quando disparado pelo Tempo, são iniciados pelo
Trabalhador. Por legibilidade, o desenho não mostra uma linha do Trabalhador
para cada elipse.

## 3. Lista e prioridade

| ID | Caso de uso | Prioridade | Existe hoje? | Observação |
|---|---|---|---|---|
| UC01 | Bater ponto agora | **Alta** | não | é o uso real: uma anotação de 10 segundos, na hora |
| UC02 | Lançar dia manualmente | **Alta** | sim (formulário) | mantido; ganha validação de ordem dos horários |
| UC03 | Classificar dia como feriado/emenda | **Alta** | parcial (tipo de dia manual) | passa a vir sugerido pelo calendário |
| UC04 | Excluir lançamento | Média | sim | mantido |
| UC05 | Consultar mês | **Alta** | sim (calendário web) | ganha feriados, emendas e totais |
| UC06 | Preparar calendário do ano | **Alta** | não | offline, pela lib `holidays` |
| UC07 | Conferir pendências do mês | **Alta** | não | dia útil sem lançamento, dia incompleto |
| UC08 | Ver folha do mês para cópia | **Alta** | não | é o que resolve o fim do mês: a ordem da folha de papel |
| UC09 | Fazer backup / restaurar | Média | não | o ADR-001 já apontava como "próximo passo" |
| UC10 | Cadastrar feriado local ou emenda | Média | não | municipal e da empresa |
| UC11 | Configurar preferências | Baixa | parcial (tema) | UF, município, jornada, tema |

## 4. Especificação textual

### UC01 · Bater ponto agora
| Campo | Conteúdo |
|---|---|
| **Descrição** | Com um toque, o Trabalhador registra a hora atual na próxima marcação vazia do dia. |
| **Atores** | Trabalhador |
| **Gatilho** | O Trabalhador chega, sai para o almoço, volta ou vai embora. |
| **Pré-condição** | O app está instalado. Não precisa haver lançamento do dia. |
| **Fluxo principal** | 1. O Trabalhador abre o app na aba **Hoje**. 2. O sistema mostra as marcações do dia (Manhã e Tarde; Extra, se houver) e destaca a próxima vazia (ex.: "Registrar **Entrada**"). 3. O Trabalhador toca no botão. 4. O sistema grava a hora atual, arredondada ao minuto, nessa marcação (RN01) e recalcula o status (RN03). 5. O sistema mostra a marcação gravada e o próximo botão ("Registrar **Saída almoço**"). |
| **Fluxo alternativo** | 4'. O dia ainda não tinha lançamento: o sistema cria o lançamento com o tipo sugerido pelo calendário (RN06) e grava a marcação. |
| **Fluxo alternativo** | 3'. O Trabalhador esqueceu de bater na hora: toca na marcação, ajusta a hora (ex.: 07:45) e confirma. Segue no passo 4 com a hora informada. |
| **Fluxo alternativo** | 3''. **Hora extra**: depois da saída da tarde, o botão vira "Registrar **Entrada extra**" e depois "**Saída extra**". |
| **Situações de erro** | E1: a hora informada no 3' quebra a ordem das marcações (RN02). E2: as quatro marcações normais e as duas extras já estão preenchidas. |
| **Estado em caso de erro** | E1: nada é gravado e o sistema mostra qual marcação conflita. E2: o botão some e a ação vira "Editar dia" (UC02). |
| **Pós-condição** | A marcação está gravada no SQLite do aparelho e o status do dia foi atualizado. |
| **Regras** | RN01, RN02, RN03, RN06 |

### UC02 · Lançar dia manualmente
| Campo | Conteúdo |
|---|---|
| **Descrição** | O Trabalhador cria ou corrige o lançamento de qualquer data: tipo do dia, horários (Manhã, Tarde e Extra) e observações. |
| **Atores** | Trabalhador |
| **Gatilho** | Tocar num dia do calendário (UC05) ou em "Editar dia" na aba Hoje. |
| **Pré-condição** | — |
| **Fluxo principal** | 1. O sistema abre o formulário da data, preenchido com o lançamento existente ou com o tipo sugerido (RN06). 2. O Trabalhador escolhe o tipo do dia e preenche ou ajusta os horários e as observações. 3. O Trabalhador toca em **Salvar**. 4. O sistema valida (RN01, RN02), normaliza os horários vazios para "sem horário", calcula o status (RN03) e grava. Na primeira gravação guarda o `created_at`; nas seguintes atualiza só o `updated_at`. 5. O sistema volta para a tela de origem já atualizada. |
| **Fluxo alternativo** | 2'. **Preencher jornada padrão**: o Trabalhador toca em "Usar jornada padrão" e o sistema preenche Manhã e Tarde com a jornada configurada em UC11 (07:45 · 12:00 · 13:00 · 14:45). Extra fica vazia. |
| **Ponto de extensão** | *tipo do dia*: UC03 |
| **Situações de erro** | E1: horário fora do formato HH:MM ou fora de 00:00–23:59. E2: marcações fora de ordem (RN02). |
| **Estado em caso de erro** | O formulário continua aberto, com o campo inválido destacado. Nada é gravado. |
| **Pós-condição** | Existe exatamente um lançamento para a data (RN04). |
| **Regras** | RN01–RN04, RN06 |

### UC03 · Classificar dia como feriado ou emenda (estende UC02 e UC05)
| Campo | Conteúdo |
|---|---|
| **Descrição** | Quando a data é feriado, ponto facultativo ou candidata a emenda, o sistema sugere o tipo do dia e o Trabalhador confirma ou troca. |
| **Atores** | Trabalhador |
| **Condição de extensão** | A data aparece no calendário do ano (UC06/UC10) ou casa com a regra de emenda (RN05). |
| **Fluxo principal** | 1. O sistema mostra um aviso no formulário ou no calendário: "Feriado: Tiradentes" ou "Possível emenda (feriado na terça, 21/04)". 2. O tipo do dia já vem pré-selecionado: *Feriado* para feriados; *Folga* para emendas candidatas, com a observação "Emenda (feriado …)". 3. O Trabalhador confirma, ou troca para *Trabalho*, caso a empresa não tenha dado a emenda. |
| **Pós-condição** | O lançamento tem o tipo escolhido. Uma emenda confirmada é registrada como emenda no calendário e passa a contar como dia não útil (RN07). |
| **Regras** | RN05, RN06, RN07 |

### UC04 · Excluir lançamento (estende UC02)
| Campo | Conteúdo |
|---|---|
| **Descrição** | Apaga o lançamento de uma data. |
| **Condição de extensão** | O dia aberto em UC02 já tem lançamento. |
| **Fluxo principal** | 1. O Trabalhador toca em **Excluir**. 2. O sistema pede confirmação mostrando a data. 3. O Trabalhador confirma. 4. O sistema apaga o lançamento e volta ao calendário. |
| **Fluxo alternativo** | 3'. O Trabalhador cancela: nada muda. |
| **Pós-condição** | A data volta a não ter lançamento. Feriado e emenda continuam aparecendo no calendário, porque pertencem ao calendário e não ao lançamento. |

### UC05 · Consultar mês
| Campo | Conteúdo |
|---|---|
| **Descrição** | Mostra o mês em grade de calendário, mantendo o layout atual do web: cor por status, horários dentro da célula e legenda. Agora a grade também marca feriados e emendas e mostra os totais do mês. |
| **Atores** | Trabalhador |
| **Gatilho** | Abrir a aba **Mês**. |
| **Fluxo principal** | 1. O sistema abre no mês corrente. 2. Para cada dia, mostra o número, os horários ou o rótulo do tipo, e a cor do status. Feriados e pontos facultativos aparecem com o nome; emendas candidatas, com um marcador próprio. 3. O sistema inclui UC07 e mostra o resumo: dias úteis, dias lançados, pendências e horas trabalhadas (RN08). 4. O Trabalhador navega com ‹ › entre meses ou toca num dia (→ UC02). |
| **Ponto de extensão** | *ano sem calendário*: UC06 · *dia com emenda candidata*: UC03 |
| **Pós-condição** | Nenhuma alteração de dados. |
| **Regras** | RN05, RN07, RN08 |

### UC06 · Preparar calendário do ano
| Campo | Conteúdo |
|---|---|
| **Descrição** | Gera e guarda no SQLite os feriados e pontos facultativos de um ano para a UF configurada, sem usar rede. |
| **Atores** | Tempo ou Trabalhador (iniciam); Calendário oficial do Brasil (secundário). |
| **Gatilho** | Abrir o app ou navegar para um ano ainda não preparado, ou a virada do ano. |
| **Fluxo principal** | 1. O sistema percebe que o ano *A* não tem calendário. 2. O sistema pede ao Calendário oficial os feriados de *A* para a UF configurada, nas categorias `public` e `optional`. 3. O sistema grava cada data com nome, origem (`nacional`, `estadual`, `facultativo`) e versão da lib. 4. O sistema calcula as emendas candidatas (RN05) e as guarda como sugestões. |
| **Fluxo alternativo** | 1'. O Trabalhador toca em "Recalcular calendário" (ex.: depois de trocar a UF ou atualizar o app). O sistema refaz os passos 2–4 e preserva os itens cadastrados à mão (UC10) e as emendas já confirmadas. |
| **Situações de erro** | E1: a UF configurada não existe na lib. |
| **Estado em caso de erro** | O sistema usa só os feriados nacionais e avisa para revisar a UF (UC11). |
| **Pós-condição** | O ano *A* tem calendário local, e o app funciona sem rede para sempre nesse ano. |
| **Regras** | RN05, RN09 |

### UC07 · Conferir pendências do mês (incluído por UC05 e UC08)
| Campo | Conteúdo |
|---|---|
| **Descrição** | Lista o que impede a folha do mês de estar fechada. |
| **Fluxo principal** | 1. O sistema percorre os dias do mês até hoje. 2. Para cada um, classifica: **dia útil sem lançamento**, **lançamento incompleto** (RN03) ou **emenda pendente de confirmação**. 3. O sistema devolve a lista ordenada por data, e cada item abre UC02. |
| **Pós-condição** | Nenhuma alteração de dados. |
| **Regras** | RN03, RN05, RN07 |

### UC08 · Ver folha do mês para cópia
| Campo | Conteúdo |
|---|---|
| **Descrição** | Mostra o mês **na mesma ordem da folha de papel**, para o Trabalhador copiar à mão de uma só vez. Opcionalmente exporta como texto ou CSV. |
| **Atores** | Trabalhador |
| **Gatilho** | No fim do mês, com a folha de papel na mão, tocar em **Folha** na aba Mês. |
| **Fluxo principal** | 1. O sistema inclui UC07. Se houver pendências, mostra quantas são e oferece "Resolver" ou "Ver mesmo assim". 2. O sistema mostra uma tabela com uma linha por dia, **01 a 31 corridos**, e as colunas `DIA · MANHÃ entrada · MANHÃ saída · TARDE entrada · TARDE saída · EXTRA entrada · EXTRA saída · observação`. Em fim de semana, feriado, folga ou emenda, os horários ficam vazios e a observação mostra o motivo (ex.: `21 · — · Feriado: Tiradentes`). 3. O Trabalhador copia linha a linha; cada linha tocada fica marcada como "copiada" para ele não se perder. |
| **Fluxo alternativo** | 2'. **Exportar**: tocar em "Compartilhar" gera o mesmo conteúdo em texto ou CSV e abre o menu de compartilhamento do Android. |
| **Fluxo alternativo** | 1'. O Trabalhador escolhe "Resolver": o sistema abre a lista de UC07. |
| **Pós-condição** | Nenhuma alteração nos lançamentos. A marca de "copiada" é só visual e reinicia ao trocar de mês. |
| **Regras** | RN07, RN08, RN10 |

### UC09 · Fazer backup / restaurar
| Campo | Conteúdo |
|---|---|
| **Descrição** | Copia todos os dados para um arquivo e restaura a partir dele. Sem isso, perder ou trocar o celular perde o histórico (consequência do ADR-001). |
| **Atores** | Trabalhador |
| **Fluxo principal (backup)** | 1. Tocar em **Fazer backup**. 2. O sistema gera um arquivo JSON versionado, com lançamentos, feriados locais, emendas confirmadas e preferências. 3. O sistema abre o menu de compartilhamento (Drive, e-mail, pasta Downloads). |
| **Fluxo alternativo (restaurar)** | 1'. Tocar em **Restaurar** e escolher o arquivo. 2'. O sistema valida a versão e o formato e mostra quantos dias serão importados. 3'. O Trabalhador escolhe **substituir tudo** ou **mesclar**; ao mesclar, prevalece o lançamento com o `updated_at` mais recente. 4'. O sistema importa numa transação única. |
| **Situações de erro** | E1: arquivo inválido ou de versão desconhecida. |
| **Estado em caso de erro** | Nada é importado (*rollback*). |
| **Pós-condição** | backup: existe um arquivo com todos os dados. restaurar: o banco reflete o arquivo. |

### UC10 · Cadastrar feriado local ou emenda
| Campo | Conteúdo |
|---|---|
| **Descrição** | Inclui no calendário datas que nenhuma fonte pronta conhece: feriado municipal (ex.: aniversário da cidade) ou emenda dada pela empresa. |
| **Atores** | Trabalhador |
| **Fluxo principal** | 1. Em Preferências ▸ Calendário, tocar em **Adicionar data**. 2. Informar a data, o nome, o tipo (*feriado municipal* ou *emenda*) e se repete todo ano. 3. O sistema grava com origem `manual`. |
| **Fluxo alternativo** | 1'. Remover ou editar uma data manual. Datas vindas da lib não podem ser apagadas, só ocultadas. |
| **Pós-condição** | A data aparece no calendário e entra nos cálculos de dia útil (RN07). |

### UC11 · Configurar preferências
| Campo | Conteúdo |
|---|---|
| **Descrição** | Ajusta o que muda de pessoa para pessoa. |
| **Fluxo principal** | O Trabalhador define: **UF** (padrão SP) e **município** (só o nome, usado nos feriados manuais); **jornada padrão** (padrão: 07:45 · 12:00 · 13:00 · 14:45, de segunda a sexta), usada em UC02 2' e para calcular o saldo; **considerar pontos facultativos como folga** (sim/não; **padrão: sim**); **tema** claro/escuro. |
| **Pós-condição** | Preferências gravadas no SQLite. Trocar a UF oferece recalcular o calendário (UC06 1'). |

## 5. Regras de negócio

| ID | Regra | Origem |
|---|---|---|
| RN01 | Horário no formato `HH:MM`, entre 00:00 e 23:59. Vazio = sem horário. Marcações: `entrada`, `saida_almoco`, `volta_almoco`, `saida`, `entrada_extra`, `saida_extra`. | `dominio/vocabulario.py` + folha oficial |
| RN02 | **Proposta nova:** as marcações preenchidas seguem a ordem entrada < saída almoço < volta almoço < saída < entrada extra < saída extra. Marcações vazias no meio são permitidas. Saída extra exige entrada extra; entrada extra sozinha é hora extra em andamento (não conta horas). | lacuna atual: o app aceita saída antes da entrada |
| RN03 | Status: tipo **não trabalhado** e nenhum horário → `não trabalhado`. Os quatro horários normais preenchidos → `completo` (a extra não influi). Qualquer outro caso → `incompleto`. | herdada da v1; vetores golden em `tests/dados/casos_status.json` |
| RN04 | Um lançamento por data (upsert). `created_at` é preservado na edição. | atual |
| RN05 | **Emenda candidata:** feriado na **terça** → a segunda anterior. Feriado na **quinta** → a sexta seguinte. Só se o dia candidato for útil. Ex. 2026: 02/01 (sex), 20/04 (seg), 05/06 (sex, Corpus Christi), 10/07 (sex). É sugestão: só vira emenda quando confirmada (UC03) ou cadastrada (UC10). Emenda confirmada = **folga** (D6). | usuário, confirmado |
| RN06 | Tipo sugerido ao criar um lançamento: feriado → *Feriado*; ponto facultativo (preferência ligada) → *Folga* (obs. nome do facultativo); emenda confirmada → *Folga* (obs. "Emenda"); sábado ou domingo → *Folga*; senão → *Trabalho*. | novo |
| RN07 | **Dia útil** = segunda a sexta que não é feriado nem emenda confirmada. Ponto facultativo **também não é dia útil** (é folga), a menos que a preferência seja desligada (UC11). | usuário, 05/11/2026 |
| RN08 | Horas do dia = (saída almoço − entrada) + (saída − volta almoço) + (saída extra − entrada extra), calculadas só em dias `completo`. Saldo = horas − jornada padrão (6 h). | novo |
| RN10 | A folha lista **todos** os dias do mês, de 01 ao último, inclusive fins de semana. | folha oficial |
| RN09 | A fonte do calendário fica registrada (`nacional`, `estadual`, `facultativo`, `manual`) junto com a versão da lib, para dar para explicar por que um dia é feriado. | rastreabilidade |

Tipos de dia: os sete atuais (`trabalho`, `atividade_teorica`, `folga`,
`compensacao`, `feriado`, `falta`, `outro`). Nenhum tipo novo: emenda é folga
(D6). O vocabulário fica em `src/folha_ponto/dominio/vocabulario.py` (enums
`TipoDia`, `Status`, `Marcacao`), com os dois campos de hora extra.

## 6. Requisitos não funcionais

| ID | Requisito |
|---|---|
| RNF01 | **100% offline:** o APK não pede a permissão `INTERNET`, e um teste reprova qualquer import de rede no código do app (evolução do `no_network_offline_test.dart`). |
| RNF02 | **Python ≥ 3.12 com uv:** `pyproject.toml` + `uv.lock`; `uv run` para rodar e testar no PC; `uv run flet build apk` para gerar o APK. |
| RNF03 | **Dados locais:** um arquivo SQLite na área privada do app, com migrações versionadas (`PRAGMA user_version`). |
| RNF04 | **Rapidez:** UC01 em até 2 toques a partir do ícone do app; abertura em menos de 2 s num aparelho de entrada. |
| RNF05 | **Regras testáveis sem UI:** domínio e calendário em Python puro, cobertos por `pytest`, com os vetores golden do contrato. |
| RNF06 | **Layout simples:** o layout não é prioridade (D5). Basta ser legível com uma mão: abas Hoje / Mês / Folha e botões grandes. Se der, reaproveitar a paleta de cores do web atual. |

## 7. Rastreabilidade com o sistema atual (gap analysis)

| Hoje (baseline) | Alvo (target) | Operação |
|---|---|---|
| Regras de status (Python + Dart duplicado) | só Python | **keep** + eliminar a duplicata |
| Contrato `time_record.json` + gerador para 3 linguagens | vocabulário como módulo Python (`dominio/vocabulario.py`) | **keep** (simplificado) |
| Django + DRF + API key + WhiteNoise | — | **eliminate** |
| React/Vite (layout) | UI em Python (Flet) com o mesmo desenho | eliminate + **create** |
| Flutter + sqflite + adapter remoto | — | **eliminate** |
| Celular velho como servidor (Termux, SSH) | — | **eliminate** |
| Mongo / Docker / Caddy (restos) | — | **eliminate** |
| — | UC01, UC06, UC07, UC08, UC09, UC10 | **create** |

## 8. Perguntas em aberto

| # | Pergunta | Situação |
|---|---|---|
| 1 | A regra de emenda (terça→segunda, quinta→sexta) e "emenda = folga"? | **respondida:** emenda é folga (D6) |
| 2 | Município? | **respondida:** Cubatão/SP. Os feriados municipais entram por UC10; as datas ainda precisam ser confirmadas pelo usuário. |
| 3 | Formato da folha oficial? | **respondida:** papel, preenchida à mão, Manhã/Tarde/Extra, dias 01–31 (D5) |
| 4 | Pontos facultativos (Carnaval, Corpus Christi, Dia do Servidor) contam como folga? | **respondida:** sim, são folga. Continua como preferência (UC11), **ligada por padrão**. |
