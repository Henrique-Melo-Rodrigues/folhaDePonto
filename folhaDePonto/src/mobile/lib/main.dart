import 'package:flutter/material.dart';

import 'screens/home_screen.dart';
import 'services/time_record_api.dart';

void main() {
  runApp(FolhaDePontoApp(api: TimeRecordApi()));
}

class FolhaDePontoApp extends StatelessWidget {
  const FolhaDePontoApp({super.key, required this.api});

  final TimeRecordApi api;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Folha de Ponto',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2563EB),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
        inputDecorationTheme: const InputDecorationTheme(
          border: OutlineInputBorder(),
        ),
      ),
      home: HomeScreen(api: api),
    );
  }
}

