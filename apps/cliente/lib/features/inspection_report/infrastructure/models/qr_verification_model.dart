import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:taller_cliente/features/inspection_report/domain/entities/inspection_summary.dart';

part 'qr_verification_model.freezed.dart';
part 'qr_verification_model.g.dart';

@freezed
class InspectionSummaryModel with _$InspectionSummaryModel {
  const factory InspectionSummaryModel({
    required String id,
    required String number,
    required String status,
    double? score,
    @JsonKey(name: 'vehicle_plate') required String vehiclePlate,
    @JsonKey(name: 'vehicle_make') required String vehicleMake,
    @JsonKey(name: 'vehicle_model') required String vehicleModel,
    @JsonKey(name: 'vehicle_year') int? vehicleYear,
    @JsonKey(name: 'completed_at') DateTime? completedAt,
  }) = _InspectionSummaryModel;

  factory InspectionSummaryModel.fromJson(Map<String, dynamic> json) =>
      _$InspectionSummaryModelFromJson(json);
}

@freezed
class QrVerificationModel with _$QrVerificationModel {
  const factory QrVerificationModel({
    required bool valid,
    @JsonKey(name: 'token_id') String? tokenId,
    InspectionSummaryModel? inspection,
    @JsonKey(name: 'expires_at') DateTime? expiresAt,
    @Default(false) bool revoked,
    String? reason,
  }) = _QrVerificationModel;

  factory QrVerificationModel.fromJson(Map<String, dynamic> json) =>
      _$QrVerificationModelFromJson(json);
}

extension QrVerificationModelMapper on QrVerificationModel {
  QrVerification toDomain() => QrVerification(
        valid: valid,
        tokenId: tokenId,
        inspection: inspection == null
            ? null
            : InspectionSummary(
                id: inspection!.id,
                number: inspection!.number,
                status: inspection!.status,
                score: inspection!.score,
                vehiclePlate: inspection!.vehiclePlate,
                vehicleMake: inspection!.vehicleMake,
                vehicleModel: inspection!.vehicleModel,
                vehicleYear: inspection!.vehicleYear,
                completedAt: inspection!.completedAt,
              ),
        expiresAt: expiresAt,
        revoked: revoked,
        reason: reason,
      );
}
