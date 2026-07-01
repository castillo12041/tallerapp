abstract class AppException implements Exception {
  const AppException(this.message);

  final String message;

  @override
  String toString() => '$runtimeType: $message';
}

class ServerException extends AppException {
  const ServerException([super.message = 'Error del servidor']);
}

class UnauthorizedException extends AppException {
  const UnauthorizedException([super.message = 'No autorizado']);
}

class ForbiddenException extends AppException {
  const ForbiddenException([super.message = 'Acceso denegado']);
}

class NotFoundException extends AppException {
  const NotFoundException([super.message = 'Recurso no encontrado']);
}

class NetworkException extends AppException {
  const NetworkException([super.message = 'Error de conexión']);
}

class CacheException extends AppException {
  const CacheException([super.message = 'Error de caché local']);
}
