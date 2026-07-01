import 'package:taller_cliente/features/estimate/domain/entities/public_estimate.dart';
import 'package:taller_cliente/features/estimate/domain/repositories/estimate_repository.dart';
import 'package:taller_cliente/features/estimate/infrastructure/datasources/estimate_api_datasource.dart';

class EstimateRepositoryImpl implements EstimateRepository {
  const EstimateRepositoryImpl({EstimateApiDatasource? datasource})
      : _datasource = datasource ?? const EstimateApiDatasource();

  final EstimateApiDatasource _datasource;

  @override
  Future<PublicEstimate> getPublicEstimate(String token) async {
    final model = await _datasource.getPublicEstimate(token);
    return model.toDomain();
  }

  @override
  Future<void> respond({
    required String token,
    required bool accepted,
    String? clientNotes,
  }) =>
      _datasource.respond(
        token: token,
        accepted: accepted,
        clientNotes: clientNotes,
      );
}
