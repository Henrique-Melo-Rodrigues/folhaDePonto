import 'package:flutter/material.dart';

import 'data/local_time_record_store.dart';
import 'data/remote_time_record_store.dart';
import 'data/time_record_dao.dart';
import 'data/time_record_store.dart';
import 'screens/home_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(FolhaDePontoApp(store: buildStore()));
}

/// Composition root: o único lugar que conhece as implementações concretas.
///
/// Offline é o default — o app roda inteiro no aparelho, com SQLite embarcado.
/// O adapter remoto só entra quando o build define `API_BASE_URL`:
///
///     flutter build apk --dart-define=API_BASE_URL=http://192.168.0.106:8000 \
///                       --dart-define=API_KEY=<chave>
TimeRecordStore buildStore() {
  if (RemoteTimeRecordStore.defaultBaseUrl.isEmpty) {
    return LocalTimeRecordStore(dao: TimeRecordDao());
  }
  return RemoteTimeRecordStore();
}

class FolhaDePontoApp extends StatelessWidget {
  const FolhaDePontoApp({super.key, required this.store});

  final TimeRecordStore store;

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
      home: HomeScreen(store: store),
    );
  }
}
