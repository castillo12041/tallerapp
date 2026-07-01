import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:taller_cliente/core/network/api_exception.dart';
import 'package:taller_cliente/features/inspection_report/application/providers/inspection_report_provider.dart';
import 'package:taller_cliente/features/inspection_report/presentation/widgets/score_banner.dart';
import 'package:taller_cliente/features/inspection_report/presentation/widgets/vehicle_info_card.dart';
import 'package:taller_cliente/features/inspection_report/presentation/widgets/verification_badge.dart';
import 'package:taller_cliente/features/shared/presentation/widgets/error_screen.dart';
import 'package:taller_cliente/features/shared/presentation/widgets/loading_screen.dart';

class InspectionReportPage extends ConsumerWidget {
  const InspectionReportPage({super.key, required this.token});
  final String token;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncValue = ref.watch(qrVerificationProvider(token));

    return asyncValue.when(
      loading: () => const LoadingScreen(message: 'Verificando informe...'),
      error: (error, _) => ErrorScreen(
        message: _errorMessage(error),
        onRetry: () => ref.invalidate(qrVerificationProvider(token)),
      ),
      data: (verification) {
        if (!verification.valid) {
          return ErrorScreen(
            message: verification.reason ??
                (verification.revoked
                    ? 'Este código QR ha sido revocado por el taller.'
                    : 'El enlace no es válido o ha expirado.'),
          );
        }
        final inspection = verification.inspection!;
        return Scaffold(
          appBar: AppBar(
            title: const Text('Informe de Inspección'),
            automaticallyImplyLeading: false,
          ),
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                VerificationBadge(
                  isValid: verification.valid,
                  expiresAt: verification.expiresAt,
                  revoked: verification.revoked,
                ),
                const SizedBox(height: 16),
                VehicleInfoCard(inspection: inspection),
                if (inspection.score != null) ...[
                  const SizedBox(height: 16),
                  ScoreBanner(score: inspection.score!),
                ],
                const SizedBox(height: 16),
                _StatusCard(
                  status: inspection.status,
                  completedAt: inspection.completedAt,
                ),
                const SizedBox(height: 24),
                _InfoBanner(),
              ],
            ),
          ),
        );
      },
    );
  }

  String _errorMessage(Object error) {
    return switch (error) {
      NotFoundException() => 'El enlace no es válido o ha expirado.',
      NetworkException() => 'Sin conexión. Verifica tu red e intenta nuevamente.',
      _ => 'No se pudo cargar el informe. Intenta nuevamente.',
    };
  }
}

class _StatusCard extends StatelessWidget {
  const _StatusCard({required this.status, this.completedAt});
  final String status;
  final DateTime? completedAt;

  @override
  Widget build(BuildContext context) {
    final label = switch (status) {
      'completed' => 'Completada',
      'review' => 'En revisión',
      'in_progress' => 'En progreso',
      _ => status,
    };
    return Card(
      child: ListTile(
        leading: const Icon(Icons.assignment_turned_in_rounded),
        title: Text('Estado de inspección'),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
            if (completedAt != null)
              Text(
                'Completada el ${DateFormat('dd/MM/yyyy HH:mm').format(completedAt!.toLocal())}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
          ],
        ),
      ),
    );
  }
}

class _InfoBanner extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Icon(Icons.info_outline_rounded,
              color: Theme.of(context).colorScheme.onSurfaceVariant, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              'Este informe fue generado por un profesional certificado. '
              'El código QR garantiza su autenticidad.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}
