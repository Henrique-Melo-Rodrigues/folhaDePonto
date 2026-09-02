// Formatação e parsing de datas. Fora do model de propósito: o registro não
// deve carregar regra de apresentação.

const _monthNames = <String>[
  'Janeiro',
  'Fevereiro',
  'Março',
  'Abril',
  'Maio',
  'Junho',
  'Julho',
  'Agosto',
  'Setembro',
  'Outubro',
  'Novembro',
  'Dezembro',
];

/// Data no formato da API/banco (`YYYY-MM-DD`).
String formatApiDate(DateTime date) {
  final year = date.year.toString().padLeft(4, '0');
  final month = date.month.toString().padLeft(2, '0');
  final day = date.day.toString().padLeft(2, '0');
  return '$year-$month-$day';
}

DateTime parseApiDate(String value) {
  final parts = value.split('-').map(int.parse).toList();
  return DateTime(parts[0], parts[1], parts[2]);
}

String formatDisplayDate(String value) {
  final date = parseApiDate(value);
  final day = date.day.toString().padLeft(2, '0');
  final month = date.month.toString().padLeft(2, '0');
  return '$day/$month/${date.year}';
}

String monthLabel(DateTime date) => '${_monthNames[date.month - 1]} ${date.year}';

/// Carimbo de tempo local com offset e precisão de segundos, espelhando
/// `timezone.now().replace(microsecond=0).isoformat()` do backend.
String nowTimestamp([DateTime? now]) {
  final moment = (now ?? DateTime.now()).toLocal();
  final truncated = DateTime(
    moment.year,
    moment.month,
    moment.day,
    moment.hour,
    moment.minute,
    moment.second,
  );
  final offset = truncated.timeZoneOffset;
  final sign = offset.isNegative ? '-' : '+';
  final hours = offset.inHours.abs().toString().padLeft(2, '0');
  final minutes = (offset.inMinutes.abs() % 60).toString().padLeft(2, '0');
  return '${truncated.toIso8601String()}$sign$hours:$minutes';
}
