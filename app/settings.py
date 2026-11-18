from typing import Literal

from fastapi_mail import ConnectionConfig
from pydantic import EmailStr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    ALEMBIC_DATABASE_URL: str | None = None
    ALEMBIC_ONLINE_DATABASE_URL: str | None = None
    SECRET_KEY: str
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ECHO_SQL: bool = False
    WANT_SINGLE_SIGNIN: bool = False
    BASE_URL: str = "http://localhost:3000"
    COOKIE_DOMAIN: str | None = None
    COOKIE_SECURE: bool = True
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "none"
    CORS_ORIGINS: str = "http://localhost:3000,https://ave-frontend-service.onrender.com"
    PASSWORD_MIN_LENGTH: int = 8
    MAX_PHOTO_BYTES: int = 5 * 1024 * 1024
    AWS_REGION: str = "us-east-1"
    S3_REGION: str = "eu-west-2"
    S3_BUCKET: str = "ave-base-bucket"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


class EmailSettings(BaseSettings):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: bool
    VALIDATE_CERTS: bool

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


EMAIL_SETTINGS = EmailSettings()

email_config = ConnectionConfig(
    MAIL_USERNAME=EMAIL_SETTINGS.MAIL_USERNAME,
    MAIL_PASSWORD=SecretStr(EMAIL_SETTINGS.MAIL_PASSWORD),
    MAIL_FROM=EMAIL_SETTINGS.MAIL_FROM,
    MAIL_PORT=EMAIL_SETTINGS.MAIL_PORT,
    MAIL_SERVER=EMAIL_SETTINGS.MAIL_SERVER,
    MAIL_STARTTLS=EMAIL_SETTINGS.MAIL_STARTTLS,
    MAIL_SSL_TLS=EMAIL_SETTINGS.MAIL_SSL_TLS,
    USE_CREDENTIALS=EMAIL_SETTINGS.USE_CREDENTIALS,
    VALIDATE_CERTS=EMAIL_SETTINGS.VALIDATE_CERTS,
)

APP_SETTINGS = Settings()
