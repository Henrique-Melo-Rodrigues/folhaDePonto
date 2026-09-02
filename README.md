# Folha de Ponto Pessoal

## A origem do projeto

Todo mês eu enfrento o mesmo problema: preciso preencher a folha de ponto oficial, mas os meus horários estão espalhados em mensagens do WhatsApp ao longo de semanas. Entrada, saída para o almoço, retorno, saída final — tudo anotado em conversas, sem organização, sem histórico estruturado.

No final do mês, juntar essas informações vira um trabalho à parte: rolar o histórico do WhatsApp, tentar lembrar o dia certo, tentar identificar qual mensagem corresponde a qual horário. É repetitivo, cansativo e fácil de errar.

Foi desse problema real que surgiu a ideia deste projeto.

## O que é

Um web-app pessoal para registrar os horários de trabalho diariamente, classificar o tipo de cada dia e consultar o histórico do mês de forma organizada — substituindo as anotações soltas do WhatsApp por uma interface simples e acessível de qualquer navegador.

O app permite registrar:

- Horário de entrada
- Saída para o almoço
- Retorno do almoço
- Saída final
- Tipo do dia (trabalho, atividade teórica, folga, compensação, feriado, falta)
- Observações livres

## Por que esse projeto

Além de resolver um problema real do dia a dia, este projeto é um ambiente deliberado de aprendizado e prática de boas práticas de desenvolvimento com o auxílio de IA.

A ideia é construir algo funcional do zero — com arquitetura limpa, testes, segurança e ferramentas modernas — usando IA como par de programação ao longo de todo o processo. Não como atalho, mas como forma de aprender mais rápido e com mais qualidade.

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend web | React + Vite + TypeScript (`src/web`) |
| API | Django + Django REST Framework (`src/backend`) |
| Banco de dados | SQLite via Django ORM |
| Servidor | Django/WhiteNoise (serve API + frontend num só processo) |
| App Android | Flutter + SQLite embarcado, offline (`src/mobile`) |
| Contratos de domínio | JSON + gerador em Python (`contracts/`) |
| Gerenciador de pacotes | uv (backend) / npm (frontend) / pub (mobile) |

## Dois escopos, um domínio

O projeto entrega o mesmo registro de ponto por dois caminhos independentes:

- **Web-app com servidor** (`src/backend` + `src/web`) — o caminho principal.
  O Django guarda os dados e aplica as regras; o React é o cliente. Roda no PC
  ou num celular antigo via Termux, e é acessível de qualquer navegador da rede.
- **App Android offline** (`src/mobile`) — roda inteiro no aparelho, com SQLite
  embarcado. Sem servidor, sem rede e sem chave de API. Existe um adapter HTTP
  opcional para falar com o backend, mas ele só entra num build feito de
  propósito para isso.

Os dois não sincronizam entre si: cada um tem o seu banco. O que eles
compartilham é o **domínio**.

`contracts/time_record.json` é a fonte única do vocabulário — tipos de dia,
campos de horário, status possíveis, formato da hora. O gerador escreve os três
alvos, que são versionados e **nunca editados à mão**:

```bash
python3 contracts/generate.py           # regera os alvos
python3 contracts/generate.py --check   # falha se algum estiver fora de sincronia
```

| Alvo gerado | Consumidor |
|---|---|
| `src/backend/apps/time_records/domain_generated.py` | Django |
| `src/web/src/domain.generated.ts` | React |
| `src/mobile/lib/domain/domain.g.dart` | Flutter |

Backend e mobile implementam as regras de status em linguagens diferentes; os
vetores golden de `contracts/status_cases.json` rodam nos testes dos dois lados
e provam que continuam concordando.

O raciocínio por trás do escopo offline está em
[docs/decisions/ADR-001-mobile-local-first.md](docs/decisions/ADR-001-mobile-local-first.md).

## Arquitetura do backend (camadas em classes)

```
views.py        → recebe HTTP, valida e delega (APIView)
serializers.py  → valida e normaliza o input
services.py     → regras de negócio (TimeRecordService)
repositories.py → acesso ao SQLite via ORM (TimeRecordRepository)
models.py       → modelo TimeRecord
```

## Como rodar localmente

Backend (porta 8000):

```bash
cd src/backend
cp .env.example .env   # preencha SECRET_KEY e API_KEY
uv sync
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8000
```

Frontend em modo dev (porta 5173, com proxy para a API):

```bash
cd src/web
npm install
npm run dev
```

Ou tudo numa porta só (como em produção): `npm run build` em `src/web` e
acesse direto `http://localhost:8000` — o Django serve o build.

Na primeira visita o app pede a chave de API (`API_KEY` do `.env`).

## Rodando num celular antigo (Termux + SSH)

Veja o passo a passo completo em [DEPLOY.md](DEPLOY.md).

## Endpoints da API

```
GET    /api/health/
POST   /api/time-records/
GET    /api/time-records/today/
GET    /api/time-records/month/?year=YYYY&month=M
GET    /api/time-records/<date>/
PUT    /api/time-records/<date>/
DELETE /api/time-records/<date>/
```

Todos os endpoints (exceto `/health`) exigem o header:

```
X-Api-Key: <sua chave do .env>
```
