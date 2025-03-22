from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.APIKeys import get_api_key

from ..services import UserService, get_user_service
from ..database.database import get_db_session
from ..schemas.UserSchema import UserCreateModel

GeneralUserRouter = APIRouter(prefix="/user", tags=["General User"])

UserServiceDependency = Annotated[UserService, Depends(get_user_service)]


@GeneralUserRouter.post("/create_user", dependencies=[Depends(get_api_key)])
async def create_new_user(user: UserCreateModel, user_service: UserServiceDependency):
    created_message = await user_service.create_new_user(user)

    return created_message


@GeneralUserRouter.post("/send_verification_code")
async def verify_user_email_after_reg(
    user_email: str,
    matric: str,
    background_tasks: BackgroundTasks,
    user_service: UserServiceDependency,
):
    user_verified = await user_service.create_and_send_registration_code(
        email=user_email, matric=matric, backgroundTask=background_tasks
    )
    return user_verified


@GeneralUserRouter.post("/forgot_password")
async def forgot_password(
    student_email: str,
    background_tasks: BackgroundTasks,
    user_service: UserServiceDependency,
):
    await user_service.send_reset_password_email(
        user_email=student_email,
        background_tasks=background_tasks,
    )
    return {"message": "Password reset email has been sent successfully"}


@GeneralUserRouter.post("/reset_password")
async def reset_password(
    new_password: str,
    token: str,
    background_tasks: BackgroundTasks,
    user_service: UserServiceDependency,
):

    message = await user_service.change_password(new_password, token, background_tasks)
    return message
