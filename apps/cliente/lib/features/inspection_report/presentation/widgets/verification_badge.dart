import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

class VerificationBadge extends StatelessWidget {
  const VerificationBadge({
    super.key,
    required this.isValid,
    this.expiresAt,
    this.revoked = false,
  });

  final bool isValid;
  final DateTime? expiresAt;
  final bool revoked;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final (icon, label, color) = switch ((isValid, revoked)) {
      (true, _) => (
          Icons.verified_rounded,
          'Informe verificado',
          cs.primary,
        ),
      (_, true) => (
          Icons.block_rounded,
          'QR revocado',
          cs.error,
        ),
      _ => (
          Icons.help_outline_rounded,
          'Token inválido',
          cs.error,
        ),
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
          Icon(icon, color: color, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: TextStyle(
                        color: color, fontWeight: FontWeight.w600)),
                if (isValid && expiresAt != null)
                  Text(
                    'Válido hasta ${DateFormat('dd/MM/yyyy').format(expiresAt!.toLocal())}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: cs.onSurfaceVariant,
                        ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
