from typing import Annotated

from ..models import Session, User
from ..database import get_db_session

from fastapi import Depends
from sqlalchemy import and_, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

DatabaseDependency = Annotated[AsyncSession, Depends(get_db_session)]


class SessionRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_user_by_email_or_matric(self, email: str = None, matric: str = None):
        stmt = select(User).filter(or_(User.email == email, User.user_matric == matric))
        result = await self.db_session.execute(stmt)
        user = result.scalars().first()

        return user

    async def get_user_session_by_token(self, session_token):
        stmt = (
            select(Session)
            .options(selectinload(Session.user))
            .filter(and_(Session.token == session_token, Session.is_expired == False))
        )

        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def get_user_session_by_matric(self, user_matric: str):
        stmt = select(Session).filter(
            and_(Session.user_id == user_matric, Session.is_expired == False)
        )
        result = await self.db_session.execute(stmt)

        return result.scalars().first()


def get_session_repository(db_session: DatabaseDependency):
    return SessionRepository(db_session)
