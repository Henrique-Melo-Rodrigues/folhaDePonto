import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/time_record.dart';
import '../services/time_record_api.dart';

class TimeRecordFormScreen extends StatefulWidget {
  const TimeRecordFormScreen({
    super.key,
    required this.api,
    required this.selectedDate,
    this.initialRecord,
  });

  final TimeRecordApi api;
  final DateTime selectedDate;
  final TimeRecord? initialRecord;

  @override
  State<TimeRecordFormScreen> createState() => _TimeRecordFormScreenState();
}

class _TimeRecordFormScreenState extends State<TimeRecordFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late DateTime _date;
  late String _dayType;
  late final TextEditingController _arrivalController;
  late final TextEditingController _lunchStartController;
  late final TextEditingController _lunchEndController;
  late final TextEditingController _departureController;
  late final TextEditingController _notesController;
  bool _isSaving = false;

  bool get _isEditing => widget.initialRecord != null;

  @override
  void initState() {
    super.initState();
    final record = widget.initialRecord;
    _date = record == null ? widget.selectedDate : parseApiDate(record.date);
    _dayType = record?.dayType ?? 'trabalho';
    _arrivalController = TextEditingController(text: record?.times.arrival ?? '');
    _lunchStartController = TextEditingController(text: record?.times.lunchStart ?? '');
    _lunchEndController = TextEditingController(text: record?.times.lunchEnd ?? '');
    _departureController = TextEditingController(text: record?.times.departure ?? '');
    _notesController = TextEditingController(text: record?.notes ?? '');
  }

  @override
  void dispose() {
    _arrivalController.dispose();
    _lunchStartController.dispose();
    _lunchEndController.dispose();
    _departureController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    if (_isEditing) {
      return;
    }

    final picked = await showDatePicker(
      context: context,
      firstDate: DateTime(_date.year - 2),
      lastDate: DateTime(_date.year + 2),
      initialDate: _date,
    );

    if (picked != null) {
      setState(() => _date = picked);
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() => _isSaving = true);
    final record = TimeRecord(
      date: formatApiDate(_date),
      dayType: _dayType,
      times: TimeRecordTimes(
        arrival: _arrivalController.text,
        lunchStart: _lunchStartController.text,
        lunchEnd: _lunchEndController.text,
        departure: _departureController.text,
      ),
      notes: _notesController.text.trim(),
      status: widget.initialRecord?.status ?? 'incomplete',
    );

    try {
      if (_isEditing) {
        await widget.api.update(record);
      } else {
        await widget.api.create(record);
      }

      if (mounted) {
        Navigator.of(context).pop(true);
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error.toString())),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }

  Future<void> _delete() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Apagar registro?'),
        content: Text(formatDisplayDate(formatApiDate(_date))),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Apagar'),
          ),
        ],
      ),
    );

    if (confirmed != true) {
      return;
    }

    setState(() => _isSaving = true);
    try {
      await widget.api.delete(formatApiDate(_date));
      if (mounted) {
        Navigator.of(context).pop(true);
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error.toString())),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isEditing ? 'Editar dia' : 'Novo dia'),
        actions: [
          if (_isEditing)
            IconButton(
              tooltip: 'Apagar',
              onPressed: _isSaving ? null : _delete,
              icon: const Icon(Icons.delete_outline),
            ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.event),
              title: const Text('Data'),
              subtitle: Text(formatDisplayDate(formatApiDate(_date))),
              trailing: _isEditing ? null : const Icon(Icons.edit_calendar),
              onTap: _pickDate,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _dayType,
              decoration: const InputDecoration(labelText: 'Tipo do dia'),
              items: [
                for (final type in dayTypes)
                  DropdownMenuItem(
                    value: type,
                    child: Text(dayTypeLabels[type] ?? type),
                  ),
              ],
              onChanged: _isSaving ? null : (value) => setState(() => _dayType = value!),
            ),
            const SizedBox(height: 12),
            _TimeField(label: 'Entrada', controller: _arrivalController),
            const SizedBox(height: 12),
            _TimeField(label: 'Saida almoco', controller: _lunchStartController),
            const SizedBox(height: 12),
            _TimeField(label: 'Retorno almoco', controller: _lunchEndController),
            const SizedBox(height: 12),
            _TimeField(label: 'Saida final', controller: _departureController),
            const SizedBox(height: 12),
            TextFormField(
              controller: _notesController,
              enabled: !_isSaving,
              decoration: const InputDecoration(labelText: 'Observacoes'),
              minLines: 3,
              maxLines: 5,
            ),
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: _isSaving ? null : _save,
              icon: _isSaving
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.save),
              label: const Text('Salvar'),
            ),
          ],
        ),
      ),
    );
  }
}

class _TimeField extends StatelessWidget {
  const _TimeField({required this.label, required this.controller});

  final String label;
  final TextEditingController controller;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      decoration: InputDecoration(labelText: label, hintText: 'HH:MM'),
      keyboardType: TextInputType.datetime,
      inputFormatters: [
        FilteringTextInputFormatter.allow(RegExp(r'[0-9:]')),
        LengthLimitingTextInputFormatter(5),
      ],
      validator: _validateTime,
    );
  }

  String? _validateTime(String? value) {
    final text = value?.trim() ?? '';
    if (text.isEmpty) {
      return null;
    }

    final match = RegExp(r'^(\d{2}):(\d{2})$').firstMatch(text);
    if (match == null) {
      return 'Use HH:MM';
    }

    final hour = int.parse(match.group(1)!);
    final minute = int.parse(match.group(2)!);
    if (hour > 23 || minute > 59) {
      return 'Horario invalido';
    }

    return null;
  }
}

