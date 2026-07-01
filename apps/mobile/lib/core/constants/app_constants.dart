abstract final class AppConstants {
  static const String appName = 'Taller Inspección';

  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api/v1',
  );

  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 30);

  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
}
