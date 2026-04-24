from abc import ABC
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4, UUID

from jwt import PyJWTError, decode, encode, InvalidSignatureError, ExpiredSignatureError
from sqlalchemy import Delete, delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import InvalidTokenError
from ..models import Token
from ..schemas import UserOutputModel
from ..settings import APP_SETTINGS
from ..utils import logger


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_VERIFICATION = "account_verification"
    SIGNUP_SESSION = "signup_session"


    @property
    def lifetime(self) -> timedelta:
        return TOKEN_LIFETIMES[self]


TOKEN_LIFETIMES: dict[TokenType, timedelta] = {
    TokenType.ACCESS: timedelta(minutes=60),
    TokenType.PASSWORD_RESET: timedelta(minutes=10),
    TokenType.REFRESH: timedelta(weeks=1),
    TokenType.ACCOUNT_VERIFICATION: timedelta(minutes=15),
    TokenType.SIGNUP_SESSION: timedelta(minutes=15),  # short window

}


class BaseToken[DecodedType](ABC):
    token_type: TokenType

    @classmethod
    async def new(
        cls,
        sub: str,
        data: dict | None = None,
        jti: str | None = None,
        now: datetime | None = None,
        expires_at: datetime | None = None,
    ) -> str:
        now = now or datetime.now(UTC)
        expires_at = expires_at or datetime.now(UTC) + cls.token_type.lifetime

        return encode(
            payload={
                "data": data,
                "exp": expires_at,
                "iat": now,
                "jti": jti or str(uuid4().hex),
                "sub": sub,
                "type": cls.token_type,
            },
            key=APP_SETTINGS.SECRET_KEY,
            algorithm=APP_SETTINGS.ALGORITHM,
        )

    @classmethod
    async def decode(cls, token: str) -> DecodedType:
        # Actual decoding
        try:
            claims: dict = decode(
                token, key=APP_SETTINGS.SECRET_KEY, algorithms=[APP_SETTINGS.ALGORITHM]
            )
        except InvalidSignatureError as e:
            logger.error(f"Error with token: {e}")
            raise InvalidTokenError("The token's signature invalid")
        except ExpiredSignatureError as e:
            logger.error(f"Error with token: {e}")
            raise InvalidTokenError("The token's signature has expired")
        except PyJWTError as e:
            logger.error(f"Error with token: {e}")
            raise InvalidTokenError

        # Validating the token type
        if claims.get("type") != cls.token_type.value:
            logger.error(f"Invalid token type: {claims.get('type')}. User passed an incorrect token type")
            raise InvalidTokenError("Incorrect token type passed to the endpoint")

        return claims


#noinspection PyMethodOverriding
class RevocableToken[DecodedType](BaseToken[DecodedType]):
    @classmethod
    async def _create_token_in_db(cls, conn: AsyncSession, user_id: str) -> Token:
        new_token = Token(user_id=user_id)
        conn.add(new_token)
        await conn.flush()
        await conn.refresh(new_token)

        logger.debug("Token created in database")

        return new_token

    @classmethod
    async def _delete_all_user_tokens_in_db(cls, conn: AsyncSession, user_id: str):
        stmt: Delete = delete(Token).where(Token.user_id == user_id)
        await conn.execute(stmt)
        await conn.flush()

    @classmethod
    async def _revoke(cls, conn: AsyncSession, jti: UUID) -> None:
        stmt = delete(Token).where(Token.jti == jti)
        await conn.execute(stmt)
        await conn.flush()

        logger.debug(f"Token revoked: {jti}")

    @classmethod
    async def _ensure_token_in_db(cls, conn: AsyncSession, jti: UUID) -> None:
        token_exists = await conn.scalar(exists(Token).where(Token.jti == jti).select())
        if not token_exists:
            raise InvalidTokenError

    @classmethod
    async def new(
        cls,
        conn: AsyncSession,
        sub: str,
        data: dict | None = None,
        jti: str | None = None,
    ) -> str:
        now = datetime.now(UTC)
        expires_at = now + cls.token_type.lifetime
        await cls._delete_all_user_tokens_in_db(user_id=sub, conn=conn)
        token_in_db = await cls._create_token_in_db(conn=conn, user_id=sub)
        return await super().new(
            sub=sub, data=data, jti=str(token_in_db.jti), now=now, expires_at=expires_at
        )

    @classmethod
    async def decode(cls, conn: AsyncSession, token: str) -> dict:
        claims = await super().decode(token=token)
        # Ensuring the token is in the database
        if jti := claims.get("jti"):
            if isinstance(jti, str):
                jti = UUID(
                    jti
                )  # make sure the jti is a UUID type (as is in the database) before using it for operations
            await cls._ensure_token_in_db(conn=conn, jti=jti)
            await cls._revoke(conn=conn, jti=jti)
        else:
            raise InvalidTokenError("The provided token does not contain a JTI value")
        return claims


