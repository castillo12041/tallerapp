import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:taller_cliente/features/inspection_report/domain/entities/inspection_summary.dart';
import 'package:taller_cliente/features/inspection_report/infrastructure/repositories/inspection_report_repository_impl.dart';

part 'inspection_report_provider.g.dart';

@riverpod
Future<QrVerification> qrVerification(
  QrVerificationRef ref,
  String token,
) async {
  final repository = InspectionReportRepositoryImpl();
  return repository.verifyToken(token);
}
