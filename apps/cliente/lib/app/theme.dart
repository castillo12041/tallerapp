import 'package:flutter/material.dart';

abstract final class AppTheme {
  static ThemeData get light => ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1565C0), // Azul taller profesional
          brightness: Brightness.light,
        ),
        appBarTheme: const AppBarTheme(
          centerTitle: false,
          elevation: 0,
        ),
        cardTheme: const CardThemeData(
          elevation: 2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(12)),
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            minimumSize: const Size(double.infinity, 52),
            shape: const RoundedRectangleBorder(
              borderRadius: BorderRadius.all(Radius.circular(10)),
            ),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            minimumSize: const Size(double.infinity, 52),
            shape: const RoundedRectangleBorder(
              borderRadius: BorderRadius.all(Radius.circular(10)),
            ),
          ),
        ),
      );
}

/// Colores semánticos para estados de inspección y presupuesto.
abstract final class StatusColors {
  static Color good(BuildContext context) =>
      const Color(0xFF2E7D32); // green[800]

  static Color regular(BuildContext context) =>
      const Color(0xFFF57F17); // yellow[900]

  static Color bad(BuildContext context) =>
      const Color(0xFFC62828); // red[800]

  static Color pending(BuildContext context) =>
      Theme.of(context).colorScheme.outline;

  static Color forScore(double score) {
    if (score >= 80) return const Color(0xFF2E7D32);
    if (score >= 60) return const Color(0xFFF57F17);
    return const Color(0xFFC62828);
  }
}
