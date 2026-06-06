import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/time_record.dart';

class TimeRecordApi {
  TimeRecordApi({String? baseUrl, http.Client? client})
      : baseUrl = _normalizeBaseUrl(baseUrl ?? _defaultBaseUrl),
        _client = client ?? http.Client();

  static const _defaultBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  final String baseUrl;
  final http.Client _client;

  Future<TimeRecord?> getToday() async {
    final response = await _client.get(_uri('/time-records/today/'));
    if (response.statusCode == 404) {
      return null;
    }
    _ensureSuccess(response);
    return TimeRecord.fromJson(_decodeObject(response));
  }

  Future<TimeRecord?> getByDate(String date) async {
    final response = await _client.get(_uri('/time-records/$date/'));
    if (response.statusCode == 404) {
      return null;
    }
    _ensureSuccess(response);
    return TimeRecord.fromJson(_decodeObject(response));
  }

  Future<List<TimeRecord>> getMonth(int year, int month) async {
    final response = await _client.get(
      _uri(
        '/time-records/month/',
        {
          'year': year.toString(),
          'month': month.toString(),
        },
      ),
    );
    _ensureSuccess(response);

    final data = _decodeObject(response);
    final results = (data['results'] as List<dynamic>? ?? [])
        .cast<Map<String, dynamic>>()
        .map(TimeRecord.fromJson)
        .toList();
    return results;
  }

  Future<TimeRecord> create(TimeRecord record) async {
    final response = await _client.post(
      _uri('/time-records/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(record.toSaveJson()),
    );
    _ensureSuccess(response);
    return TimeRecord.fromJson(_decodeObject(response));
  }

  Future<TimeRecord> update(TimeRecord record) async {
    final response = await _client.put(
      _uri('/time-records/${record.date}/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(record.toSaveJson()),
    );
    _ensureSuccess(response);
    return TimeRecord.fromJson(_decodeObject(response));
  }

  Future<void> delete(String date) async {
    final response = await _client.delete(_uri('/time-records/$date/'));
    _ensureSuccess(response);
  }

  Uri _uri(String path, [Map<String, String>? queryParameters]) {
    return Uri.parse('$baseUrl/api$path').replace(queryParameters: queryParameters);
  }

  static String _normalizeBaseUrl(String value) {
    return value.endsWith('/') ? value.substring(0, value.length - 1) : value;
  }

  Map<String, dynamic> _decodeObject(http.Response response) {
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    return decoded as Map<String, dynamic>;
  }

  void _ensureSuccess(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return;
    }

    throw TimeRecordApiException(
      'Erro ${response.statusCode}: ${utf8.decode(response.bodyBytes)}',
    );
  }
}

class TimeRecordApiException implements Exception {
  const TimeRecordApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

