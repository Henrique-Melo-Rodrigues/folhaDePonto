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
| Gerenciador de pacotes | uv (backend) / npm (frontend) |

> O app Flutter original ainda está em `src/mobile`, mas o caminho principal agora é o web-app.

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
