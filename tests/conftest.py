import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough")
os.environ.setdefault("MAIL_USERNAME", "test@example.com")
os.environ.setdefault("MAIL_PASSWORD", "password")
os.environ.setdefault("MAIL_FROM", "test@example.com")
os.environ.setdefault("MAIL_SERVER", "smtp.example.com")
os.environ.setdefault("MAIL_PORT", "587")
os.environ.setdefault("MAIL_STARTTLS", "true")
os.environ.setdefault("MAIL_SSL_TLS", "false")
os.environ.setdefault("USE_CREDENTIALS", "true")
os.environ.setdefault("VALIDATE_CERTS", "true")
