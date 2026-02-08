from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, Request


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


@general_user_router.post("/forgot_password")
async def forgot_password(
    student_email: str,
    user_service: UserServiceDependency,
):
    await user_service.send_reset_password_email(
        user_email=student_email,
    )
    return {"message": "Password reset email has been sent successfully"}


@general_user_router.post("/reset_password")
async def reset_password(
    new_password: str,
    token: str,
    user_service: UserServiceDependency,
):

    return await user_service.change_password(new_password, token)
