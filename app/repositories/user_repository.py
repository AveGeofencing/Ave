from typing import Annotated
from fastapi import Depends
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, update
from pydantic import EmailStr

from ..schemas.user_schema import UserCreateModel
from ..models import User
from ..utils import logger


class UserRepository:
    @classmethod
    async def create_new_user(cls, user: UserCreateModel, conn: AsyncSession):
        new_user: User = User(
            id=user.user_id,
            email=user.email,
            user_matric=user.user_matric,
            role=user.role,
            username=user.username,
            hashed_password=user.password,
        )

        conn.add(new_user)
        await conn.flush()
        await conn.refresh(new_user)

        return new_user

    @classmethod
    async def get_user_by_id(cls, user_id: str, conn: AsyncSession):
        stmt = select(User).where(User.id == user_id)
        result = await conn.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_user_by_email_or_matric(
        cls, conn: AsyncSession, email: str | EmailStr = None, matric: str = None,
    ) -> User:
        stmt = (
            select(User)
            .options(selectinload(User.attendances))
            .where(or_(User.email == email, User.user_matric == matric))
        )
        result = await conn.execute(stmt)

        user: User = result.scalar_one_or_none()

        return user

    @classmethod
    async def change_user_password(cls, user_id: str, new_hashed_password: str, conn: AsyncSession):
        stmt = update(User).where(User.id == user_id).values(hashed_password=new_hashed_password).returning(User.email)
        result = await conn.execute(stmt)
        row = result.scalar()
        logger.debug(f"Password changed for user {row}")
        return row
