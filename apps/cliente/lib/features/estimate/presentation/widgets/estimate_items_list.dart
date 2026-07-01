import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:taller_cliente/features/estimate/domain/entities/public_estimate.dart';

class EstimateItemsList extends StatelessWidget {
  const EstimateItemsList({super.key, required this.items, required this.currency});
  final List<EstimateItemEntity> items;
  final String currency;

  @override
  Widget build(BuildContext context) {
    final fmt = NumberFormat.currency(
      locale: 'es_CL',
      symbol: currency == 'CLP' ? '\$' : currency,
      decimalDigits: currency == 'CLP' ? 0 : 2,
    );

    final grouped = <String, List<EstimateItemEntity>>{};
    for (final item in items) {
      final key = item.category ?? 'Sin categoría';
      grouped.putIfAbsent(key, () => []).add(item);
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Detalle del presupuesto',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 12),
            for (final entry in grouped.entries) ...[
              if (grouped.length > 1) ...[
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Text(
                    entry.key,
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                          color: Theme.of(context).colorScheme.primary,
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                ),
              ],
              for (final item in entry.value)
                _ItemRow(item: item, fmt: fmt),
              const Divider(height: 16),
            ],
          ],
        ),
      ),
    );
  }
}

class _ItemRow extends StatelessWidget {
  const _ItemRow({required this.item, required this.fmt});
  final EstimateItemEntity item;
  final NumberFormat fmt;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.name,
                    style: const TextStyle(fontWeight: FontWeight.w500)),
                if (item.description != null)
                  Text(item.description!,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Theme.of(context)
                                .colorScheme
                                .onSurfaceVariant,
                          )),
                Text(
                  '${item.quantity % 1 == 0 ? item.quantity.toInt() : item.quantity} × ${fmt.format(item.unitPrice)}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          Text(
            fmt.format(item.subtotal),
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }
}