class AccessToken(BaseToken[UserOutputModel]):
    token_type = TokenType.ACCESS

    # noinspection PyMethodOverriding
    @classmethod
    async def new(cls, user: UserOutputModel) -> str:
        user_id = user.user_id
        return await super().new(sub=user_id, data=user.model_dump())

    @classmethod
    async def decode(cls, token: str) -> UserOutputModel:
        claims = await super().decode(token)
        data = claims["data"]
        data["user_id"] = claims["sub"]

        return UserOutputModel.model_validate(data)


class RefreshToken[str](RevocableToken[str]):
    """
    Refresh token factory class.

    Decoding returns the user_id
    """

    token_type = TokenType.REFRESH

    # noinspection PyMethodOverriding
    @classmethod
    async def new(cls, conn: AsyncSession, user_id: str) -> str:
        return await super().new(conn=conn, sub=user_id)

    @classmethod
    async def decode(cls, conn: AsyncSession, token: str) -> str:
        claims = await super().decode(conn=conn, token=token)
        user_id = claims["sub"]
        return user_id


class PasswordResetToken(RevocableToken):
    token_type = TokenType.PASSWORD_RESET

    # noinspection PyMethodOverriding
    @classmethod
    async def new(cls, user_id: str, conn: AsyncSession) -> str:
        return await super().new(sub=user_id, conn=conn)

    @classmethod
    async def decode(cls, token: str, conn: AsyncSession) -> str:
        claims = await super().decode(token=token, conn=conn)
        user_id = claims["sub"]
        return user_id

class AccountVerificationToken(BaseToken[UserOutputModel]):
    token_type = TokenType.ACCOUNT_VERIFICATION

    @classmethod
    async def _store_token_in_db(cls, conn: AsyncSession, user_id: str, jti: str):
        new_token = Token(user_id=user_id, jti=jti)
        conn.add(new_token)
        await conn.flush()
        await conn.refresh(new_token)
        return new_token

    @classmethod
    async def _check_token_in_db(cls, conn: AsyncSession, jti: str):
        stmt = select(Token).where(Token.jti == jti)
        result = await conn.execute(stmt)
        return result.scalar_one_or_none()

    # noinspection PyMethodOverriding
    @classmethod
    async def new(cls, user_id: str, user_email: str, conn: AsyncSession) -> str:
        user_id = user_id
        return await super().new(sub=user_id, data={"email": user_email})

    @classmethod
    async def decode(cls, token: str, conn: AsyncSession|None = None) -> dict:
        claims = await super().decode(token)

        token_exists: Token|None = await cls._check_token_in_db(conn=conn, jti=claims["jti"])
        if token_exists:
            raise InvalidTokenError("The provided account verification token already exists in the database")

        data: dict = claims["data"] # Unpacking
        data["user_id"] = claims["sub"]

        # Store token in the database after usage to prevent re-use
        await cls._store_token_in_db(
            conn=conn,
            user_id=claims["sub"],
            jti=claims["jti"]
        )

        return data

class SignupSessionToken(BaseToken[dict]):
    token_type = TokenType.SIGNUP_SESSION

    @classmethod
    async def new(cls, user_id: str, email: str) -> str:
        return await super().new(
            sub=user_id,
            data={
                "email": email,
                "purpose": "signup"   # guards against token misuse
            }
        )

    @classmethod
    async def decode(cls, token: str) -> dict:
        claims = await super().decode(token)
        if claims.get("data", {}).get("purpose") != "signup":
            raise InvalidTokenError("Invalid token purpose")

        return {
            "user_id": claims["sub"],
            "email": claims["data"]["email"]
        }
