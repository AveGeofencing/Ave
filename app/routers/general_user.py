from typing import Annotated
from fastapi import APIRouter, Depends

from ..services import UserService

general_user_router = APIRouter(prefix="/user", tags=["General User"])
UserServiceDependency = Annotated[UserService, Depends()]

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

@general_user_router.get("/colleges")
async def get_colleges(
    user_service: Annotated[UserService, Depends()]
):
    return await user_service.get_college_list()