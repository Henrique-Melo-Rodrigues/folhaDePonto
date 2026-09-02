import 'domain.g.dart';
import 'status.dart';

/// Horários de um dia. O mapa tem sempre exatamente os campos de `timeFields`
/// (contrato), com branco normalizado para null.
class TimeRecordTimes {
  TimeRecordTimes(Map<String, String?> values) : _values = normalizeTimes(values);

  TimeRecordTimes.empty() : _values = normalizeTimes(null);

  factory TimeRecordTimes.fromJson(Map<String, dynamic>? json) {
    return TimeRecordTimes({
      for (final field in timeFields) field: json?[field] as String?,
    });
  }

  final Map<String, String?> _values;

  String? operator [](String field) => _values[field];

  Map<String, String?> toMap() => Map<String, String?>.unmodifiable(_values);

  Map<String, dynamic> toJson() => <String, dynamic>{..._values};
}

/// O que a UI envia para salvar um dia. Mesma forma do `TimeRecordInput` do
/// backend (`serializers.py`) e do web — o `status` é derivado, nunca enviado.
class TimeRecordInput {
  const TimeRecordInput({
    required this.date,
    required this.dayType,
    required this.times,
    this.notes = '',
  });

  final String date;
  final String dayType;
  final TimeRecordTimes times;
  final String notes;

  Map<String, dynamic> toJson() {
    return {
      'date': date,
      'day_type': dayType,
      'times': times.toJson(),
      'notes': notes,
    };
  }
}

/// O documento completo de um dia, igual ao que o backend devolve.
class TimeRecord {
  const TimeRecord({
    required this.date,
    required this.dayType,
    required this.times,
    required this.notes,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
  });

  factory TimeRecord.fromJson(Map<String, dynamic> json) {
    return TimeRecord(
      date: json['date'] as String,
      dayType: json['day_type'] as String,
      times: TimeRecordTimes.fromJson(json['times'] as Map<String, dynamic>?),
      notes: (json['notes'] as String?) ?? '',
      status: (json['status'] as String?) ?? statusIncomplete,
      createdAt: (json['created_at'] as String?) ?? '',
      updatedAt: (json['updated_at'] as String?) ?? '',
    );
  }

  final String date;
  final String dayType;
  final TimeRecordTimes times;
  final String notes;
  final String status;
  final String createdAt;
  final String updatedAt;

  TimeRecordInput toInput() {
    return TimeRecordInput(
      date: date,
      dayType: dayType,
      times: times,
      notes: notes,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'date': date,
      'day_type': dayType,
      'times': times.toJson(),
      'notes': notes,
      'status': status,
      'created_at': createdAt,
      'updated_at': updatedAt,
    };
  }
}
