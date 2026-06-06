# Backend - Folha de Ponto

API Django/DRF para o MVP de folha de ponto pessoal.

## Desenvolvimento local com uv

```bash
cd backend
uv sync
uv run python manage.py test
uv run python manage.py runserver 0.0.0.0:8000
```

Para usar os endpoints de ponto nesse modo, deixe um MongoDB local em `mongodb://localhost:27017`.

## Docker Compose

```bash
cd backend
docker compose up --build
```

A API ficará em `http://localhost:8000`.

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
