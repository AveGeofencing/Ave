from ..models.used_password_reset_tokens import UsedPasswordResetToken
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

class UsedPasswordResetTokenRepo:

    @classmethod
    async def add_reset_token(cls, conn: AsyncSession, token_value: str) -> UsedPasswordResetToken:
        password_reset_token: UsedPasswordResetToken = UsedPasswordResetToken(
            value=token_value
        )
        conn.add(password_reset_token)
        await conn.flush()
        await conn.refresh(password_reset_token)

        return password_reset_token


    @classmethod
    async def get_used_token(cls, conn: AsyncSession, token_value: str) -> UsedPasswordResetToken:
        stmt = select(UsedPasswordResetToken).where(UsedPasswordResetToken.value == token_value)
        result = await conn.execute(stmt)
        return result.scalar_one_or_none()