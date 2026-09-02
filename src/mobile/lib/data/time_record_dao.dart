import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../domain/domain.g.dart';
import '../domain/time_record.dart';

const _table = 'time_records';
const _databaseFile = 'folha_de_ponto.db';

/// Acesso ao SQLite embarcado no aparelho. Espelha
/// `src/backend/apps/time_records/repositories.py`.
///
/// O schema é escrito à mão de propósito: mudança de schema é migração
/// deliberada, não efeito colateral do contrato. Já a leitura/escrita das
/// colunas de horário segue `timeFields`.
class TimeRecordDao {
  TimeRecordDao({DatabaseFactory? factory, String? path})
      : _factory = factory,
        _path = path;

  final DatabaseFactory? _factory;
  final String? _path;
  Database? _database;

  /// Resolvido só na primeira query: construir o DAO não toca a plataforma,
  /// o que deixa `buildStore()` testável fora do aparelho.
  DatabaseFactory get _databaseFactory => _factory ?? databaseFactory;

  Future<Database> _open() async {
    final database = _database;
    if (database != null) {
      return database;
    }

    final factory = _databaseFactory;
    final path = _path ?? p.join(await factory.getDatabasesPath(), _databaseFile);
    return _database = await factory.openDatabase(
      path,
      options: OpenDatabaseOptions(version: 1, onCreate: _createSchema),
    );
  }

  Future<void> _createSchema(Database database, int version) async {
    await database.execute('''
      CREATE TABLE $_table (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        date TEXT NOT NULL,
        day_type TEXT NOT NULL,
        arrival TEXT,
        lunch_start TEXT,
        lunch_end TEXT,
        departure TEXT,
        notes TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    ''');
    await database.execute(
      'CREATE UNIQUE INDEX unique_user_date ON $_table (user_id, date)',
    );
  }

  Future<TimeRecord?> getByDate(String userId, String date) async {
    final database = await _open();
    final rows = await database.query(
      _table,
      where: 'user_id = ? AND date = ?',
      whereArgs: [userId, date],
      limit: 1,
    );
    return rows.isEmpty ? null : _fromRow(rows.first);
  }

  Future<List<TimeRecord>> listMonth(String userId, int year, int month) async {
    final database = await _open();
    final prefix = '${year.toString().padLeft(4, '0')}-${month.toString().padLeft(2, '0')}-';
    final rows = await database.query(
      _table,
      where: 'user_id = ? AND date LIKE ?',
      whereArgs: [userId, '$prefix%'],
      orderBy: 'date',
    );
    return rows.map(_fromRow).toList();
  }

  Future<TimeRecord> upsert(String userId, TimeRecord record) async {
    final database = await _open();
    await database.insert(
      _table,
      _toRow(userId, record),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
    return record;
  }

  Future<bool> delete(String userId, String date) async {
    final database = await _open();
    final deleted = await database.delete(
      _table,
      where: 'user_id = ? AND date = ?',
      whereArgs: [userId, date],
    );
    return deleted == 1;
  }

  Future<void> close() async {
    await _database?.close();
    _database = null;
  }

  Map<String, Object?> _toRow(String userId, TimeRecord record) {
    return {
      'user_id': userId,
      'date': record.date,
      'day_type': record.dayType,
      for (final field in timeFields) field: record.times[field],
      'notes': record.notes,
      'status': record.status,
      'created_at': record.createdAt,
      'updated_at': record.updatedAt,
    };
  }

  TimeRecord _fromRow(Map<String, Object?> row) {
    return TimeRecord(
      date: row['date'] as String,
      dayType: row['day_type'] as String,
      times: TimeRecordTimes({
        for (final field in timeFields) field: row[field] as String?,
      }),
      notes: (row['notes'] as String?) ?? '',
      status: row['status'] as String,
      createdAt: (row['created_at'] as String?) ?? '',
      updatedAt: (row['updated_at'] as String?) ?? '',
    );
  }
}
