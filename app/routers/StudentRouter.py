from typing import Annotated, Optional
from fastapi import APIRouter

from ..services import UserService, get_user_service
from fastapi import Depends
from ..auth.sessions.sessionDependencies import authenticate_student_user

StudentRouter = APIRouter(prefix="/user/student", tags=["Users/Student"])

authenticate_student = Annotated[dict, Depends(authenticate_student_user)]
UserServiceDependency = Annotated[UserService, Depends(get_user_service)]


@StudentRouter.get("/get_my_records")
async def get_my_records(
    course_title: Optional[str],
    student: authenticate_student,
    user_service: UserServiceDependency,
):
    user_records = await user_service.get_user_records(
        student["user_matric"], course_title
    )
    return user_records
