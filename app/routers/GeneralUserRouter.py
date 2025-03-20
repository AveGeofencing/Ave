from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.APIKeys import get_api_key

from ..services import UserService
from ..database.database import get_db_session
from ..schemas.UserSchema import UserCreateModel

GeneralUserRouter = APIRouter(prefix="/user", tags=["General User"])
DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@GeneralUserRouter.post("/create_user", dependencies=[Depends(get_api_key)])
async def create_new_user(
    user: UserCreateModel,
    session: DBSessionDep,
):
    user_service = UserService(session)
    created_message = await user_service.create_new_user(user)

    return created_message

@GeneralUserRouter.post("/send_verification_code")
async def verify_user_email_after_reg(
    session: DBSessionDep,
    user_email: str,
    matric: str,
    background_tasks: BackgroundTasks,
):
    userService = UserService(session)
    user_verified = await userService.create_and_send_registration_code(email=user_email, matric=matric, backgroundTask=background_tasks)
    return user_verified

@GeneralUserRouter.post("/forgot_password")
async def forgot_password(
    session: DBSessionDep,
    student_email: str,
    background_tasks: BackgroundTasks,
    request: Request,
):
    userService = UserService(session)
    await userService.send_reset_password_email(
        user_email=student_email,
        background_tasks=background_tasks,
    )
    return {"message": "Password reset email has been sent successfully"}


@GeneralUserRouter.post("/reset_password")
async def reset_password(
    new_password, token: str, session: DBSessionDep, background_tasks: BackgroundTasks
):

    userService = UserService(session)
    message = await userService.change_password(new_password, token, background_tasks)
    return message
