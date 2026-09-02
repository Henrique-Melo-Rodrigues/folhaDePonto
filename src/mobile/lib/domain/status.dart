import 'domain.g.dart';

// Regras de negócio do registro de ponto, portadas de
// `src/backend/apps/time_records/services.py` e `serializers.py`.
//
// Os vetores de `contracts/status_cases.json` provam que esta implementação e
// a do backend concordam — veja `test/domain/status_test.dart`.

/// Espelha `TimeRecordService.calculate_status`.
String calculateStatus(String dayType, Map<String, String?> times) {
  final values = timeFields.map((field) => times[field]).toList();
  final hasAnyTime = values.any(_isFilled);
  final hasAllTimes = values.every(_isFilled);

  if (notWorkedDayTypes.contains(dayType) && !hasAnyTime) {
    return statusNotWorked;
  }

  if (hasAllTimes) {
    return statusComplete;
  }

  return statusIncomplete;
}

/// Espelha `TimeRecordService._normalize_times`: branco vira null e o mapa
/// sempre tem exatamente os campos do contrato.
Map<String, String?> normalizeTimes(Map<String, String?>? times) {
  final source = times ?? const <String, String?>{};
  return {
    for (final field in timeFields) field: _blankToNull(source[field]),
  };
}

/// Espelha `TimesSerializer._normalize_time`. Devolve a mensagem de erro ou
/// null quando o valor é aceitável (vazio inclusive).
String? validateTime(String? value) {
  final text = value?.trim() ?? '';
  if (text.isEmpty) {
    return null;
  }

  if (!RegExp(timePattern).hasMatch(text)) {
    return 'Use horários no formato HH:MM.';
  }

  final hour = int.parse(text.substring(0, 2));
  final minute = int.parse(text.substring(3, 5));
  if (hour > 23 || minute > 59) {
    return 'Use horários válidos entre 00:00 e 23:59.';
  }

  return null;
}

bool _isFilled(String? value) => value != null && value.isNotEmpty;

String? _blankToNull(String? value) {
  final text = value?.trim() ?? '';
  return text.isEmpty ? null : text;
}
