import 'package:taller_cliente/features/inspection_report/domain/entities/inspection_summary.dart';
import 'package:taller_cliente/features/inspection_report/domain/repositories/inspection_report_repository.dart';
import 'package:taller_cliente/features/inspection_report/infrastructure/datasources/inspection_api_datasource.dart';
import 'package:taller_cliente/features/inspection_report/infrastructure/models/qr_verification_model.dart';

class InspectionReportRepositoryImpl implements InspectionReportRepository {
  InspectionReportRepositoryImpl({InspectionApiDatasource? datasource})
      : _datasource = datasource ?? InspectionApiDatasource();

  final InspectionApiDatasource _datasource;

  @override
  Future<QrVerification> verifyToken(String token) async {
    final model = await _datasource.verifyToken(token);
    return model.toDomain();
  }
}
