# Backend - Folha de Ponto

API Django/DRF com SQLite para a folha de ponto pessoal. Também serve o build
do frontend web (`src/web/dist`) via WhiteNoise — em produção basta Python.

## Desenvolvimento local com uv

```bash
cd src/backend
cp .env.example .env   # preencha SECRET_KEY e API_KEY
uv sync
uv run python manage.py migrate
uv run python manage.py test
uv run python manage.py runserver 0.0.0.0:8000
```

## Sem uv (ex.: Termux)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## Endpoints

```text
GET    /api/health/
POST   /api/time-records/
GET    /api/time-records/today/
GET    /api/time-records/month/?year=2026&month=5
GET    /api/time-records/<date>/
PUT    /api/time-records/<date>/
DELETE /api/time-records/<date>/
```

Todos os endpoints (exceto `/api/health/`) exigem o header `X-Api-Key`.
Qualquer rota fora de `/api/` devolve o `index.html` do frontend
(ou 503 se o build ainda não existir).

## Arquitetura (camadas em classes)

```text
views.py        → recebe HTTP, valida e delega (APIView)
serializers.py  → valida e normaliza o input
services.py     → regras de negócio (TimeRecordService)
repositories.py → acesso ao SQLite via Django ORM (TimeRecordRepository)
models.py       → modelo TimeRecord (tabela SQLite)
```
