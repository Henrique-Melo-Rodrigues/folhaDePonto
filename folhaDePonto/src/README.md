# Folha de Ponto Pessoal

MVP de folha de ponto pessoal com API Django/DRF, MongoDB via PyMongo e app Flutter Android.

## Backend

```bash
cd backend
uv sync
uv run python manage.py test
uv run python manage.py runserver 0.0.0.0:8000
```

Para usar os endpoints de ponto nesse modo, deixe um MongoDB local em `mongodb://localhost:27017`.

Com Docker instalado:

```bash
cd backend
docker compose up --build
```

Endpoints principais:

```text
GET    /api/health/
POST   /api/time-records/
GET    /api/time-records/today/
GET    /api/time-records/month/?year=2026&month=5
GET    /api/time-records/<date>/
PUT    /api/time-records/<date>/
DELETE /api/time-records/<date>/
```

## Mobile

Se a pasta `mobile/android/` ainda nao existir:

```bash
cd mobile
flutter create . --platforms=android --project-name folha_de_ponto
flutter pub get
```

Emulador Android:

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Celular fisico na mesma rede:

```bash
flutter run --dart-define=API_BASE_URL=http://SEU_IP_LOCAL:8000
```

Se o Android bloquear HTTP local, adicione `android:usesCleartextTraffic="true"` no `application` do `android/app/src/main/AndroidManifest.xml`.
