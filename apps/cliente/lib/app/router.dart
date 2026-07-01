import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:taller_cliente/features/estimate/presentation/pages/estimate_page.dart';
import 'package:taller_cliente/features/inspection_report/presentation/pages/inspection_report_page.dart';
import 'package:taller_cliente/features/shared/presentation/pages/not_found_page.dart';

final GoRouter appRouter = GoRouter(
  debugLogDiagnostics: false,
  initialLocation: '/',
  errorBuilder: (context, state) => const NotFoundPage(),
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const _LandingPage(),
    ),
    GoRoute(
      path: '/informe/:token',
      builder: (context, state) => InspectionReportPage(
        token: state.pathParameters['token']!,
      ),
    ),
    GoRoute(
      path: '/presupuesto/:token',
      builder: (context, state) => EstimatePage(
        token: state.pathParameters['token']!,
      ),
    ),
  ],
);

/// Página de inicio simple — redirige al cliente a usar el enlace específico.
class _LandingPage extends StatelessWidget {
  const _LandingPage();

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.directions_car_rounded, size: 64, color: cs.primary),
              const SizedBox(height: 24),
              Text(
                'Portal de Clientes',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 12),
              Text(
                'Accede mediante el enlace enviado por tu taller.',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: cs.onSurfaceVariant,
                    ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
