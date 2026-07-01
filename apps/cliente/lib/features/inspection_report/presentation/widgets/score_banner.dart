import 'package:flutter/material.dart';
import 'package:taller_cliente/app/theme.dart';

class ScoreBanner extends StatelessWidget {
  const ScoreBanner({super.key, required this.score});
  final double score;

  @override
  Widget build(BuildContext context) {
    final color = StatusColors.forScore(score);
    final label = score >= 80
        ? 'Excelente estado'
        : score >= 60
            ? 'Estado aceptable'
            : 'Requiere atención';

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 24),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Text(
            '${score.toStringAsFixed(0)}',
            style: Theme.of(context).textTheme.displaySmall?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: Colors.white70,
                ),
          ),
          Text(
            'Puntuación sobre 100',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.white54,
                ),
          ),
        ],
      ),
    );
  }
}
