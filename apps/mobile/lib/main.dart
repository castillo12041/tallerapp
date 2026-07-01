import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tallerapp/core/router/app_router.dart';
import 'package:tallerapp/core/theme/app_theme.dart';

// Firebase se inicializa en Fase 1 (Autenticación).
// Requiere ejecutar: flutterfire configure
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ProviderScope(child: TallerApp()));
}

class TallerApp extends ConsumerWidget {
  const TallerApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);

    return MaterialApp.router(
      title: 'Taller Inspección',
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.system,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
