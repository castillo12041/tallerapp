from fastapi import status


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "APP_ERROR",
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "No autorizado") -> None:
        super().__init__(
            message,
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "Acceso denegado") -> None:
        super().__init__(
            message,
            status.HTTP_403_FORBIDDEN,
            "FORBIDDEN",
        )


class NotFoundException(AppException):
    def __init__(self, message: str = "Recurso no encontrado") -> None:
        super().__init__(
            message,
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND",
        )


class ConflictException(AppException):
    def __init__(self, message: str = "Conflicto con el estado actual") -> None:
        super().__init__(
            message,
            status.HTTP_409_CONFLICT,
            "CONFLICT",
        )


class UnprocessableException(AppException):
    def __init__(self, message: str = "Error de validación") -> None:
        super().__init__(
            message,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "UNPROCESSABLE",
        )
