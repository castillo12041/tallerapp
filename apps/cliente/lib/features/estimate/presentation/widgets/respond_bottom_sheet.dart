import 'package:flutter/material.dart';

/// Bottom sheet para que el cliente acepte o rechace el presupuesto.
Future<_RespondResult?> showRespondSheet(
  BuildContext context, {
  required bool accepting,
}) {
  return showModalBottomSheet<_RespondResult>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    builder: (_) => _RespondSheet(accepting: accepting),
  );
}

class _RespondResult {
  const _RespondResult({required this.confirmed, this.notes});
  final bool confirmed;
  final String? notes;
}

class _RespondSheet extends StatefulWidget {
  const _RespondSheet({required this.accepting});
  final bool accepting;

  @override
  State<_RespondSheet> createState() => _RespondSheetState();
}

class _RespondSheetState extends State<_RespondSheet> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final isAccepting = widget.accepting;

    return Padding(
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        top: 24,
        bottom: MediaQuery.viewInsetsOf(context).bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Icon(
                isAccepting
                    ? Icons.check_circle_rounded
                    : Icons.cancel_rounded,
                color: isAccepting ? cs.primary : cs.error,
              ),
              const SizedBox(width: 12),
              Text(
                isAccepting ? 'Aceptar presupuesto' : 'Rechazar presupuesto',
                style: Theme.of(context).textTheme.titleLarge,
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            isAccepting
                ? '¿Confirmas que aceptas este presupuesto? El taller recibirá tu confirmación.'
                : '¿Confirmas que rechazas este presupuesto? Puedes dejarnos un comentario.',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _controller,
            maxLines: 3,
            decoration: InputDecoration(
              hintText: isAccepting
                  ? 'Comentario opcional...'
                  : 'Motivo del rechazo (opcional)...',
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 20),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(
              _RespondResult(
                confirmed: true,
                notes: _controller.text.trim().isEmpty
                    ? null
                    : _controller.text.trim(),
              ),
            ),
            style: isAccepting
                ? null
                : FilledButton.styleFrom(backgroundColor: cs.error),
            child: Text(isAccepting ? 'Confirmar aceptación' : 'Confirmar rechazo'),
          ),
          const SizedBox(height: 8),
          OutlinedButton(
            onPressed: () => Navigator.of(context).pop(null),
            child: const Text('Cancelar'),
          ),
        ],
      ),
    );
  }
}
