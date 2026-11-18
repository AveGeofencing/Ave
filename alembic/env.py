from logging.config import fileConfig
import os

from sqlalchemy import create_engine
from sqlalchemy import pool

from app.models import Base
from app.settings import APP_SETTINGS
from alembic import context

settings = APP_SETTINGS
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata


def get_database_url() -> str:
    """Resolve the database URL from Alembic -x parameters or env variables."""
    parameters = context.get_x_argument(as_dictionary=True)

    if "database_url" in parameters:
        url = parameters["database_url"]
    elif "database" in parameters:
        mode = parameters["database"].strip().lower()
        url = None

        if mode == "online":
            url = os.getenv("ALEMBIC_ONLINE_DATABASE_URL") or settings.ALEMBIC_ONLINE_DATABASE_URL
            if not url:
                raise RuntimeError(
                    "database=online requires ALEMBIC_ONLINE_DATABASE_URL"
                )
        elif mode == "local":
            url = os.getenv("ALEMBIC_DATABASE_URL") or settings.ALEMBIC_DATABASE_URL
            if not url:
                raise RuntimeError(
                    "database=local requires ALEMBIC_DATABASE_URL"
                )
        else:
            raise RuntimeError("database must be either 'local' or 'online'")
    elif "mode" in parameters:
        mode = parameters["mode"].strip().lower()
        if mode == "online":
            url = os.getenv("ALEMBIC_ONLINE_DATABASE_URL") or settings.ALEMBIC_ONLINE_DATABASE_URL
        else:
            if mode != "local":
                raise RuntimeError("mode must be either 'local' or 'online'")
            url = os.getenv("ALEMBIC_DATABASE_URL") or settings.ALEMBIC_DATABASE_URL
    else:
        # Positional -x values, for example: -x online
        positional_values = [
            value
            for value in context.get_x_argument(default="").split() 
            if value
        ]
        mode = "online" if "online" in positional_values else "local"

        if mode == "online":
            url = os.getenv("ALEMBIC_ONLINE_DATABASE_URL") or settings.ALEMBIC_ONLINE_DATABASE_URL
            if not url:
                raise RuntimeError(
                    "database=online requires ALEMBIC_ONLINE_DATABASE_URL"
                )
        else:
            url = os.getenv("ALEMBIC_DATABASE_URL") or settings.ALEMBIC_DATABASE_URL
            if not url:
                raise RuntimeError(
                    "database=local requires ALEMBIC_DATABASE_URL"
                )

    if not url:
        raise RuntimeError("No Alembic database URL was configured")

    # SQLAlchemy uses postgresql, rather than Heroku-style postgres, as the
    # canonical PostgreSQL dialect name.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    elif url.startswith("postgres+psycopg://"):
        url = url.replace("postgres+psycopg://", "postgresql+psycopg://", 1)

    return url

print(f"Found Alembic URL: {settings.ALEMBIC_DATABASE_URL}")
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(
        get_database_url(),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
