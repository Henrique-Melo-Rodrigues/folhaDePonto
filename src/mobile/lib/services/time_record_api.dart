import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/time_record.dart';

class TimeRecordApi {
  TimeRecordApi({String? baseUrl, String? apiKey, http.Client? client})
      : baseUrl = _normalizeBaseUrl(baseUrl ?? _defaultBaseUrl),
        apiKey = apiKey ?? _defaultApiKey,
        _client = client ?? http.Client();

  static const _defaultBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  static const _defaultApiKey = String.fromEnvironment(
    'API_KEY',
    defaultValue: '',
  );

  final String baseUrl;
  final String apiKey;
  final http.Client _client;

  Map<String, String> _headers([Map<String, String>? extra]) {
    return {
      if (apiKey.isNotEmpty) 'X-Api-Key': apiKey,
      ...?extra,
    };
  }

  Future<TimeRecord?> getToday() async {
    final response =
        await _client.get(_uri('/time-records/today/'), headers: _headers());
    if (response.statusCode == 404) {
      return null;
    }
    _ensureSuccess(response);
    return TimeRecord.fromJson(_decodeObject(response));
  }

  Future<TimeRecord?> getByDate(String date) async {
    final response =
        await _client.get(_uri('/time-records/$date/'), headers: _headers());
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
      headers: _headers(),
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
      headers: _headers({'Content-Type': 'application/json'}),
      body: jsonEncode(record.toSaveJson()),
    );
    _ensureSuccess(response);
    return TimeRecord.fromJson(_decodeObject(response));
  }

  Future<TimeRecord> update(TimeRecord record) async {
    final response = await _client.put(
      _uri('/time-records/${record.date}/'),
      headers: _headers({'Content-Type': 'application/json'}),
      body: jsonEncode(record.toSaveJson()),
    );
    _ensureSuccess(response);
    return TimeRecord.fromJson(_decodeObject(response));
  }

  Future<void> delete(String date) async {
    final response =
        await _client.delete(_uri('/time-records/$date/'), headers: _headers());
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

