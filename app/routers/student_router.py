from typing import Annotated, Optional
from fastapi import APIRouter

from ..services import UserService
from fastapi import Depends
from ..auth.sessions.sessionDependencies import authenticate_student_user

student_router = APIRouter(prefix="/user/student", tags=["Users/Student"])

authenticate_student = Annotated[dict, Depends(authenticate_student_user)]
UserServiceDependency = Annotated[UserService, Depends()]


@student_router.get("/get_my_records")
async def get_my_records(
    course_title: str | None,
    student: authenticate_student,
    user_service: UserServiceDependency,
):
    user_records = await user_service.get_user_records(
        student["user_matric"], course_title
    )
    return user_records
