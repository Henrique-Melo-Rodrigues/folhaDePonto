# Mobile - Folha de Ponto

App Flutter Android para registrar a folha de ponto pessoal.

Este workspace tem o codigo do app em `lib/`. Se a pasta `android/` ainda nao existir, gere o wrapper Android com Flutter:

```bash
cd mobile
flutter create . --platforms=android --project-name folha_de_ponto
flutter pub get
```

Rodando no emulador Android com a API local:

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Rodando em celular fisico na mesma rede do PC:

```bash
flutter run --dart-define=API_BASE_URL=http://192.168.0.10:8000
```

Troque `192.168.0.10` pelo IP local da maquina que esta rodando a API.

Se o Android bloquear HTTP local, adicione `android:usesCleartextTraffic="true"` no `application` do `android/app/src/main/AndroidManifest.xml` depois de gerar o wrapper Android.
