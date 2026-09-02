import '../domain/time_record.dart';

/// A porta entre a UI e a persistência: as telas só enxergam esta interface.
///
/// Implementações:
/// - [LocalTimeRecordStore] — SQLite no aparelho, sem rede (default).
/// - [RemoteTimeRecordStore] — API Django, opt-in via `--dart-define`.
abstract class TimeRecordStore {
  Future<TimeRecord?> getToday();

  Future<TimeRecord?> getByDate(String date);

  Future<List<TimeRecord>> listMonth(int year, int month);

  /// Upsert por data, igual ao `PUT /api/time-records/<date>/` do backend.
  Future<TimeRecord> save(TimeRecordInput input);

  Future<void> delete(String date);
}
