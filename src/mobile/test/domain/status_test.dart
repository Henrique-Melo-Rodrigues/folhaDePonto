import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:folha_de_ponto/domain/status.dart';

/// Caminho a partir da raiz do pacote (`src/mobile`), que é o cwd do
/// `flutter test`.
const _statusCasesFile = '../../contracts/status_cases.json';

void main() {
  group('calculateStatus (vetores golden do contrato)', () {
    final contract =
        jsonDecode(File(_statusCasesFile).readAsStringSync()) as Map<String, dynamic>;
    final cases = (contract['cases'] as List<dynamic>).cast<Map<String, dynamic>>();

    test('o contrato traz vetores', () {
      expect(cases, isNotEmpty);
    });

    for (final testCase in cases) {
      test(testCase['name'] as String, () {
        final times = (testCase['times'] as Map<String, dynamic>)
            .map((key, value) => MapEntry(key, value as String?));

        expect(
          calculateStatus(testCase['day_type'] as String, times),
          testCase['expected'],
          reason: 'o backend calcula isto em services.py:calculate_status',
        );
      });
    }
  });

  group('normalizeTimes', () {
    test('preenche todos os campos do contrato', () {
      final times = normalizeTimes({'arrival': '07:45'});

      expect(times.keys, containsAll(['arrival', 'lunch_start', 'lunch_end', 'departure']));
      expect(times['arrival'], '07:45');
      expect(times['departure'], isNull);
    });

    test('branco e espaços viram null', () {
      final times = normalizeTimes({'arrival': '', 'lunch_start': '   '});

      expect(times['arrival'], isNull);
      expect(times['lunch_start'], isNull);
    });

    test('aceita mapa nulo', () {
      expect(normalizeTimes(null).values.every((value) => value == null), isTrue);
    });
  });

  group('validateTime', () {
    test('aceita vazio e horário válido', () {
      expect(validateTime(''), isNull);
      expect(validateTime(null), isNull);
      expect(validateTime('07:45'), isNull);
      expect(validateTime('23:59'), isNull);
    });

    test('rejeita formato fora de HH:MM', () {
      expect(validateTime('7:45'), isNotNull);
      expect(validateTime('0745'), isNotNull);
    });

    test('rejeita horário fora da faixa', () {
      expect(validateTime('25:00'), isNotNull);
      expect(validateTime('12:60'), isNotNull);
    });
  });
}
