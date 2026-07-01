import 'package:flutter/material.dart';
import 'package:taller_cliente/features/inspection_report/domain/entities/inspection_summary.dart';

class VehicleInfoCard extends StatelessWidget {
  const VehicleInfoCard({super.key, required this.inspection});
  final InspectionSummary inspection;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.directions_car_rounded,
                    color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  'Vehículo',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            _Row(label: 'Patente', value: inspection.vehiclePlate),
            _Row(
              label: 'Vehículo',
              value:
                  '${inspection.vehicleMake} ${inspection.vehicleModel}${inspection.vehicleYear != null ? ' (${inspection.vehicleYear})' : ''}',
            ),
            _Row(label: 'N° Inspección', value: inspection.number),
          ],
        ),
      ),
    );
  }
}

class _Row extends StatelessWidget {
  const _Row({required this.label, required this.value});
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
          Text(value, style: const TextStyle(fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
