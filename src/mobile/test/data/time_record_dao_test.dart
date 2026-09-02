import 'package:flutter_test/flutter_test.dart';
import 'package:folha_de_ponto/data/time_record_dao.dart';
import 'package:folha_de_ponto/domain/time_record.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

const _userId = 'usuario_teste';

TimeRecord makeRecord({
  String date = '2026-05-27',
  String dayType = 'trabalho',
  Map<String, String?> times = const {
    'arrival': '07:45',
    'lunch_start': '12:00',
    'lunch_end': '13:00',
    'departure': '14:45',
  },
  String notes = '',
  String status = 'complete',
  String createdAt = '2026-05-27T10:00:00-03:00',
  String updatedAt = '2026-05-27T10:00:00-03:00',
}) {
  return TimeRecord(
    date: date,
    dayType: dayType,
    times: TimeRecordTimes(times),
    notes: notes,
    status: status,
    createdAt: createdAt,
    updatedAt: updatedAt,
  );
}

void main() {
  setUpAll(sqfliteFfiInit);

  late TimeRecordDao dao;

  setUp(() {
    dao = TimeRecordDao(factory: databaseFactoryFfi, path: inMemoryDatabasePath);
  });

  tearDown(() => dao.close());

  test('upsert e getByDate fazem roundtrip do documento', () async {
    await dao.upsert(_userId, makeRecord(notes: 'Dia normal'));

    final stored = await dao.getByDate(_userId, '2026-05-27');

    expect(stored, isNotNull);
    expect(stored!.dayType, 'trabalho');
    expect(stored.times['arrival'], '07:45');
    expect(stored.times['departure'], '14:45');
    expect(stored.notes, 'Dia normal');
    expect(stored.status, 'complete');
    expect(stored.createdAt, '2026-05-27T10:00:00-03:00');
  });

  test('getByDate devolve null quando não existe', () async {
    expect(await dao.getByDate(_userId, '2026-05-27'), isNull);
  });

  test('horários vazios voltam como null', () async {
    await dao.upsert(_userId, makeRecord(times: const {'arrival': '07:45'}));

    final stored = await dao.getByDate(_userId, '2026-05-27');

    expect(stored!.times['arrival'], '07:45');
    expect(stored.times['lunch_start'], isNull);
  });

  test('upsert na mesma data substitui em vez de duplicar', () async {
    await dao.upsert(_userId, makeRecord(notes: 'primeira'));
    await dao.upsert(_userId, makeRecord(notes: 'segunda'));

    final stored = await dao.listMonth(_userId, 2026, 5);

    expect(stored, hasLength(1));
    expect(stored.single.notes, 'segunda');
  });

  test('listMonth filtra pelo mês e ordena por data', () async {
    await dao.upsert(_userId, makeRecord(date: '2026-05-27'));
    await dao.upsert(_userId, makeRecord(date: '2026-05-03'));
    await dao.upsert(_userId, makeRecord(date: '2026-06-01'));

    final maio = await dao.listMonth(_userId, 2026, 5);

    expect(maio.map((record) => record.date), ['2026-05-03', '2026-05-27']);
  });

  test('listMonth isola por usuário', () async {
    await dao.upsert(_userId, makeRecord());
    await dao.upsert('outro_usuario', makeRecord());

    expect(await dao.listMonth(_userId, 2026, 5), hasLength(1));
  });

  test('delete remove e informa se havia registro', () async {
    await dao.upsert(_userId, makeRecord());

    expect(await dao.delete(_userId, '2026-05-27'), isTrue);
    expect(await dao.delete(_userId, '2026-05-27'), isFalse);
    expect(await dao.getByDate(_userId, '2026-05-27'), isNull);
  });
}
