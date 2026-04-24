from http.client import responses
from typing import Annotated, Optional, Dict, Any, Sequence, List

import boto3
import magic
from sqlalchemy.exc import IntegrityError
from fastapi import BackgroundTasks, HTTPException, Depends, UploadFile
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import Response

from ..common import hash_password, generate_id, is_password_correct, set_custom_cookie
from ..database import get_db_session
from ..email.types import WelcomeUserEmail, PasswordResetConfirmation
from ..email.types.no_reply import UserVerificationEmail, PasswordResetEmail
from ..exceptions import InvalidTokenError
from ..infra.token_utils import AccountVerificationToken, PasswordResetToken, AccessToken, RefreshToken, \
    SignupSessionToken
from ..models import User, College
from ..email import send_email_task
from ..repositories import UserRepository, UsedPasswordResetTokenRepo
from ..schemas import UserCreateModel, UserOutputModel
from ..schemas.college import CollegeSchema
from ..schemas.rekognition import DetectFacesResponse, CompareFacesResponse
from ..utils import (
    PASSWORD_MIN_LENGTH, logger,
)
from ..settings import APP_SETTINGS

settings = APP_SETTINGS

SECONDS_IN_1_MINUTE = 60

rekognition_client = boto3.client("rekognition", region_name="us-east-1")
s3_client = boto3.client("s3", region_name="eu-west-2")

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

            print(f"Verification token: {registration_token}")
            verification_link = f"{settings.BASE_URL}/verify?token={registration_token}"
            self.bg_tasks.add_task(
                send_email_task,
                email_context=UserVerificationEmail(
                    context_vars={"verification_link": verification_link}
                ),
                recipients=[email],
            )

            return {"message": "Verification link send to your email address."}

    async def verify_token(self, verification_token: str, response: Response):
        async with self.conn.begin():
            try:
                unverified_user_data: dict = await AccountVerificationToken.decode(verification_token, conn=self.conn)
            except InvalidTokenError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Link expired.")

            signup_session_token: str = await SignupSessionToken.new(
                user_id=unverified_user_data.get("user_id"),
                email=unverified_user_data.get("email")
            )

            max_cookie_age = 15
            set_custom_cookie(
                response=response,
                key="signup_session_token",
                path="/",
                value=signup_session_token,
                max_age=max_cookie_age * SECONDS_IN_1_MINUTE
            )

        return


    async def _is_valid_photo_file(self, file: UploadFile):
        header = await file.read(2048)  # read first 2KB
        await file.seek(0)  # reset

        mime = magic.from_buffer(header, mime=True)
        if mime not in ["image/jpeg", "image/png"]:
            return False

        return True

    async def _verify_photo_quality(self, file: UploadFile):
        if not await self._is_valid_photo_file(file):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File provided is not an image.")

        image_bytes = await file.read()
        await file.seek(0)

        try:
            """Detect faces in an image using Amazon Rekognition."""
            response: dict = rekognition_client.detect_faces(
                Image={"Bytes": image_bytes},
                Attributes=["ALL"],
            )

            formatted_response: DetectFacesResponse = DetectFacesResponse.model_validate(response)
        except Exception as e:
            logger.error(f"Error verifying photo quality: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error verifying photo quality."
            )

        if formatted_response.FaceDetails is None or formatted_response.FaceDetails == []:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No faces detected in the image.")

        if len(formatted_response.FaceDetails) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Multiple faces detected in the image. Only register one face per user."
            )

        if quality := formatted_response.FaceDetails[0].Quality:
            if quality.Brightness is not None and quality.Brightness < 50:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image is too dark. Try a different image."
                )
            if quality.Sharpness is not None and quality.Sharpness < 50:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image is too blurry. Try a different image."
                )

        return

    async def _upload_file_to_s3(self, user: UserCreateModel, photo_upload: UploadFile):
        s3_key = f"base_user_reference_photos/users/{user.user_matric}/profile_photo.jpg"
        await photo_upload.seek(0)

        s3_client.put_object(
            Bucket="ave-base-bucket",
            Key=s3_key,
            Body=await photo_upload.read(),
            ContentType=photo_upload.content_type,
        )
        return s3_key

    async def create_new_user(self, user: UserCreateModel, photo_upload: UploadFile, token: str, response: Response) -> dict:
        if not token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification link.")

        """Create a new user account, create verification code, send verification code"""
        try:
            user_details: dict = await SignupSessionToken.decode(token)
        except InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification link.")

        user_id: str | None = user_details.get("user_id", None)
        user_email: str | None = user_details.get("email", None)

        if not all([user_id, user_email]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Corrupted verification link")

        user.email = user_email
        user.user_id = user_id
        user.password = hash_password(user.password)

        # verify photo quality with s3
        await self._verify_photo_quality(photo_upload)
        try:
            s3_key = await self._upload_file_to_s3(user=user, photo_upload=photo_upload)
        except Exception as e:
            logger.error(f"Error uploading photo to S3: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error uploading photo.")

        # Database transaction
        async with self.conn.begin():
            # Create user
            try:
                created_user: User = await self.user_repository.create_new_user(
                    user, bucket_image_key=s3_key, conn=self.conn
                )
            except IntegrityError as e:
                logger.error(f"Error creating user: {e}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ave already knows a user with this email or matric number. Wanna try logging in instead?"
                )

            response.delete_cookie(key="signup_session_token")

            # Generate and send a welcome email to a user
            dashboard_link: str = f"{settings.BASE_URL}/dashboard/{created_user.role}"
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

            reset_link = f"{settings.BASE_URL}/reset-password?token={token}"

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
                path="/",
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

    async def refresh_token(self, request: Request, response: Response) -> dict:
        """
        Verify the provided refresh token, generate a new access token, and refresh token, and invalidate the old one.

        Args:
            response (Response): The FastAPI response object to set cookies.

        Returns:
            dict: A dictionary containing the new access token and its type.
        """
        async with self.conn.begin():
            refresh_token = request.cookies.get("refresh_token")
            if not refresh_token:
                logger.debug("No refresh token was found in the user's client.")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No refresh token provided"
                )

            try:
                # Decode the refresh token to get the user ID
                user_id: str = await RefreshToken.decode(
                    conn=self.conn,
                    token=refresh_token
                )
            except InvalidTokenError:
                logger.debug("Invalid refresh token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token"
                )

            # Retrieve the user from the database
            existing_user: User = await self.user_repository.get_user_by_id(conn=self.conn, user_id=user_id)
            if not existing_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            # Generate a new access token and refresh token
            user_data = UserOutputModel(
                user_id=existing_user.id,
                username=existing_user.username,
                email=existing_user.email,
                user_matric=existing_user.user_matric,
                role=existing_user.role,
            )
            new_access_token: str = await AccessToken.new(user_data)
            new_refresh_token: str = await RefreshToken.new(
                user_id=existing_user.id,
                conn=self.conn,
            )

            # Set the new refresh token in the user’s cookies
            set_custom_cookie(
                response=response,
                key="refresh_token",
                value=new_refresh_token,
                path="/",
                max_age=60 * 60 * 24 * 7,  # 7 days
            )

            # Return the new access token to the client
            return {
                "access_token": new_access_token,
                "token_type": "Bearer",
            }

    async def get_college_list(self):
        colleges: Sequence[College] = await self.user_repository.get_list_of_colleges(
            conn=self.conn
        )

        formatted_colleges: List[CollegeSchema] = [CollegeSchema.model_validate(college, from_attributes=True) for college in colleges]
        return formatted_colleges

    async def compare_and_verify_face(self, user: UserOutputModel, session_id: str):
        try:
            response = rekognition_client.get_face_liveness_session_results(SessionId=session_id)
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail=str(e))

        reference_image = response.get("ReferenceImage", None)
        if not reference_image:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error verifying liveness")

        s3_key = f"base_user_reference_photos/users/{user.user_matric}/profile_photo.jpg"

        try:
            s3_object = s3_client.get_object(Bucket="ave-base-bucket", Key=s3_key)
            source_bytes = s3_object["Body"].read()

            compare_faces_response = rekognition_client.compare_faces(
                TargetImage={"Bytes": reference_image["Bytes"]},
                SourceImage={"Bytes": source_bytes},
                SimilarityThreshold=80,
            )
        except Exception as e:
            logger.error(f"Error verifying face: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Facial verification failed")

        formated_compare_faces_response: CompareFacesResponse =CompareFacesResponse.model_validate(compare_faces_response)
        if not formated_compare_faces_response.FaceMatches:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Facial verification failed")

        if len(formated_compare_faces_response.FaceMatches) > 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many faces in the captured video feed. Try again")

        similarity_threshold = 80
        if formated_compare_faces_response.FaceMatches[0].Similarity < similarity_threshold:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Facial verification failed")

        return {
            "status": response["Status"],
            "confidence": response.get("Confidence", 0),
        }
