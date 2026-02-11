from typing import Annotated, Optional, Dict, Any
from fastapi import BackgroundTasks, HTTPException, Depends
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession

from ..common import hash_password
from ..database import get_db_session
from ..email.types import WelcomeUserEmail, PasswordResetConfirmation
from ..email.types.no_reply import UserVerificationEmail, PasswordResetEmail
from ..exceptions import InvalidTokenError
from ..infra.token_utils import AccountVerificationToken, PasswordResetToken
from ..models import User
from ..email import send_email_task
from ..repositories import UserRepository, UsedPasswordResetTokenRepo
from ..schemas import UserCreateModel, UserOutputModel
from ..utils import (
    PASSWORD_MIN_LENGTH,
    logger
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
        self.conn = conn # Database connection

        self.used_reset_token_repo = used_reset_token_repo
        self.bg_tasks = bg_tasks
        self.user_repository: UserRepository = user_repository


    async def create_and_send_verification_link(self, user: User):
        """
        Create and send an email with a jwt containing essential user information to the user's email.
        The jwt will expire in 1 hour.

        The email will contain a link that forwards the user to the frontend page that passes the user's jwt to the backend.
        Args:
            user:

        Returns:

        """
        # Send code to user email
        user_output_model: UserOutputModel = UserOutputModel(
            user_id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            user_matric=user.user_matric
        )

        account_verification_token = await AccountVerificationToken.new(user_output_model)

        # Background task to send verification email
        self.bg_tasks.add_task(
            send_email_task,
            email_context=UserVerificationEmail(
                context_vars={
                    "verification_link": f"{settings.BASE_URL}verify?token={account_verification_token}",
                    "username": user.username,
                    "token_expiry_minutes": 15
                }
            ),
            recipients=[user.email],
        )

        return {"message": f"Verification email sent to {user.email} successfully."}

    async def create_new_user(self, user_data: UserCreateModel) -> dict:
        """Create a new user account, create verification code, send verification code"""
        async with self.conn.begin():
            existing_user = await self.user_repository.get_user_by_email_or_matric(
                email=user_data.email, matric=user_data.user_matric, conn=self.conn
            )

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email or matric number already exists"
                )

            # Validate password
            if len(user_data.password) < PASSWORD_MIN_LENGTH:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
                )

            hashed_password = hash_password(user_data.password)

            created_user: User = await self.user_repository.create_new_user(
                user_data, hashed_password, conn=self.conn
            )
            await self.create_and_send_verification_link(user=created_user)
            logger.info(f"Verification code sent to user email: {created_user.email}")

            return {"message": "User created successfully"}

    async def verify_user(
        self, token: str
    ):
        try:
            # Decode token
            user: UserOutputModel = await AccountVerificationToken.decode(token)
        except InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        async with self.conn.begin():
            # if code exists, verify user
            updated: bool = await self.user_repository.verify_user(user_id=user.user_id, conn=self.conn)

            if not updated:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already verified")

        # Send code to user email
        self.bg_tasks.add_task(
            send_email_task,
            recipients=[user.email],
            email_context=WelcomeUserEmail(
                context_vars={"username": user.username, "dashboard_link": f"{settings.BASE_URL}dashboard"}
            )
        )

        return {"message": "User verified successfully"}

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
        """Send password reset email to user"""
        user: User = await self.user_repository.get_user_by_email_or_matric(email=user_email, conn=self.conn)
        if user is None:
            # Return success even if user doesn't exist for security reasons
            return {
                "message": "If a user with this email exists, a reset link has been sent"
            }

        # Generate token and reset link
        token = await PasswordResetToken.new(user_id=user.id)

        reset_link = f"{settings.BASE_URL}user/reset_password?token={token}"

        # Send email as background task
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

            user_id: str = await PasswordResetToken.decode(token)
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
