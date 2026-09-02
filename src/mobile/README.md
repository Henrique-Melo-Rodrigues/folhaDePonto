# Mobile - Folha de Ponto

App Flutter Android para registrar a folha de ponto pessoal. **Roda offline, no
aparelho** — sem servidor, sem rede, sem chave de API.

O porquê dessa escolha está em
[docs/decisions/ADR-001-mobile-local-first.md](../../docs/decisions/ADR-001-mobile-local-first.md).

## Como está organizado

```
lib/domain/   regras e vocabulário do dia (status, normalização, datas)
              domain.g.dart é GERADO — veja contracts/
lib/data/     TimeRecordStore (a porta) + dois adapters:
              LocalTimeRecordStore (SQLite, default) e
              RemoteTimeRecordStore (HTTP, opt-in)
lib/screens/  as telas, que só conhecem a porta
lib/main.dart composition root: escolhe o adapter
```

As telas nunca falam com SQLite nem com HTTP diretamente — só com
`TimeRecordStore`. Trocar de adapter é trocar uma linha em `main.dart`.

## Build padrão (offline)

```bash
cd src/mobile
flutter pub get
flutter run             # ou: flutter build apk --debug
```

Sem nenhum `--dart-define`, `buildStore()` monta o `LocalTimeRecordStore`: o app
guarda tudo num SQLite embarcado e calcula o status do dia sozinho, com as
mesmas regras do backend. É esse o APK que o CI publica.

## Build opcional contra a API Django

O adapter remoto só entra quando `API_BASE_URL` é definido **em tempo de build**:

```bash
# emulador Android falando com a API na máquina host
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000 \
            --dart-define=API_KEY=<chave do .env do backend>

# celular físico na mesma rede do PC
flutter run --dart-define=API_BASE_URL=http://192.168.0.10:8000 \
            --dart-define=API_KEY=<chave do .env do backend>
```

Troque `192.168.0.10` pelo IP local da máquina que roda a API. Nesse modo as
regras rodam no servidor e o app é só transporte — nada é gravado no aparelho.

Se o Android bloquear HTTP em texto claro, adicione
`android:usesCleartextTraffic="true"` no `application` do
`android/app/src/main/AndroidManifest.xml`.

## Onde ficam os dados no aparelho

No modo offline, num arquivo SQLite chamado `folha_de_ponto.db`, dentro do
diretório de bancos do próprio app (`getDatabasesPath()` — em Android,
`/data/data/com.example.folha_de_ponto/databases/`). É uma área privada do app:
desinstalar apaga tudo, e **não há backup nem exportação ainda** (é o próximo
passo do projeto).

## Testes

```bash
flutter test
```

Cobrem as regras do domínio (com os vetores golden de
`contracts/status_cases.json`), o DAO do SQLite via `sqflite_common_ffi`, o
adapter local, um smoke test das telas e o
`test/no_network_offline_test.dart`, que reprova qualquer menção a rede fora do
adapter remoto.

> Flutter não está instalado na máquina de desenvolvimento principal deste
> projeto: a verificação do mobile acontece no GitHub Actions
> (`.github/workflows/mobile.yml`).
