const dayTypes = <String>[
  'trabalho',
  'atividade_teorica',
  'folga',
  'compensacao',
  'feriado',
  'falta',
  'outro',
];

const dayTypeLabels = <String, String>{
  'trabalho': 'Trabalho',
  'atividade_teorica': 'Atividade teorica',
  'folga': 'Folga',
  'compensacao': 'Compensacao',
  'feriado': 'Feriado',
  'falta': 'Falta',
  'outro': 'Outro',
};

const statusLabels = <String, String>{
  'complete': 'Completo',
  'incomplete': 'Incompleto',
  'not_worked': 'Sem trabalho',
};

class TimeRecordTimes {
  const TimeRecordTimes({
    this.arrival,
    this.lunchStart,
    this.lunchEnd,
    this.departure,
  });

  factory TimeRecordTimes.empty() => const TimeRecordTimes();

  factory TimeRecordTimes.fromJson(Map<String, dynamic>? json) {
    return TimeRecordTimes(
      arrival: json?['arrival'] as String?,
      lunchStart: json?['lunch_start'] as String?,
      lunchEnd: json?['lunch_end'] as String?,
      departure: json?['departure'] as String?,
    );
  }

  final String? arrival;
  final String? lunchStart;
  final String? lunchEnd;
  final String? departure;

  Map<String, dynamic> toJson() {
    return {
      'arrival': _blankToNull(arrival),
      'lunch_start': _blankToNull(lunchStart),
      'lunch_end': _blankToNull(lunchEnd),
      'departure': _blankToNull(departure),
    };
  }

  static String? _blankToNull(String? value) {
    if (value == null || value.trim().isEmpty) {
      return null;
    }
    return value.trim();
  }
}

class TimeRecord {
  const TimeRecord({
    required this.date,
    required this.dayType,
    required this.times,
    required this.notes,
    required this.status,
    this.createdAt,
    this.updatedAt,
  });

  factory TimeRecord.emptyForDate(DateTime date) {
    return TimeRecord(
      date: formatApiDate(date),
      dayType: 'trabalho',
      times: TimeRecordTimes.empty(),
      notes: '',
      status: 'incomplete',
    );
  }

  factory TimeRecord.fromJson(Map<String, dynamic> json) {
    return TimeRecord(
      date: json['date'] as String,
      dayType: json['day_type'] as String,
      times: TimeRecordTimes.fromJson(json['times'] as Map<String, dynamic>?),
      notes: (json['notes'] as String?) ?? '',
      status: (json['status'] as String?) ?? 'incomplete',
      createdAt: json['created_at'] as String?,
      updatedAt: json['updated_at'] as String?,
    );
  }

  final String date;
  final String dayType;
  final TimeRecordTimes times;
  final String notes;
  final String status;
  final String? createdAt;
  final String? updatedAt;

  Map<String, dynamic> toSaveJson() {
    return {
      'date': date,
      'day_type': dayType,
      'times': times.toJson(),
      'notes': notes,
    };
  }
}

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

String monthLabel(DateTime date) {
  const months = [
    'Janeiro',
    'Fevereiro',
    'Marco',
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
  return '${months[date.month - 1]} ${date.year}';
}

