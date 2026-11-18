from logging.config import fileConfig
import os

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url

from app.models import Base
from app.settings import APP_SETTINGS

settings = APP_SETTINGS
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    """Resolve and normalize the database URL for Alembic migrations."""

    parameters = context.get_x_argument(as_dictionary=True)

    # 1. Explicit URL takes precedence.
    url = parameters.get("database_url")

    if not url:
        # 2. Resolve the requested database mode.
        mode = parameters.get("database") or parameters.get("mode")

        if mode:
            mode = mode.strip().lower()
        else:
            # Support: alembic -x online upgrade head
            positional_values = context.get_x_argument()
            mode = "online" if "online" in positional_values else "local"

        if mode not in ("local", "online"):
            raise RuntimeError("Database mode must be either 'local' or 'online'")

        # 3. Resolve the corresponding environment variable.
        env_var = (
            "ALEMBIC_ONLINE_DATABASE_URL"
            if mode == "online"
            else "ALEMBIC_DATABASE_URL"
        )

        url = os.getenv(env_var) or getattr(settings, env_var, None)

        if not url:
            raise RuntimeError(
                f"Database mode '{mode}' requires {env_var} to be configured"
            )

    # 4. Normalize PostgreSQL URLs for synchronous migrations.
    database_url = make_url(url)

    if database_url.get_backend_name() == "postgresql":
        database_url = database_url.set(drivername="postgresql+psycopg")

    return database_url.render_as_string(hide_password=False)


def run_migrations_offline() -> None:
    """Run migrations without creating an Engine."""

    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a synchronous database connection."""

    connectable = create_engine(
        get_database_url(),
        poolclass=pool.NullPool,
    )

    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
