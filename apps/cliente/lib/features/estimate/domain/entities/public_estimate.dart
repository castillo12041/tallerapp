import 'package:freezed_annotation/freezed_annotation.dart';

part 'public_estimate.freezed.dart';

@freezed
class VehicleSnapshot with _$VehicleSnapshot {
  const factory VehicleSnapshot({
    required String id,
    required String plate,
    required String make,
    required String model,
    int? year,
    String? color,
    String? vin,
  }) = _VehicleSnapshot;
}

@freezed
class ClientSnapshot with _$ClientSnapshot {
  const factory ClientSnapshot({
    required String id,
    required String fullName,
    String? email,
    String? phone,
    String? rut,
  }) = _ClientSnapshot;
}

@freezed
class EstimateItemEntity with _$EstimateItemEntity {
  const factory EstimateItemEntity({
    required String id,
    required String name,
    required double quantity,
    required double unitPrice,
    required double subtotal,
    String? category,
    String? description,
  }) = _EstimateItemEntity;
}

@freezed
class PublicEstimate with _$PublicEstimate {
  const factory PublicEstimate({
    required String number,
    required String status,
    required VehicleSnapshot vehicleSnapshot,
    ClientSnapshot? clientSnapshot,
    required List<EstimateItemEntity> items,
    required double subtotal,
    required double taxRate,
    required double taxAmount,
    required double total,
    required String currency,
    String? notes,
    DateTime? validUntil,
  }) = _PublicEstimate;

  const PublicEstimate._();

  bool get isRespondable => status == 'sent' || status == 'viewed';
  bool get isAccepted => status == 'accepted';
  bool get isRejected => status == 'rejected';
  bool get isExpired =>
      validUntil != null && DateTime.now().isAfter(validUntil!);
}
