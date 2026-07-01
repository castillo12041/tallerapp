import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:taller_cliente/core/network/api_exception.dart';
import 'package:taller_cliente/features/estimate/application/providers/estimate_provider.dart';
import 'package:taller_cliente/features/estimate/domain/entities/public_estimate.dart';
import 'package:taller_cliente/features/estimate/presentation/widgets/estimate_items_list.dart';
import 'package:taller_cliente/features/estimate/presentation/widgets/estimate_total_section.dart';
import 'package:taller_cliente/features/estimate/presentation/widgets/respond_bottom_sheet.dart';
import 'package:taller_cliente/features/shared/presentation/widgets/error_screen.dart';
import 'package:taller_cliente/features/shared/presentation/widgets/loading_screen.dart';

class EstimatePage extends ConsumerWidget {
  const EstimatePage({super.key, required this.token});
  final String token;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncValue = ref.watch(publicEstimateProvider(token));

    return asyncValue.when(
      loading: () => const LoadingScreen(message: 'Cargando presupuesto...'),
      error: (error, _) => ErrorScreen(
        message: _errorMessage(error),
        onRetry: () => ref.invalidate(publicEstimateProvider(token)),
      ),
      data: (estimate) => _EstimateView(token: token, estimate: estimate),
    );
  }

  String _errorMessage(Object error) => switch (error) {
        NotFoundException() => 'El enlace del presupuesto no es válido o ha expirado.',
        ConflictException() => 'Este presupuesto ya fue respondido.',
        NetworkException() => 'Sin conexión. Verifica tu red e intenta nuevamente.',
        _ => 'No se pudo cargar el presupuesto. Intenta nuevamente.',
      };
}

class _EstimateView extends ConsumerWidget {
  const _EstimateView({required this.token, required this.estimate});
  final String token;
  final PublicEstimate estimate;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final respondState = ref.watch(estimateRespondProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text('Presupuesto ${estimate.number}'),
        automaticallyImplyLeading: false,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _StatusBanner(estimate: estimate),
            const SizedBox(height: 16),
            _VehicleCard(estimate: estimate),
            const SizedBox(height: 16),
            EstimateItemsList(
              items: estimate.items,
              currency: estimate.currency,
            ),
            const SizedBox(height: 8),
            EstimateTotalSection(estimate: estimate),
            if (estimate.notes != null) ...[
              const SizedBox(height: 8),
              _NotesCard(notes: estimate.notes!),
            ],
            if (estimate.validUntil != null && estimate.isRespondable) ...[
              const SizedBox(height: 8),
              _ValidUntilBadge(validUntil: estimate.validUntil!),
            ],
            const SizedBox(height: 24),
            if (estimate.isRespondable)
              _RespondButtons(
                token: token,
                loading: respondState.isLoading,
                ref: ref,
                context: context,
              ),
            if (estimate.isAccepted)
              const _ResponseBadge(accepted: true),
            if (estimate.isRejected)
              const _ResponseBadge(accepted: false),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

class _StatusBanner extends StatelessWidget {
  const _StatusBanner({required this.estimate});
  final PublicEstimate estimate;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final (label, color, icon) = switch (estimate.status) {
      'sent' || 'viewed' => ('Pendiente de respuesta', cs.primary, Icons.pending_rounded),
      'accepted' => ('Aceptado', const Color(0xFF2E7D32), Icons.check_circle_rounded),
      'rejected' => ('Rechazado', cs.error, Icons.cancel_rounded),
      'converted' => ('Convertido a OT', cs.tertiary, Icons.build_circle_rounded),
      _ => ('Borrador', cs.outline, Icons.edit_rounded),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 22),
          const SizedBox(width: 10),
          Text(label, style: TextStyle(color: color, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

class _VehicleCard extends StatelessWidget {
  const _VehicleCard({required this.estimate});
  final PublicEstimate estimate;

  @override
  Widget build(BuildContext context) {
    final vs = estimate.vehicleSnapshot;
    final cs = estimate.clientSnapshot;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Icon(Icons.directions_car_rounded,
                  color: Theme.of(context).colorScheme.primary),
              const SizedBox(width: 8),
              Text('Vehículo',
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.bold)),
            ]),
            const SizedBox(height: 10),
            _InfoRow('Patente', vs.plate),
            _InfoRow('Vehículo',
                '${vs.make} ${vs.model}${vs.year != null ? ' (${vs.year})' : ''}'),
            if (cs != null) _InfoRow('Cliente', cs.fullName),
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label,
                style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurfaceVariant)),
            Text(value,
                style: const TextStyle(fontWeight: FontWeight.w500)),
          ],
        ),
      );
}

