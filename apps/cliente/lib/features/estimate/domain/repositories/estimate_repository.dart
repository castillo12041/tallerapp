import 'package:taller_cliente/features/estimate/domain/entities/public_estimate.dart';

abstract interface class EstimateRepository {
  Future<PublicEstimate> getPublicEstimate(String token);
  Future<void> respond({
    required String token,
    required bool accepted,
    String? clientNotes,
  });
}
