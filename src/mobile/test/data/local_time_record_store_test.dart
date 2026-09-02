import 'package:flutter_test/flutter_test.dart';
import 'package:folha_de_ponto/data/local_time_record_store.dart';
import 'package:folha_de_ponto/data/time_record_dao.dart';
import 'package:folha_de_ponto/domain/dates.dart';
import 'package:folha_de_ponto/domain/time_record.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

// Espelha src/backend/apps/time_records/tests/test_services.py: as mesmas
// regras, agora rodando no aparelho.

TimeRecordInput makeInput({
  String date = '2026-05-27',
  String dayType = 'trabalho',
  Map<String, String?> times = const {},
  String notes = '',
}) {
  return TimeRecordInput(
    date: date,
    dayType: dayType,
    times: TimeRecordTimes(times),
    notes: notes,
  );
}

void main() {
  setUpAll(sqfliteFfiInit);

  late TimeRecordDao dao;
  late LocalTimeRecordStore store;

  setUp(() {
    dao = TimeRecordDao(factory: databaseFactoryFfi, path: inMemoryDatabasePath);
    store = LocalTimeRecordStore(dao: dao, userId: 'usuario_teste');
  });

  tearDown(() => dao.close());

  test('dia de trabalho completo vira complete', () async {
    final record = await store.save(
      makeInput(
        times: const {
          'arrival': '07:45',
          'lunch_start': '12:00',
          'lunch_end': '13:00',
          'departure': '14:45',
        },
        notes: 'Dia normal',
      ),
    );

    expect(record.status, 'complete');
  });

  test('dia não trabalhado sem horários vira not_worked', () async {
    final record = await store.save(makeInput(dayType: 'atividade_teorica'));

    expect(record.status, 'not_worked');
  });

  test('dia de trabalho parcial vira incomplete', () async {
    final record = await store.save(makeInput(times: const {'arrival': '07:45'}));

    expect(record.status, 'incomplete');
  });

  test('horário em branco é normalizado para null', () async {
    final record = await store.save(makeInput(times: const {'arrival': '  '}));

    expect(record.times['arrival'], isNull);
    expect(record.status, 'incomplete');
  });

  test('created_at é preservado ao atualizar', () async {
    final first = await store.save(makeInput());
    final second = await store.save(makeInput(dayType: 'folga'));

    expect(second.createdAt, first.createdAt);
    expect(second.status, 'not_worked');
  });

  test('getToday devolve o registro de hoje e null quando não há', () async {
    expect(await store.getToday(), isNull);

    await store.save(makeInput(date: formatApiDate(DateTime.now())));

    expect(await store.getToday(), isNotNull);
  });

  test('listMonth devolve o que foi salvo no mês', () async {
    await store.save(makeInput(date: '2026-05-03'));
    await store.save(makeInput(date: '2026-06-03'));

    expect(await store.listMonth(2026, 5), hasLength(1));
  });

  test('delete remove o registro', () async {
    await store.save(makeInput());
    await store.delete('2026-05-27');

    expect(await store.getByDate('2026-05-27'), isNull);
  });
}
