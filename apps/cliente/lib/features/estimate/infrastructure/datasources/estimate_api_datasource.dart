import 'package:dio/dio.dart';
import 'package:taller_cliente/core/network/api_client.dart';
import 'package:taller_cliente/core/network/api_exception.dart';
import 'package:taller_cliente/features/estimate/infrastructure/models/public_estimate_model.dart';

class EstimateApiDatasource {
  const EstimateApiDatasource({ApiClient? client})
      : _client = client ?? ApiClient.instance;

  final ApiClient _client;

  Future<PublicEstimateModel> getPublicEstimate(String token) async {
    try {
      final data = await _client.get('/estimates/public/$token');
      return PublicEstimateModel.fromJson(data);
    } on DioException catch (e) {
      throw e.error is ApiException
          ? e.error! as ApiException
          : NetworkException(e.message ?? 'Error de red');
    }
  }

  Future<void> respond({
    required String token,
    required bool accepted,
    String? clientNotes,
  }) async {
    try {
      await _client.post(
        '/estimates/public/$token/respond',
        body: {
          'accepted': accepted,
          if (clientNotes != null) 'client_notes': clientNotes,
        },
      );
    } on DioException catch (e) {
      throw e.error is ApiException
          ? e.error! as ApiException
          : NetworkException(e.message ?? 'Error de red');
    }
  }
}
