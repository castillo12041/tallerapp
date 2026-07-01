import 'package:taller_cliente/features/inspection_report/domain/entities/inspection_summary.dart';

abstract interface class InspectionReportRepository {
  Future<QrVerification> verifyToken(String token);
}
