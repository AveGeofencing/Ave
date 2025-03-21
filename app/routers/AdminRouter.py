from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, HTTPException, Request

from ..services import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from ..database import get_db_session
from ..auth.sessions.sessionDependencies import authenticate_admin_user

AdminRouter = APIRouter(prefix="/user/admin", tags=["Users/Admin"])

DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@AdminRouter.get("/{email}", dependencies=[Depends(authenticate_admin_user)])
async def get_user_by_email(email: str, session: DBSessionDep):
    # print(user_data)
    userService = UserService(session)
    return await userService.get_user_by_email_or_matric(email)
