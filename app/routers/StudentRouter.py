from typing import Annotated, Optional
from fastapi import APIRouter, HTTPException, Request

from ..services import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, BackgroundTasks
from ..database import get_db_session
from ..auth.sessions.sessionDependencies import authenticate_student_user

StudentRouter = APIRouter(prefix="/user/student", tags=["Users/Student"])

DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
authenticate_student = Annotated[dict, Depends(authenticate_student_user)]


@StudentRouter.get("/get_my_records")
async def get_my_records(
    course_title: Optional[str], session: DBSessionDep, student: authenticate_student
):
    userService = UserService(session)
    user_records = await userService.get_user_records(
        student["user_matric"], course_title
    )
    return user_records