class _NotesCard extends StatelessWidget {
  const _NotesCard({required this.notes});
  final String notes;

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          leading: const Icon(Icons.note_rounded),
          title: const Text('Observaciones del taller'),
          subtitle: Text(notes),
        ),
      );
}

class _ValidUntilBadge extends StatelessWidget {
  const _ValidUntilBadge({required this.validUntil});
  final DateTime validUntil;

  @override
  Widget build(BuildContext context) {
    final fmt = DateFormat('dd/MM/yyyy');
    final expired = DateTime.now().isAfter(validUntil);
    final color =
        expired ? Theme.of(context).colorScheme.error : const Color(0xFFF57F17);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(children: [
        Icon(Icons.timer_outlined, color: color, size: 18),
        const SizedBox(width: 8),
        Text(
          expired
              ? 'Presupuesto vencido el ${fmt.format(validUntil.toLocal())}'
              : 'Válido hasta el ${fmt.format(validUntil.toLocal())}',
          style: TextStyle(color: color, fontSize: 13),
        ),
      ]),
    );
  }
}

class _RespondButtons extends StatelessWidget {
  const _RespondButtons({
    required this.token,
    required this.loading,
    required this.ref,
    required this.context,
  });
  final String token;
  final bool loading;
  final WidgetRef ref;
  final BuildContext context;

  Future<void> _respond(bool accepting) async {
    final result = await showRespondSheet(context, accepting: accepting);
    if (result == null || !result.confirmed) return;

    await ref.read(estimateRespondProvider.notifier).respond(
          token: token,
          accepted: accepting,
          clientNotes: result.notes,
        );

    if (!context.mounted) return;

    final state = ref.read(estimateRespondProvider);
    if (state.hasError) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(state.error.toString()),
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(accepting
              ? '✓ Presupuesto aceptado. El taller fue notificado.'
              : 'Presupuesto rechazado.'),
        ),
      );
      ref.invalidate(publicEstimateProvider(token));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return const Center(child: CircularProgressIndicator());
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        FilledButton.icon(
          onPressed: () => _respond(true),
          icon: const Icon(Icons.check_rounded),
          label: const Text('Aceptar presupuesto'),
        ),
        const SizedBox(height: 10),
        OutlinedButton.icon(
          onPressed: () => _respond(false),
          icon: const Icon(Icons.close_rounded),
          label: const Text('Rechazar presupuesto'),
          style: OutlinedButton.styleFrom(
            foregroundColor: Theme.of(context).colorScheme.error,
            side: BorderSide(color: Theme.of(context).colorScheme.error),
          ),
        ),
      ],
    );
  }
}

class _ResponseBadge extends StatelessWidget {
  const _ResponseBadge({required this.accepted});
  final bool accepted;

  @override
  Widget build(BuildContext context) {
    final color = accepted ? const Color(0xFF2E7D32) : Theme.of(context).colorScheme.error;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            accepted ? Icons.check_circle_rounded : Icons.cancel_rounded,
            color: color,
          ),
          const SizedBox(width: 10),
          Text(
            accepted
                ? 'Has aceptado este presupuesto'
                : 'Has rechazado este presupuesto',
            style: TextStyle(color: color, fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }
}
