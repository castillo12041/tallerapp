import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:taller_cliente/features/estimate/domain/entities/public_estimate.dart';

part 'public_estimate_model.freezed.dart';
part 'public_estimate_model.g.dart';

@freezed
class VehicleSnapshotModel with _$VehicleSnapshotModel {
  const factory VehicleSnapshotModel({
    required String id,
    required String plate,
    required String make,
    required String model,
    int? year,
    String? color,
    String? vin,
  }) = _VehicleSnapshotModel;

  factory VehicleSnapshotModel.fromJson(Map<String, dynamic> json) =>
      _$VehicleSnapshotModelFromJson(json);
}

@freezed
class ClientSnapshotModel with _$ClientSnapshotModel {
  const factory ClientSnapshotModel({
    required String id,
    @JsonKey(name: 'full_name') required String fullName,
    String? email,
    String? phone,
    String? rut,
  }) = _ClientSnapshotModel;

  factory ClientSnapshotModel.fromJson(Map<String, dynamic> json) =>
      _$ClientSnapshotModelFromJson(json);
}

@freezed
class EstimateItemModel with _$EstimateItemModel {
  const factory EstimateItemModel({
    required String id,
    required String name,
    required double quantity,
    @JsonKey(name: 'unit_price') required double unitPrice,
    required double subtotal,
    String? category,
    String? description,
  }) = _EstimateItemModel;

  factory EstimateItemModel.fromJson(Map<String, dynamic> json) =>
      _$EstimateItemModelFromJson(json);
}

@freezed
class PublicEstimateModel with _$PublicEstimateModel {
  const factory PublicEstimateModel({
    required String number,
    required String status,
    @JsonKey(name: 'vehicle_snapshot') required VehicleSnapshotModel vehicleSnapshot,
    @JsonKey(name: 'client_snapshot') ClientSnapshotModel? clientSnapshot,
    required List<EstimateItemModel> items,
    required double subtotal,
    @JsonKey(name: 'tax_rate') required double taxRate,
    @JsonKey(name: 'tax_amount') required double taxAmount,
    required double total,
    required String currency,
    String? notes,
    @JsonKey(name: 'valid_until') DateTime? validUntil,
  }) = _PublicEstimateModel;

  factory PublicEstimateModel.fromJson(Map<String, dynamic> json) =>
      _$PublicEstimateModelFromJson(json);
}

extension PublicEstimateModelMapper on PublicEstimateModel {
  PublicEstimate toDomain() {
    final vs = vehicleSnapshot;
    final cs = clientSnapshot;
    return PublicEstimate(
      number: number,
      status: status,
      vehicleSnapshot: VehicleSnapshot(
        id: vs.id, plate: vs.plate, make: vs.make, model: vs.model,
        year: vs.year, color: vs.color, vin: vs.vin,
      ),
      clientSnapshot: cs == null
          ? null
          : ClientSnapshot(
              id: cs.id, fullName: cs.fullName, email: cs.email,
              phone: cs.phone, rut: cs.rut,
            ),
      items: items
          .map((i) => EstimateItemEntity(
                id: i.id, name: i.name, quantity: i.quantity,
                unitPrice: i.unitPrice, subtotal: i.subtotal,
                category: i.category, description: i.description,
              ))
          .toList(),
      subtotal: subtotal,
      taxRate: taxRate,
      taxAmount: taxAmount,
      total: total,
      currency: currency,
      notes: notes,
      validUntil: validUntil,
    );
  }
}
