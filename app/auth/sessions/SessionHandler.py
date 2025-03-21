import json
import uuid
from zoneinfo import ZoneInfo
import logging

from fastapi import HTTPException
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from ...repositories import SessionRepository, UserRepository
from passlib.context import CryptContext
from ...utils.config import settings
from ...redis import RedisClient

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
WANT_SINGLE_SIGNIN_FLAG = settings.WANT_SINGLE_SIGNIN

logger = logging.getLogger("uvicorn")


class SessionHandler:
    def __init__(self, db_session: AsyncSession = None):
        self.SESSION_TIMEOUT_MINUTES = 24 * 60
        self.sessionRepository = SessionRepository(db_session=db_session)

        # redis
        self.redis_client = RedisClient.get_instance()

    async def get_user_by_session(self, session_token: str):
        session = json.loads(await self.redis_client.get(session_token))
        if session:
            return {
                "user_matric": session["user_matric"],
                "email": session["email"],
                "username": session["username"],
                "role": session["role"],
            }

        return None

    async def get_user_session_by_matric(self, user_matric: str):
        existing_user_session = await self.redis_client.get(f"user:{user_matric}")
        return existing_user_session

    async def create_new_session(self, user_matric: str, email: str, role: str):
        existing_user_session = await self.redis_client.get(f"user:{user_matric}")
        if existing_user_session:
            if WANT_SINGLE_SIGNIN_FLAG:
                raise HTTPException(
                    status_code=400,
                    detail=f"Already logged in. Sign out of other devices before logging in again",
                )

            return existing_user_session

        # generate new user session
        session_token = str(uuid.uuid4())

        user_data = {
            "user_matric": user_matric,
            "email": email,
            "username": user_matric,
            "role": role,
        }

        # Setting the session in redis
        await self.redis_client.set(
            f"{session_token}",  # Token as the key
            json.dumps(user_data),  # Json object containing user_data
            ex=timedelta(days=1),
        )

        # Reverse mapping to quickly find user session by matric
        await self.redis_client.set(
            f"user:{user_matric}", session_token, ex=timedelta(days=1)
        )

        return session_token

    async def deactivate_session(self, session_token):
        session_state = json.loads(await self.redis_client.get(session_token))
        print(session_state)

        if session_state is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            await self.redis_client.delete(session_token)
            await self.redis_client.delete(f"user:{session_state["user_matric"]}")
            return "Logged out successfully"
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail=f"Failed to deactivate session")

    async def login(self, user_matric: str, password: str, email: str = None):
        existing_user = await self.sessionRepository.get_user_by_email_or_matric(
            email=email, matric=user_matric
        )
        if not existing_user:
            raise HTTPException(
                status_code=400, detail="User not found. Please sign up"
            )
        if not bcrypt_context.verify(password, existing_user.hashed_password):
            raise HTTPException(
                status_code=400, detail="Incorrect username or password"
            )

        session_token = await self.create_new_session(
            user_matric=existing_user.user_matric,
            email=existing_user.email,
            role=existing_user.role,
        )

        return {
            "message": "Successfully logged in",
            "session_token": session_token,
            "username": existing_user.username,
            "role": existing_user.role,
        }
