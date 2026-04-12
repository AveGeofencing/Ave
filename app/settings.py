from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, SecretStr
from fastapi_mail import ConnectionConfig

class Settings(BaseSettings):
    DATABASE_URL: str
    ALEMBIC_DATABASE_URL: str | None = None
    SECRET_KEY: str
    ALGORITHM: str
    ECHO_SQL: bool = False
    WANT_SINGLE_SIGNIN: bool
    BASE_URL: str
    COOKIE_DOMAIN: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


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
        env_file=".env", extra="ignore",
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