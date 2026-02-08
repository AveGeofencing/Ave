from typing import Annotated
from fastapi import APIRouter, Depends

from ..services import UserService
from ..auth.sessions.sessionDependencies import authenticate_admin_user

admin_router = APIRouter(prefix="/user/admin", tags=["Users/Admin"])

UserServiceDependency = Annotated[UserService, Depends()]


@admin_router.get(
    path="/{email}",
    dependencies=[Depends(authenticate_admin_user)],
)
async def get_user_by_email(email: str, user_service: UserServiceDependency):
    return await user_service.get_user_by_email_or_matric(email)
