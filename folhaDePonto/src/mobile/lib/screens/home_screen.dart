import 'package:flutter/material.dart';

import '../models/time_record.dart';
import '../services/time_record_api.dart';
import 'time_record_form_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.api});

  final TimeRecordApi api;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late Future<TimeRecord?> _todayFuture;
  late Future<List<TimeRecord>> _monthFuture;
  DateTime _visibleMonth = DateTime(DateTime.now().year, DateTime.now().month);

  @override
  void initState() {
    super.initState();
    _reload();
  }

  void _reload() {
    _todayFuture = widget.api.getToday();
    _monthFuture = widget.api.getMonth(_visibleMonth.year, _visibleMonth.month);
  }

  void _setMonth(DateTime month) {
    setState(() {
      _visibleMonth = DateTime(month.year, month.month);
      _monthFuture = widget.api.getMonth(_visibleMonth.year, _visibleMonth.month);
    });
  }

  Future<void> _openForm({TimeRecord? record, DateTime? date}) async {
    final changed = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => TimeRecordFormScreen(
          api: widget.api,
          initialRecord: record,
          selectedDate: date ?? DateTime.now(),
        ),
      ),
    );

    if (changed == true && mounted) {
      setState(_reload);
    }
  }

  Future<void> _pickDateAndCreate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      firstDate: DateTime(now.year - 2),
      lastDate: DateTime(now.year + 2),
      initialDate: now,
    );

    if (picked != null) {
      await _openForm(date: picked);
    }
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Folha de ponto'),
          bottom: const TabBar(
            tabs: [
              Tab(icon: Icon(Icons.today), text: 'Hoje'),
              Tab(icon: Icon(Icons.calendar_month), text: 'Mes'),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            _TodayTab(
              future: _todayFuture,
              onCreate: () => _openForm(date: DateTime.now()),
              onEdit: (record) => _openForm(record: record),
              onRetry: () => setState(_reload),
            ),
            _MonthTab(
              future: _monthFuture,
              visibleMonth: _visibleMonth,
              onPreviousMonth: () => _setMonth(
                DateTime(_visibleMonth.year, _visibleMonth.month - 1),
              ),
              onNextMonth: () => _setMonth(
                DateTime(_visibleMonth.year, _visibleMonth.month + 1),
              ),
              onCreate: _pickDateAndCreate,
              onEdit: (record) => _openForm(record: record),
              onRetry: () => setState(_reload),
            ),
          ],
        ),
      ),
    );
  }
}

class _TodayTab extends StatelessWidget {
  const _TodayTab({
    required this.future,
    required this.onCreate,
    required this.onEdit,
    required this.onRetry,
  });

  final Future<TimeRecord?> future;
  final VoidCallback onCreate;
  final ValueChanged<TimeRecord> onEdit;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<TimeRecord?>(
      future: future,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }

        if (snapshot.hasError) {
          return _ErrorState(message: snapshot.error.toString(), onRetry: onRetry);
        }

        final record = snapshot.data;
        if (record == null) {
          return _EmptyState(
            title: 'Hoje ainda nao foi preenchido',
            actionLabel: 'Preencher hoje',
            icon: Icons.add_circle_outline,
            onPressed: onCreate,
          );
        }

        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _RecordCard(record: record, onTap: () => onEdit(record)),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: () => onEdit(record),
              icon: const Icon(Icons.edit),
              label: const Text('Editar hoje'),
            ),
          ],
        );
      },
    );
  }
}

class _MonthTab extends StatelessWidget {
  const _MonthTab({
    required this.future,
    required this.visibleMonth,
    required this.onPreviousMonth,
    required this.onNextMonth,
    required this.onCreate,
    required this.onEdit,
    required this.onRetry,
  });

  final Future<List<TimeRecord>> future;
  final DateTime visibleMonth;
  final VoidCallback onPreviousMonth;
  final VoidCallback onNextMonth;
  final VoidCallback onCreate;
  final ValueChanged<TimeRecord> onEdit;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 4),
          child: Row(
            children: [
              IconButton(
                tooltip: 'Mes anterior',
                onPressed: onPreviousMonth,
                icon: const Icon(Icons.chevron_left),
              ),
              Expanded(
                child: Text(
                  monthLabel(visibleMonth),
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
              IconButton(
                tooltip: 'Proximo mes',
                onPressed: onNextMonth,
                icon: const Icon(Icons.chevron_right),
              ),
              IconButton(
                tooltip: 'Adicionar dia',
                onPressed: onCreate,
                icon: const Icon(Icons.add),
              ),
            ],
          ),
        ),
        Expanded(
          child: FutureBuilder<List<TimeRecord>>(
            future: future,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }

              if (snapshot.hasError) {
                return _ErrorState(message: snapshot.error.toString(), onRetry: onRetry);
              }

              final records = snapshot.data ?? [];
              if (records.isEmpty) {
                return _EmptyState(
                  title: 'Nenhum registro neste mes',
                  actionLabel: 'Adicionar dia',
                  icon: Icons.add,
                  onPressed: onCreate,
                );
              }

              return RefreshIndicator(
                onRefresh: () async => onRetry(),
                child: ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                  itemBuilder: (context, index) {
                    final record = records[index];
                    return _RecordCard(record: record, onTap: () => onEdit(record));
                  },
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemCount: records.length,
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _RecordCard extends StatelessWidget {
  const _RecordCard({required this.record, required this.onTap});

  final TimeRecord record;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final label = dayTypeLabels[record.dayType] ?? record.dayType;
    final statusLabel = statusLabels[record.status] ?? record.status;

    return Card(
      margin: EdgeInsets.zero,
      child: ListTile(
        onTap: onTap,
        title: Text(formatDisplayDate(record.date)),
        subtitle: Text('$label · $statusLabel'),
        trailing: const Icon(Icons.chevron_right),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({
    required this.title,
    required this.actionLabel,
    required this.icon,
    required this.onPressed,
  });

  final String title;
  final String actionLabel;
  final IconData icon;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 40, color: Theme.of(context).colorScheme.primary),
            const SizedBox(height: 12),
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: onPressed,
              icon: Icon(icon),
              label: Text(actionLabel),
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off, size: 40),
            const SizedBox(height: 12),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Tentar de novo'),
            ),
          ],
        ),
      ),
    );
  }
}

