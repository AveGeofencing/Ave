from typing import Annotated
from fastapi import APIRouter, Depends


from ..services import UserService
from ..schemas.user_schema import UserCreateModel

general_user_router = APIRouter(prefix="/user", tags=["General User"])

UserServiceDependency = Annotated[UserService, Depends()]


@general_user_router.post(
    path="/",
    summary="Creating a new user. Sends a verification email to the user's email address.",
)
async def create_new_user(user: UserCreateModel, user_service: UserServiceDependency):
    """Endpoint for creating new user in the system"""
    return await user_service.create_new_user(user)


@general_user_router.post(
    path="/verify",
    summary="Verifying user's email after registration. Gets a JWT to update user account to 'verified'"
)
async def verify_user_email_after_reg(
    token: str,
    user_service: UserServiceDependency,
):
    user_verified = await user_service.verify_user(
        token=token
    )
    return user_verified


@general_user_router.post(
    path="/forgot_password",
    summary="Send a password reset email to the users email. "
            "Sends a link that redirects them to the /reset_password endpoint."
)
async def forgot_password(
    student_email: str,
    user_service: UserServiceDependency,
):
    await user_service.send_reset_password_email(
        user_email=student_email,
    )
    return {"message": "Password reset email has been sent successfully"}


@general_user_router.post(
    path="/reset_password",
    summary="Takes in a jwt, decodes it and gets the user id of the user they want to update."
)
async def reset_password(
    new_password: str,
    token: str,
    user_service: UserServiceDependency,
):

    return await user_service.change_password(new_password, token)
