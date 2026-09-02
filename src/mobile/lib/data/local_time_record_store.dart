import '../domain/dates.dart';
import '../domain/status.dart';
import '../domain/time_record.dart';
import 'time_record_dao.dart';
import 'time_record_store.dart';

/// Mesmo `FIXED_USER_ID` do backend, para o documento gravado aqui ser igual ao
/// do servidor caso um dia exista sync.
const localUserId = String.fromEnvironment('USER_ID', defaultValue: 'usuario_001');

/// Regras de negócio rodando no aparelho, sem rede. Espelha
/// `TimeRecordService` (`src/backend/apps/time_records/services.py`).
class LocalTimeRecordStore implements TimeRecordStore {
  LocalTimeRecordStore({required this.dao, this.userId = localUserId});

  final TimeRecordDao dao;
  final String userId;

  @override
  Future<TimeRecord?> getToday() => getByDate(formatApiDate(DateTime.now()));

  @override
  Future<TimeRecord?> getByDate(String date) => dao.getByDate(userId, date);

  @override
  Future<List<TimeRecord>> listMonth(int year, int month) =>
      dao.listMonth(userId, year, month);

  @override
  Future<TimeRecord> save(TimeRecordInput input) async {
    final times = normalizeTimes(input.times.toMap());
    final existing = await dao.getByDate(userId, input.date);
    final now = nowTimestamp();

    return dao.upsert(
      userId,
      TimeRecord(
        date: input.date,
        dayType: input.dayType,
        times: TimeRecordTimes(times),
        notes: input.notes,
        status: calculateStatus(input.dayType, times),
        createdAt: existing?.createdAt ?? now,
        updatedAt: now,
      ),
    );
  }

  @override
  Future<void> delete(String date) => dao.delete(userId, date);
}
