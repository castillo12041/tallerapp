/// Excepción tipada para errores de la API.
sealed class ApiException implements Exception {
  const ApiException(this.message);
  final String message;

  @override
  String toString() => message;
}

/// Token inválido, expirado o revocado.
final class TokenException extends ApiException {
  const TokenException(super.message);
}

/// Recurso no encontrado (404).
final class NotFoundException extends ApiException {
  const NotFoundException(super.message);
}

/// Operación no permitida en el estado actual (409).
final class ConflictException extends ApiException {
  const ConflictException(super.message);
}

/// Error de red (sin conexión, timeout).
final class NetworkException extends ApiException {
  const NetworkException(super.message);
}

/// Error inesperado del servidor (5xx).
final class ServerException extends ApiException {
  const ServerException(super.message);
}
