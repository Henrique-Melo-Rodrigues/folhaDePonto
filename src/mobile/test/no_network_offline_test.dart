import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:folha_de_ponto/data/local_time_record_store.dart';
import 'package:folha_de_ponto/main.dart';

// Guarda do escopo offline: o app roda inteiro no aparelho. A rede é uma
// exceção deliberada e isolada num único arquivo — se ela vazar para qualquer
// outro lugar de `lib/`, este teste quebra antes do APK ser publicado.
//
// Veja docs/decisions/ADR-001-mobile-local-first.md.

const _networkTokens = <String>[
  'package:http',
  'HttpClient',
  'Socket',
  'dart:io',
];

/// O único adapter autorizado a falar rede, e só quando o build define
/// `API_BASE_URL` (veja [buildStore]).
const _remoteAdapter = 'lib/data/remote_time_record_store.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('nenhum arquivo de lib/ fala rede, exceto o adapter remoto', () {
    final lib = Directory('lib');
    expect(
      lib.existsSync(),
      isTrue,
      reason: 'rode o teste a partir de src/mobile (o `flutter test` faz isso).',
    );

    final offenders = <String>[];

    for (final entity in lib.listSync(recursive: true)) {
      if (entity is! File || !entity.path.endsWith('.dart')) {
        continue;
      }

      final path = entity.path.replaceAll(r'\', '/');
      if (path == _remoteAdapter) {
        continue;
      }

      final source = entity.readAsStringSync();
      for (final token in _networkTokens) {
        if (source.contains(token)) {
          offenders.add('$path usa "$token"');
        }
      }
    }

    expect(
      offenders,
      isEmpty,
      reason: 'rede só é permitida em $_remoteAdapter; mova o código para lá '
          'ou remova a dependência.',
    );
  });

  test('buildStore devolve o adapter offline sem --dart-define=API_BASE_URL', () {
    expect(buildStore(), isA<LocalTimeRecordStore>());
  });
}
