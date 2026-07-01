from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ------------------------------------------------------------------ #
    # Aplicación                                                           #
    # ------------------------------------------------------------------ #
    PROJECT_NAME: str = "Taller Inspección API"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production
    LOG_LEVEL: str = "INFO"  # DEBUG | INFO | WARNING | ERROR | CRITICAL

    # ------------------------------------------------------------------ #
    # URLs                                                                 #
    # ------------------------------------------------------------------ #
    API_V1_STR: str = "/api/v1"
    API_V2_STR: str = "/api/v2"
    PUBLIC_BASE_URL: str = "https://tallerinspeccion.tapsolutions.cl"

    # ------------------------------------------------------------------ #
    # CORS                                                                 #
    # ------------------------------------------------------------------ #
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5000",
        "http://localhost:57627",  # Flutter web dev
    ]

    # ------------------------------------------------------------------ #
    # Google Cloud Platform                                                #
    # ------------------------------------------------------------------ #
    GCP_PROJECT_ID: str = "taller-85514"
    USE_SECRET_MANAGER: bool = False  # True en producción con Cloud Run

    # ------------------------------------------------------------------ #
    # Firebase                                                             #
    # ------------------------------------------------------------------ #
    FIREBASE_PROJECT_ID: str = "taller-85514"
    FIREBASE_CREDENTIALS_PATH: str = "firebase_credentials.json"
    FIREBASE_STORAGE_BUCKET: str = "taller-85514.appspot.com"

    # ------------------------------------------------------------------ #
    # JWT interno (complementa Firebase Auth — no lo reemplaza)           #
    # ------------------------------------------------------------------ #
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ------------------------------------------------------------------ #
    # HMAC para tokens públicos (QR, informes, presupuestos)              #
    # ------------------------------------------------------------------ #
    HMAC_SECRET_KEY: str = ""
    QR_TOKEN_EXPIRY_DAYS: int = 365

    # ------------------------------------------------------------------ #
    # Rate limiting (por IP, ventana deslizante)                          #
    # ------------------------------------------------------------------ #
    RATE_LIMIT_CALLS: int = 60
    RATE_LIMIT_PERIOD_SECONDS: int = 60
    RATE_LIMIT_AUTH_CALLS: int = 10  # Más estricto para endpoints de auth

    # ------------------------------------------------------------------ #
    # Email — SendGrid (prioridad) o SMTP                                  #
    # ------------------------------------------------------------------ #
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@tallerinspeccion.tapsolutions.cl"
    SENDGRID_FROM_NAME: str = "Taller Inspección"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True

    # ------------------------------------------------------------------ #
    # WhatsApp — Twilio                                                    #
    # ------------------------------------------------------------------ #
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = ""  # Ej: "whatsapp:+14155238886"

    # ------------------------------------------------------------------ #
    # PDF                                                                  #
    # ------------------------------------------------------------------ #
    PDF_MAX_WORKERS: int = 2
    PDF_TIMEOUT_SECONDS: int = 30

    # ------------------------------------------------------------------ #
    # Monitoring                                                           #
    # ------------------------------------------------------------------ #
    SENTRY_DSN: str = ""

    # ------------------------------------------------------------------ #
    # Workers internos (Cloud Run — Fase 19)                              #
    # ------------------------------------------------------------------ #
    WORKERS_URL: str = ""
    WORKERS_API_KEY: str = ""


settings = Settings()
