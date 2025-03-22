from fastapi import Depends
from typing import Annotated, Union
from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_

from ..models import PasswordResetToken
from ..database import get_db_session

DatabaseDependency = Annotated[AsyncSession, Depends(get_db_session)]


class PasswordResetTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def set_token_is_used(
        self, token: Union[str, None] = None, user_matric: Union[str, None] = None
    ):
        stmt = (
            update(PasswordResetToken)
            .filter(
                or_(
                    PasswordResetToken.token == token,
                    PasswordResetToken.user_id == user_matric,
                )
            )
            .values(is_used=True)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_token(self, token: str) -> PasswordResetToken:
        stmt = select(PasswordResetToken).filter(PasswordResetToken.token == token)
        result = await self.session.execute(stmt)
        reset_token = result.scalars().first()
        return reset_token

    async def add_token(
        self, user_id: str, token: str, expires_at
    ) -> PasswordResetToken:

        new_token = PasswordResetToken(
            user_id=user_id, token=token, expires_at=expires_at
        )
        self.session.add(new_token)
        await self.session.commit()
        await self.session.refresh(new_token)

        return new_token

    async def get_token_by_matric(self, user_matric: str) -> PasswordResetToken:
        stmt = select(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_matric
        )
        result = await self.session.execute(stmt)
        reset_token = result.scalars().first()
        return reset_token

    async def deactivate_token(self, token: PasswordResetToken):
        stmt = select(PasswordResetToken).filter(PasswordResetToken.token == token)

        result = await self.session.execute(stmt)
        reset_token = result.scalars().first()
        reset_token.is_used = True
        await self.session.commit()


def get_password_reset_token_repository(
    db_session: DatabaseDependency,
) -> PasswordResetTokenRepository:
    return PasswordResetTokenRepository(session=db_session)
