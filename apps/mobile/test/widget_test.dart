import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tallerapp/main.dart';

void main() {
  testWidgets('TallerApp renderiza sin errores', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: TallerApp()));
    await tester.pump();

    expect(find.byType(ProviderScope), findsOneWidget);
    expect(find.byType(MaterialApp), findsNothing); // Usa MaterialApp.router
  });

  testWidgets('Splash page muestra nombre de la app', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: TallerApp()));
    await tester.pumpAndSettle();

    expect(find.text('Taller Inspección'), findsOneWidget);
  });
}
