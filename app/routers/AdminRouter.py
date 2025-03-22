from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, HTTPException, Request

from ..services import UserService, get_user_service
from fastapi import Depends
from ..auth.sessions.sessionDependencies import authenticate_admin_user

AdminRouter = APIRouter(prefix="/user/admin", tags=["Users/Admin"])

UserServiceDependency = Annotated[UserService, Depends(get_user_service)]


@AdminRouter.get("/{email}", dependencies=[Depends(authenticate_admin_user)])
async def get_user_by_email(email: str, user_service: UserServiceDependency):
    return await user_service.get_user_by_email_or_matric(email)
