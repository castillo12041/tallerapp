import 'package:dio/dio.dart';
import 'package:taller_cliente/core/config/app_config.dart';
import 'package:taller_cliente/core/network/api_exception.dart';

/// Cliente HTTP singleton para todos los datasources del portal.
class ApiClient {
  ApiClient._() : _dio = _buildDio();

  static final ApiClient instance = ApiClient._();

  final Dio _dio;

  static Dio _buildDio() {
    final dio = Dio(
      BaseOptions(
        baseUrl: AppConfig.apiBaseUrl,
        connectTimeout: AppConfig.connectTimeout,
        receiveTimeout: AppConfig.receiveTimeout,
        headers: const {'Content-Type': 'application/json'},
      ),
    );
    dio.interceptors.add(_ExceptionInterceptor());
    return dio;
  }

  Future<Map<String, dynamic>> get(String path) async {
    final response = await _dio.get<Map<String, dynamic>>(path);
    return response.data!;
  }

  Future<void> post(String path, {Map<String, dynamic>? body}) async {
    await _dio.post<void>(path, data: body);
  }
}

class _ExceptionInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final statusCode = err.response?.statusCode;
    final detail = _extractDetail(err.response?.data);

    if (err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        err.type == DioExceptionType.connectionError) {
      handler.reject(
        _wrap(err, NetworkException('Sin conexión. Verifica tu red e intenta nuevamente.')),
      );
      return;
    }

    switch (statusCode) {
      case 404:
        handler.reject(_wrap(err, NotFoundException(detail ?? 'Enlace no encontrado.')));
      case 409:
        handler.reject(_wrap(err, ConflictException(detail ?? 'Operación no permitida.')));
      case >= 500:
        handler.reject(_wrap(err, ServerException('Error del servidor. Intenta más tarde.')));
      default:
        handler.reject(_wrap(err, ApiException(detail ?? 'Error inesperado.')));
    }
  }

  String? _extractDetail(dynamic data) {
    if (data is Map<String, dynamic>) {
      return data['detail']?.toString();
    }
    return null;
  }

  DioException _wrap(DioException original, ApiException cause) {
    return DioException(
      requestOptions: original.requestOptions,
      response: original.response,
      type: original.type,
      error: cause,
    );
  }
}
