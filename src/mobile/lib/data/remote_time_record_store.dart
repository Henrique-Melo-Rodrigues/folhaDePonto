import 'dart:convert';

import 'package:http/http.dart' as http;

import '../domain/time_record.dart';
import 'time_record_store.dart';

/// Adapter opt-in para a API Django (`src/backend`). Não é montado por default:
/// veja `main.dart`. Aqui as regras de negócio rodam no servidor — este arquivo
/// só transporta documentos.
class RemoteTimeRecordStore implements TimeRecordStore {
  RemoteTimeRecordStore({String? baseUrl, String? apiKey, http.Client? client})
      : baseUrl = _normalizeBaseUrl(baseUrl ?? defaultBaseUrl),
        apiKey = apiKey ?? defaultApiKey,
        _client = client ?? http.Client();

  static const defaultBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  static const defaultApiKey = String.fromEnvironment(
    'API_KEY',
    defaultValue: '',
  );

  final String baseUrl;
  final String apiKey;
  final http.Client _client;

  @override
  Future<TimeRecord?> getToday() => _getRecord('/time-records/today/');

  @override
  Future<TimeRecord?> getByDate(String date) => _getRecord('/time-records/$date/');

  @override
  Future<List<TimeRecord>> listMonth(int year, int month) async {
    final response = await _client.get(
      _uri('/time-records/month/', {
        'year': year.toString(),
        'month': month.toString(),
      }),
      headers: _headers(),
    );
    _ensureSuccess(response);

    final results = _decodeObject(response)['results'] as List<dynamic>? ?? [];
    return results
        .cast<Map<String, dynamic>>()
        .map(TimeRecord.fromJson)
        .toList();
  }

  @override
  Future<TimeRecord> save(TimeRecordInput input) async {
    final response = await _client.put(
      _uri('/time-records/${input.date}/'),
      headers: _headers({'Content-Type': 'application/json'}),
      body: jsonEncode(input.toJson()),
    );
    _ensureSuccess(response);
    return TimeRecord.fromJson(_decodeObject(response));
  }

  @override
  Future<void> delete(String date) async {
    final response = await _client.delete(
      _uri('/time-records/$date/'),
      headers: _headers(),
    );
    _ensureSuccess(response);
  }

  Future<TimeRecord?> _getRecord(String path) async {
    final response = await _client.get(_uri(path), headers: _headers());
    if (response.statusCode == 404) {
      return null;
    }
    _ensureSuccess(response);
    return TimeRecord.fromJson(_decodeObject(response));
  }

  Map<String, String> _headers([Map<String, String>? extra]) {
    return {
      if (apiKey.isNotEmpty) 'X-Api-Key': apiKey,
      ...?extra,
    };
  }

  Uri _uri(String path, [Map<String, String>? queryParameters]) {
    return Uri.parse('$baseUrl/api$path').replace(queryParameters: queryParameters);
  }

  static String _normalizeBaseUrl(String value) {
    return value.endsWith('/') ? value.substring(0, value.length - 1) : value;
  }

  Map<String, dynamic> _decodeObject(http.Response response) {
    return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
  }

  void _ensureSuccess(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return;
    }

    throw TimeRecordStoreException(
      'Erro ${response.statusCode}: ${utf8.decode(response.bodyBytes)}',
    );
  }
}

class TimeRecordStoreException implements Exception {
  const TimeRecordStoreException(this.message);

  final String message;

  @override
  String toString() => message;
}
