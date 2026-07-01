import 'package:freezed_annotation/freezed_annotation.dart';

part 'inspection_summary.freezed.dart';

@freezed
class InspectionSummary with _$InspectionSummary {
  const factory InspectionSummary({
    required String id,
    required String number,
    required String status,
    required double? score,
    required String vehiclePlate,
    required String vehicleMake,
    required String vehicleModel,
    required int? vehicleYear,
    required DateTime? completedAt,
  }) = _InspectionSummary;
}

@freezed
class QrVerification with _$QrVerification {
  const factory QrVerification({
    required bool valid,
    String? tokenId,
    InspectionSummary? inspection,
    DateTime? expiresAt,
    @Default(false) bool revoked,
    String? reason,
  }) = _QrVerification;
}
