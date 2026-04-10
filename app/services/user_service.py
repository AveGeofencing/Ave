from typing import Annotated, Optional, Dict, Any
from fastapi import BackgroundTasks, HTTPException, Depends
from pydantic import with_config
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import Response

from ..common import hash_password, generate_id, is_password_correct, set_custom_cookie
from ..database import get_db_session
from ..email.types import WelcomeUserEmail, PasswordResetConfirmation
from ..email.types.no_reply import UserVerificationEmail, PasswordResetEmail
from ..exceptions import InvalidTokenError
from ..infra.token_utils import AccountVerificationToken, PasswordResetToken, AccessToken, RefreshToken
from ..models import User
from ..email import send_email_task
from ..repositories import UserRepository, UsedPasswordResetTokenRepo
from ..schemas import UserCreateModel, UserOutputModel
from ..utils import (
    PASSWORD_MIN_LENGTH, logger,
)
from ..settings import APP_SETTINGS

settings = APP_SETTINGS


class UserService:
    def __init__(
            self,
            user_repository: Annotated[UserRepository, Depends()],
            used_reset_token_repo: Annotated[UsedPasswordResetTokenRepo, Depends()],
            conn: Annotated[AsyncSession, Depends(get_db_session)],
            bg_tasks: BackgroundTasks,
    ):
        self.conn = conn  # Database connection

        self.used_reset_token_repo = used_reset_token_repo
        self.bg_tasks = bg_tasks
        self.user_repository: UserRepository = user_repository

    async def register_user(self, email: str):
        """
        Generates a one-time use link for verifying user email
        Args:
            email: str

        Returns:
        """
        async with self.conn.begin():
            existing_user: User = await self.user_repository.get_user_by_email_or_matric(conn=self.conn, email=email)
            if existing_user:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail="Ave already knows this email. Wanna try logging in instead?")

            user_id: str = generate_id()
            registration_token = await AccountVerificationToken.new(
                conn=self.conn,
                user_id=user_id,
                user_email=email,
            )

            verification_link = f"{settings.BASE_URL}/verify?token={registration_token}"
            self.bg_tasks.add_task(
                send_email_task,
                email_context=UserVerificationEmail(
                    context_vars={"verification_link": verification_link}
                ),
                recipients=[email],
            )

            return {"message": "Verification link send to your email address."}

    async def verify_token(self, verification_token: str):
        async with self.conn.begin():
            try:
                unverified_user_data: dict = await AccountVerificationToken.decode(verification_token, conn=self.conn)
            except InvalidTokenError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Link expired.")

            return {"user_email": unverified_user_data.get("email"), "user_id": unverified_user_data.get("user_id")}

    async def create_new_user(self, user: UserCreateModel) -> dict:
        """Create a new user account, create verification code, send verification code"""
        async with self.conn.begin():
            # Validate password
            if len(user.password) < PASSWORD_MIN_LENGTH:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
                )

            #Hash password
            user.password = hash_password(user.password)
            created_user: User = await self.user_repository.create_new_user(
                user, conn=self.conn
            )

            dashboard_link: str = f"{settings.BASE_URL}/dashboard"
            self.bg_tasks.add_task(
                send_email_task,
                email_context=WelcomeUserEmail(
                    context_vars={"dashboard_link": dashboard_link}
                ),
                recipients=[created_user.email]
            )
            return {"message": "User created successfully"}

    async def get_user_by_email_or_matric(
            self, email: str = None, matric: str = None
    ) -> Dict[str, Any]:
        """Retrieve user information by email or matric number"""
        if not email and not matric:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or matric number must be provided"
            )

        user = await self.user_repository.get_user_by_email_or_matric(conn=self.conn, email=email, matric=matric)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {email} or matric {matric} not found"
            )

        return {
            "user_username": user.username,
            "user_matric": user.user_matric,
            "user_email": user.email,
            "user_role": user.role,
            "user_attendances": user.attendances,
        }

    async def get_user_records(
            self, user_matric: str, course_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieve user attendance records, optionally filtered by course"""
        user: User = await self.user_repository.get_user_by_email_or_matric(matric=user_matric, conn=self.conn)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with matric {user_matric} not found"
            )

        if course_title is None:
            return {"attendance": user.attendances}

        filtered_attendances = [
            attendance
            for attendance in user.attendances
            if attendance.course_title == course_title
        ]
        return {"attendance": filtered_attendances}

    async def send_reset_password_email(
            self, user_email: str
    ) -> Dict[str, str]:
        async with self.conn.begin() as conn:
            """Send password reset email to user"""
            user: User = await self.user_repository.get_user_by_email_or_matric(email=user_email, conn=self.conn)
            if user is None:
                # Return success even if user doesn't exist for security reasons
                return {
                    "message": "If a user with this email exists, a reset link has been sent"
                }

            # Generate token and reset link
            token = await PasswordResetToken.new(user_id=user.id, conn=self.conn)

            reset_link = f"{settings.BASE_URL}/user/reset_password?token={token}"

            # Send email as a background task
            self.bg_tasks.add_task(
                send_email_task,
                recipients=[user.email],
                email_context=PasswordResetEmail(context_vars={"reset_link": reset_link, "link_expiry_time": 10}),
            )

            return {
                "message": "If a user with this email exists, a reset link has been sent"
            }

    async def change_password(
            self, new_password: str, token: str,
    ) -> Dict[str, str]:
        """Change user password using reset token"""
        async with self.conn.begin():
            #Check database for existence of reset token
            token_is_used = await self.used_reset_token_repo.get_used_token(token_value=token, conn=self.conn)
            if token_is_used:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expired link.")

            user_id: str = await PasswordResetToken.decode(token, conn=self.conn)
            # Add reset token to database
            await self.used_reset_token_repo.add_reset_token(token_value=token, conn=self.conn)

            if not new_password or len(new_password) < PASSWORD_MIN_LENGTH:
                raise HTTPException(
                    status_code=400,
                    detail=f"Password must be at least {PASSWORD_MIN_LENGTH} characters",
                )

            # Hash and update password
            new_hashed_password = hash_password(new_password)
            user_email = await self.user_repository.change_user_password(
                user_id=user_id, new_hashed_password=new_hashed_password, conn=self.conn
            )

            self.bg_tasks.add_task(
                send_email_task,
                recipients=[user_email],
                email_context=PasswordResetConfirmation(
                    context_vars={"username": user_email}
                )
            )

            return {"message": "Password changed successfully"}

    async def login(self, email: str, user_matric: str, password: str, response: Response):
        """Handles the login process for a user.

        It checks if the user exists in the database and verifies the password.

        When all checks are successful, it creates a new session for the user, stores it in the redis database,
        and returns the session token.
        """
        async with self.conn.begin():
            existing_user: User = await self.user_repository.get_user_by_email_or_matric(
                email=email, matric=user_matric, conn=self.conn
            )
            if not existing_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found. Please sign up"
                )
            if not is_password_correct(existing_user.hashed_password, password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password"
                )

            user_to_login: UserOutputModel = UserOutputModel(
                user_id=existing_user.id,
                username=existing_user.username,
                email=existing_user.email,
                user_matric=existing_user.user_matric,
                role=existing_user.role,
            )

            access_token: str = await AccessToken.new(user_to_login)
            new_refresh_token: str = await RefreshToken.new(
                user_id=user_to_login.user_id,
                conn=self.conn,
            )

            set_custom_cookie(
                response=response,
                key="refresh_token",
                value=new_refresh_token,
                path="/auth",
                max_age=60 * 60 * 24 * 7,
            )  # Set the refresh token in a cookie

            return {
                "access_token": access_token,
                "token_type": "Bearer",
                "username": existing_user.username,
                "role": existing_user.role,
            }

    async def logout(self, request: Request, response: Response):
        async with self.conn.begin():
            refresh_token: str = request.cookies.get("refresh_token")
            if not refresh_token:
                logger.debug("No refresh token was found in the user's client.")
                return {"message": "Logged out successfully."}

            try:
                # Delete the refresh token from the database by decoding it
                await RefreshToken.decode(conn=self.conn, token=refresh_token)
                # Delete the refresh token from the client
            except InvalidTokenError:
                logger.debug("Token wasn't deleted")
                pass

            response.delete_cookie("refresh_token")

            return {"message": "Logged out successfully."}
