import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:taller_cliente/features/estimate/domain/entities/public_estimate.dart';

class EstimateTotalSection extends StatelessWidget {
  const EstimateTotalSection({super.key, required this.estimate});
  final PublicEstimate estimate;

  @override
  Widget build(BuildContext context) {
    final fmt = NumberFormat.currency(
      locale: 'es_CL',
      symbol: estimate.currency == 'CLP' ? '\$' : estimate.currency,
      decimalDigits: estimate.currency == 'CLP' ? 0 : 2,
    );
    final cs = Theme.of(context).colorScheme;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _TotalRow(
              label: 'Subtotal',
              value: fmt.format(estimate.subtotal),
            ),
            _TotalRow(
              label: 'IVA (${(estimate.taxRate * 100).toStringAsFixed(0)}%)',
              value: fmt.format(estimate.taxAmount),
            ),
            const Divider(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'TOTAL',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                Text(
                  fmt.format(estimate.total),
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: cs.primary,
                      ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _TotalRow extends StatelessWidget {
  const _TotalRow({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant)),
          Text(value),
        ],
      ),
    );
  }
}
