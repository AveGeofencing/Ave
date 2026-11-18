from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from ..settings import APP_SETTINGS


class Base(DeclarativeBase):
    pass


engine = create_async_engine(url=APP_SETTINGS.DATABASE_URL, echo=APP_SETTINGS.ECHO_SQL)
SessionLocal = async_sessionmaker(bind=engine, autocommit=False, expire_on_commit=False)


async def get_db_session():
    async with SessionLocal() as session:
        yield session  # Automatically manages commit/rollback
