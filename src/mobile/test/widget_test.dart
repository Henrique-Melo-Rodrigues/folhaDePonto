import 'package:flutter_test/flutter_test.dart';
import 'package:folha_de_ponto/data/time_record_store.dart';
import 'package:folha_de_ponto/domain/dates.dart';
import 'package:folha_de_ponto/domain/status.dart';
import 'package:folha_de_ponto/domain/time_record.dart';
import 'package:folha_de_ponto/main.dart';

// Smoke test do app montado na porta [TimeRecordStore]: sem SQLite, sem rede.
// Prova que o composition root e as duas abas continuam de pé.

/// Fake em memória — as mesmas regras do adapter local, sem persistência.
class FakeTimeRecordStore implements TimeRecordStore {
  FakeTimeRecordStore([Iterable<TimeRecord> initial = const []]) {
    for (final record in initial) {
      _records[record.date] = record;
    }
  }

  final Map<String, TimeRecord> _records = {};

  @override
  Future<TimeRecord?> getToday() => getByDate(formatApiDate(DateTime.now()));

  @override
  Future<TimeRecord?> getByDate(String date) async => _records[date];

  @override
  Future<List<TimeRecord>> listMonth(int year, int month) async {
    final prefix = '${year.toString().padLeft(4, '0')}-'
        '${month.toString().padLeft(2, '0')}-';
    final records = _records.values.where((r) => r.date.startsWith(prefix)).toList()
      ..sort((a, b) => a.date.compareTo(b.date));
    return records;
  }

  @override
  Future<TimeRecord> save(TimeRecordInput input) async {
    final times = normalizeTimes(input.times.toMap());
    final now = nowTimestamp();
    return _records[input.date] = TimeRecord(
      date: input.date,
      dayType: input.dayType,
      times: TimeRecordTimes(times),
      notes: input.notes,
      status: calculateStatus(input.dayType, times),
      createdAt: _records[input.date]?.createdAt ?? now,
      updatedAt: now,
    );
  }

  @override
  Future<void> delete(String date) async {
    _records.remove(date);
  }
}

TimeRecord makeRecord(String date) {
  return TimeRecord(
    date: date,
    dayType: 'trabalho',
    times: TimeRecordTimes.empty(),
    notes: '',
    status: 'complete',
    createdAt: '',
    updatedAt: '',
  );
}

void main() {
  testWidgets('sem registros, as duas abas mostram o estado vazio', (tester) async {
    await tester.pumpWidget(FolhaDePontoApp(store: FakeTimeRecordStore()));
    await tester.pumpAndSettle();

    expect(find.text('Hoje ainda nao foi preenchido'), findsOneWidget);

    await tester.tap(find.text('Mes'));
    await tester.pumpAndSettle();

    expect(find.text('Nenhum registro neste mes'), findsOneWidget);
  });

  testWidgets('o registro de hoje aparece nas duas abas', (tester) async {
    final today = formatApiDate(DateTime.now());
    await tester.pumpWidget(
      FolhaDePontoApp(store: FakeTimeRecordStore([makeRecord(today)])),
    );
    await tester.pumpAndSettle();

    expect(find.text('Hoje ainda nao foi preenchido'), findsNothing);
    expect(find.text(formatDisplayDate(today)), findsOneWidget);

    await tester.tap(find.text('Mes'));
    await tester.pumpAndSettle();

    expect(find.text('Nenhum registro neste mes'), findsNothing);
    expect(find.text(formatDisplayDate(today)), findsOneWidget);
  });
}
