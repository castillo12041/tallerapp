import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:taller_cliente/app/router.dart';
import 'package:taller_cliente/app/theme.dart';

void main() {
  runApp(const ProviderScope(child: ClienteApp()));
}

class ClienteApp extends StatelessWidget {
  const ClienteApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Portal Cliente — Taller Inspección',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      routerConfig: appRouter,
    );
  }
}
