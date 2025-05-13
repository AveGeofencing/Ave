from datetime import timedelta
import logging
import json
from typing import Annotated
import uuid

from fastapi import HTTPException, Depends
from passlib.context import CryptContext
from redis.asyncio import Redis

from ...models import User
from ...redis import get_redis_client
from ...repositories import SessionRepository, get_session_repository
from ...utils.config import get_app_settings

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dependencies
SessionRepositoryDependency = Annotated[
    SessionRepository, Depends(get_session_repository)
]
RedisClientDependency = Annotated[Redis, Depends(get_redis_client)]
logger = logging.getLogger("uvicorn")
settings = get_app_settings()


class SessionHandler:
    def __init__(self, sessionRepository: SessionRepository, redis_client: Redis):
        # redis
        self.redis_client = redis_client
        self.sessionRepository = sessionRepository

    async def get_user_by_session(self, session_token: str) -> dict[str, str] | None:
        """Retrieves the user information from the session token stored in the redis database."""
        session = json.loads(await self.redis_client.get(session_token))
        if session:
            return {
                "user_matric": session["user_matric"],
                "email": session["email"],
                "username": session["username"],
                "role": session["role"],
            }

        return None

    async def get_user_session_by_matric(self, user_matric: str) -> str:
        """Used to get user session details by their matric.

        Made possible with the reverse mapping using the user matric as the key.
        """
        existing_user_session = await self.redis_client.get(f"user:{user_matric}")
        return existing_user_session

    async def create_new_session(self, user_matric: str, email: str, role: str) -> str:
        """Creates a new session for the user and stores it in the redis database."""
        existing_user_session: str = await self.redis_client.get(f"user:{user_matric}")

        # If the user is already logged in, just return the session token of the existing session.
        if existing_user_session:
            # if settings.WANT_SINGLE_SIGNIN: #Flag to enable/disable single sign in
            #     raise HTTPException(
            #         status_code=400,
            #         detail=f"Already logged in. Sign out of other devices before logging in again",
            #     )
            return existing_user_session

        # generate new user session
        session_token: str = str(uuid.uuid4())
        user_data: dict = {
            "user_matric": user_matric,
            "email": email,
            "username": user_matric,
            "role": role,
        }

        # Setting the session in redis
        await self.redis_client.set(
            f"{session_token}",  # session token as the key
            json.dumps(user_data),  # Json object containing user_data as the value
            ex=timedelta(days=1),  # Expiry time as 24 hours(1 day)
        )

        # Reverse mapping to quickly find user session_token by their matric
        await self.redis_client.set(
            f"user:{user_matric}", session_token, ex=timedelta(days=1)
        )

        return session_token

    # Method for logging out a user
    async def deactivate_session(self, session_token: str) -> str:
        """Deactivatves a session by deleting it from the redis database"""
        session_state = json.loads(await self.redis_client.get(session_token))
        print(session_state)

        if session_state is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            await self.redis_client.delete(session_token)
            await self.redis_client.delete(f"user:{session_state['user_matric']}")
            return "Logged out successfully"
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail=f"Failed to deactivate session")

    # Method for logging in a user
    async def login(
        self, 
        user_matric: str, 
        password: str, 
        email: str = None
    ) -> dict[str, ...]:
        """Handles the login process for a user.

        It checks if the user exists in the database and verifies the password.

        When all checks are successful, it creates a new session for the user, stores it in the redis database,
        and returns the session token.
        """
        existing_user: User = await self.sessionRepository.get_user_by_email_or_matric(
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

        session_token: str = await self.create_new_session(
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


def get_session_handler(
    session_repository: SessionRepositoryDependency, redis_client: RedisClientDependency
) -> SessionHandler:

    return SessionHandler(
        sessionRepository=session_repository, redis_client=redis_client
    )
