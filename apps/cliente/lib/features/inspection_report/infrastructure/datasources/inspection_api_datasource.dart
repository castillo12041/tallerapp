import 'package:dio/dio.dart';
import 'package:taller_cliente/core/network/api_client.dart';
import 'package:taller_cliente/core/network/api_exception.dart';
import 'package:taller_cliente/features/inspection_report/infrastructure/models/qr_verification_model.dart';

class InspectionApiDatasource {
  InspectionApiDatasource({ApiClient? client})
      : _client = client ?? ApiClient.instance;

  final ApiClient _client;

  Future<QrVerificationModel> verifyToken(String token) async {
    try {
      final data = await _client.get('/qr/verify/$token');
      return QrVerificationModel.fromJson(data);
    } on DioException catch (e) {
      throw e.error is ApiException
          ? e.error! as ApiException
          : NetworkException(e.message ?? 'Error de red');
    }
  }
}
