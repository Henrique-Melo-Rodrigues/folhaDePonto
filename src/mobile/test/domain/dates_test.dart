import 'package:flutter_test/flutter_test.dart';
import 'package:folha_de_ponto/domain/dates.dart';

void main() {
  test('formatApiDate usa YYYY-MM-DD com zero à esquerda', () {
    expect(formatApiDate(DateTime(2026, 5, 7)), '2026-05-07');
  });

  test('parseApiDate volta para DateTime', () {
    expect(parseApiDate('2026-05-27'), DateTime(2026, 5, 27));
  });

  test('formatDisplayDate usa DD/MM/YYYY', () {
    expect(formatDisplayDate('2026-05-07'), '07/05/2026');
  });

  test('monthLabel nomeia o mês', () {
    expect(monthLabel(DateTime(2026, 3)), 'Março 2026');
  });

  test('nowTimestamp tem o formato ISO com offset e sem microssegundos', () {
    expect(
      nowTimestamp(DateTime(2026, 5, 27, 10, 30, 15, 999)),
      matches(r'^2026-05-27T10:30:15[+-]\d{2}:\d{2}$'),
    );
  });
}
