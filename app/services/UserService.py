import logging
import random
from typing import Optional, Dict, Any, Union
from zoneinfo import ZoneInfo
from datetime import timedelta, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks, HTTPException
from passlib.context import CryptContext
from pydantic import EmailStr
from jose import JWTError, jwt

from ..redis import RedisClient
from .EmailService import send_email
from ..exceptions import *
from ..repositories import (
    PasswordResetTokenRepository,
    SessionRepository,
    UserRepository,
)
from ..schemas import UserCreateModel
from ..utils.config import settings
from ..utils.constants import (
    PASSWORD_RESET_TOKEN_EXPIRY_MINUTES,
    EMAIL_SUBJECTS,
    PASSWORD_MIN_LENGTH,
)

# Create a password context for hashing
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger("uvicorn")


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: Optional[UserRepository] = None,
        password_reset_token_repository: Optional[PasswordResetTokenRepository] = None,
        session_repository: Optional[SessionRepository] = None,
    ):
        self.session = session
        self.user_repository = user_repository or UserRepository(session)
        self.password_reset_token_repository = (
            password_reset_token_repository or PasswordResetTokenRepository(session)
        )
        self.session_repository = session_repository or SessionRepository(session)
        self.redis_client = RedisClient.get_instance()

    async def create_new_user(self, user_data: UserCreateModel) -> Dict[str, str]:
        """Create a new user account"""
        try:
            existing_user = await self.user_repository.get_user_by_email_or_matric(
                email=user_data.email, matric=user_data.user_matric
            )

            if existing_user:
                raise UserAlreadyExistsError(
                    "User with this email or matric number already exists"
                )

            # Validate password
            if len(user_data.password) < PASSWORD_MIN_LENGTH:
                raise ValueError(
                    f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
                )

            # Validate verification code
            cached_code = await self.redis_client.get(user_data.email)

            if int(cached_code) != int(user_data.verification_code):
                raise VerificationCodeError("Invalid verification code")

            hashed_password = bcrypt_context.hash(user_data.password)

            return await self.user_repository.create_new_user(
                user_data, hashed_password
            )

        except UserAlreadyExistsError as e:
            logger.warning(
                f"Attempt to create duplicate user: {user_data.email}/{user_data.user_matric}"
            )
            raise HTTPException(status_code=409, detail=str(e))
        except VerificationCodeError as e:
            logger.error(f"Invalid verification code: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except ValueError as e:
            logger.error(f"Invalid user data: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error creating new user: {user_data.email}", exc_info=True)
            raise HTTPException(
                status_code=500, detail="Something went wrong, contact admin."
            )

    async def create_and_send_registration_code(
        self, email: str, matric: str, backgroundTask: BackgroundTasks
    ):
        try:
            # Check if code exist in database againsts user email and it has not expired
            existing_user = await self.user_repository.get_user_by_email_or_matric(
                email=email, matric=matric
            )

            if existing_user:
                raise UserAlreadyExistsError(
                    "User with this email or matric number already exists"
                )

            # Generate 6 digit random number
            code = random.randint(100000, 999999)

            # SO if the user already has a code, delete it and set a new one
            if await self.redis_client.exists(email):
                await self.redis_client.delete(email)

            # Store code in redis with email as key
            await self.redis_client.set(email, code, ex=300)

            body = await self._get_user_registration_email_template(email, code)

            # Send code to user email
            backgroundTask.add_task(
                send_email,
                subject=EMAIL_SUBJECTS["VERIFY"],
                recipients=[email],
                body=body,
            )

            return None
        except UserAlreadyExistsError as e:
            logger.warning(f"Attempt to create duplicate user: {email}/{matric}")
            raise HTTPException(status_code=409, detail=str(e))
        except Exception as e:
            logger.error(
                f"Error creating and sending registration code to {email}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail="Something went wrong, contact admin."
            )

    async def get_user_by_email_or_matric(
        self, email: str = None, matric: str = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve user information by email or matric number"""
        if not email and not matric:
            raise HTTPException(
                status_code=400, detail="Email or matric number must be provided"
            )

        try:
            user = await self.user_repository.get_user_by_email_or_matric(email, matric)
            if user is None:
                return None

            return {
                "user_username": user.username,
                "user_matric": user.user_matric,
                "user_email": user.email,
                "user_role": user.role,
                "user_attendances": user.attendances,
            }

        except Exception as e:
            logger.error(
                f"Error fetching user by email/matric: {email} or {matric}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail="Something went wrong, contact admin."
            )

    async def get_user_records(
        self, user_matric: str, course_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieve user attendance records, optionally filtered by course"""
        try:
            user = await self.user_repository.get_user_by_email_or_matric(
                matric=user_matric
            )

            if not user:
                raise UserNotFoundError(f"User with matric {user_matric} not found")

            if not user.attendances:
                return {"attendance": []}

            if course_title is None:
                return {"attendance": user.attendances}

            filtered_attendances = [
                attendance
                for attendance in user.attendances
                if attendance.course_title == course_title
            ]
            return {"attendance": filtered_attendances}

        except UserNotFoundError as e:
            logger.warning(str(e))
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(
                f"Error fetching records for user {user_matric}", exc_info=True
            )
            raise HTTPException(
                status_code=500, detail="Something went wrong, contact admin."
            )

    async def _generate_password_reset_token(
        self,
        email: EmailStr,
        username: str,
        user_matric: str,
        expires_delta: timedelta = timedelta(
            minutes=PASSWORD_RESET_TOKEN_EXPIRY_MINUTES
        ),
    ) -> str:
        """Generate a JWT token for password reset"""
        try:
            # Invalidate any existing tokens
            existing_token = (
                await self.password_reset_token_repository.get_token_by_matric(
                    user_matric
                )
            )
            if existing_token:
                await self.password_reset_token_repository.set_token_is_used(
                    user_matric=user_matric
                )

            # Prepare token data
            expires = datetime.now(tz=ZoneInfo("UTC")) + expires_delta
            token_data = {
                "sub": email,
                "username": username,
                "user_matric": user_matric,
                "exp": expires,
            }

            # Create JWT token
            token = jwt.encode(
                token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM
            )

            # Store token in database
            await self.password_reset_token_repository.add_token(
                user_id=user_matric, token=token, expires_at=expires
            )

            return token

        except Exception as e:
            logger.error(
                f"Error generating password reset token for {email}", exc_info=True
            )
            raise TokenError(f"Failed to generate reset token: {str(e)}")

    async def _decode_password_reset_token(self, token: str) -> Dict[str, str]:
        """Validate and decode a password reset token"""
        try:
            # Verify token exists and is valid
            existing_token = await self.password_reset_token_repository.get_token(token)

            if not existing_token:
                raise TokenError("Token not found")

            if existing_token.is_used:
                raise TokenError("Token has already been used")

            # Decode JWT
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )

            # Extract token data
            email = payload.get("sub")
            username = payload.get("username")
            user_matric = payload.get("user_matric")

            if not all([email, username, user_matric]):
                raise TokenError("Invalid token data")

            # Mark token as used
            await self.password_reset_token_repository.set_token_is_used(token)

            return {
                "email": email,
                "username": username,
                "user_matric": user_matric,
            }

        except JWTError:
            # If JWT is invalid, deactivate the token
            await self.password_reset_token_repository.deactivate_token(token)
            raise TokenError("Invalid or expired token")
        except TokenError as e:
            logger.error(f"Error decoding token({str(e)})")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid link. Please request a new password reset link.",
            )
        except Exception as e:
            logger.error(f"Error decoding token: {token[:10]}...", exc_info=True)
            raise HTTPException(status_code=500, detail="Something went wrong")

    async def _get_password_reset_email_template(
        self, username: str, reset_link: str
    ) -> str:
        """Generate HTML template for password reset email"""
        return f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f4;
                        padding: 20px;
                        text-align: center;
                    }}
                    .container {{
                        max-width: 500px;
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                        margin: auto;
                    }}
                    .header {{
                        font-size: 24px;
                        font-weight: bold;
                        color: #333;
                        margin-bottom: 10px;
                    }}
                    .button {{
                        background: #007bff;
                        color: white;
                        padding: 12px 20px;
                        font-size: 16px;
                        text-decoration: none;
                        border-radius: 5px;
                        display: inline-block;
                        margin: 15px 0;
                    }}
                    .footer {{
                        font-size: 12px;
                        color: #666;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">Password Reset Request</div>
                    <p>Hi <strong>{username}</strong>,</p>
                    <p>We received a request to reset your password. Click the button below to reset it:</p>
                    <a class="button" style="color: white" href="{reset_link}">Reset Password</a>
                    <p>This link will expire in <strong>{PASSWORD_RESET_TOKEN_EXPIRY_MINUTES} minutes</strong>.</p>
                    <p>If you didn’t request this, you can safely ignore this email.</p>
                    <hr>
                    <div class="footer">
                        Best Regards, <br>
                        <strong>Ave Geofencing</strong>
                    </div>
                </div>
            </body>
        </html>
        """

    async def _get_password_changed_email_template(self, username: str) -> str:
        """Generate HTML template for password changed confirmation email"""
        return f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f4;
                        padding: 20px;
                        text-align: center;
                    }}
                    .container {{
                        max-width: 500px;
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                        margin: auto;
                    }}
                    .header {{
                        font-size: 24px;
                        font-weight: bold;
                        color: #333;
                        margin-bottom: 10px;
                    }}
                    .alert {{
                        color: #d9534f;
                        font-weight: bold;
                    }}
                    .footer {{
                        font-size: 12px;
                        color: #666;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">Your Password Has Been Changed</div>
                    <p>Hi <strong>{username}</strong>,</p>
                    <p>Your password was successfully changed.</p>
                    <p class="alert">If you did not change your password and believe your account has been compromised, please contact support immediately.</p>
                    <hr>
                    <div class="footer">
                        Best Regards, <br>
                        <strong>Ave Geofencing</strong>
                    </div>
                </div>
            </body>
        </html>
        """

    async def _get_user_registration_email_template(self, email: str, code: int):
        return f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f4;
                        padding: 20px;
                        text-align: center;
                    }}
                    .container {{
                        max-width: 500px;
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                        margin: auto;
                    }}
                    .header {{
                        font-size: 24px;
                        font-weight: bold;
                        color: #333;
                        margin-bottom: 10px;
                    }}
                    .code {{
                        font-size: 28px;
                        font-weight: bold;
                        color: #007bff;
                        background: #e7f1ff;
                        padding: 10px 15px;
                        display: inline-block;
                        border-radius: 5px;
                        margin: 10px 0;
                    }}
                    .footer {{
                        font-size: 12px;
                        color: #666;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">Welcome to Ave Geofencing!</div>
                    <p>Dear User,</p>
                    <p>Your registration code is:</p>
                    <div class="code">{code}</div>
                    <p>This code is valid for <strong>5 minutes</strong>. Please do not share it with anyone.</p>
                    <p>If you did not request this code, please ignore this email.</p>
                    <hr>
                    <div class="footer">
                        Best Regards, <br>
                        <strong>Ave Geofencing</strong>
                    </div>
                </div>
            </body>
        </html>
        """

    async def send_reset_password_email(
        self, user_email: str, background_tasks: BackgroundTasks
    ) -> Dict[str, str]:
        """Send password reset email to user"""
        try:
            user = await self.get_user_by_email_or_matric(email=user_email)
            if user is None:
                # Return success even if user doesn't exist for security reasons
                return {
                    "message": "If a user with this email exists, a reset link has been sent"
                }

            # Generate token and reset link
            token = await self._generate_password_reset_token(
                email=user["user_email"],
                username=user["user_username"],
                user_matric=user["user_matric"],
            )

            reset_link = f"{settings.BASE_URL}user/student/reset_password?token={token}"

            # Generate email body
            body = await self._get_password_reset_email_template(
                username=user["user_username"], reset_link=reset_link
            )

            # Send email as background task
            background_tasks.add_task(
                send_email,
                subject=EMAIL_SUBJECTS["PASSWORD_RESET"],
                recipients=[user["user_email"]],
                body=body,
            )

            return {
                "message": "If a user with this email exists, a reset link has been sent"
            }

        except TokenError as e:
            logger.error(f"Token generation error for {user_email}: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to generate reset token"
            )
        except Exception as e:
            logger.error(
                f"Error sending password reset email to {user_email}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail="Something went wrong, contact admin"
            )

    async def change_password(
        self, new_password: str, token: str, background_tasks: BackgroundTasks
    ) -> Dict[str, str]:
        """Change user password using reset token"""
        if not new_password or len(new_password) < PASSWORD_MIN_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Password must be at least {PASSWORD_MIN_LENGTH} characters",
            )

        try:
            # Verify and decode token
            user = await self._decode_password_reset_token(token)

            # Hash and update password
            new_hashed_password = bcrypt_context.hash(new_password)
            change_password_message = await self.user_repository.change_user_password(
                user_email=user["email"], new_hashed_password=new_hashed_password
            )

            # Deactivate all user sessions for security
            await self.redis_client.delete(f"user:{user['user_matric']}")

            # Send confirmation email
            body = await self._get_password_changed_email_template(
                username=user["username"]
            )

            background_tasks.add_task(
                send_email,
                subject=EMAIL_SUBJECTS["PASSWORD_CHANGED"],
                recipients=[user["email"]],
                body=body,
            )

            return change_password_message

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error changing password with token {token[:10]}...", exc_info=True
            )
            raise HTTPException(status_code=500, detail="Something went wrong")
