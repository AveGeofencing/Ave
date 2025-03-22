from datetime import datetime
from typing import Annotated, Dict, List
from fastapi import APIRouter, Depends

from ..schemas import GeofenceCreateModel, AttendanceRecordModel, AttendanceRecordOut
from ..database import get_db_session
from ..auth.sessions.sessionDependencies import (
    authenticate_admin_user,
    authenticate_student_user,
    authenticate_user_by_session_token,
)
from ..services import GeofenceService, get_geofence_service, get_user_service

authenticate_admin = Annotated[dict, Depends(authenticate_admin_user)]
authenticate_student = Annotated[dict, Depends(authenticate_student_user)]
GeofenceServiceDependency = Annotated[GeofenceService, Depends(get_geofence_service)]


GeofenceRouter = APIRouter(prefix="/geofence", tags=["Geofences"])


@GeofenceRouter.post("/create_geofence")
async def create_geofence(
    geofence: GeofenceCreateModel,
    geofence_service: GeofenceServiceDependency,
    admin: authenticate_admin,
):
    result = await geofence_service.create_geofence(admin["user_matric"], geofence)
    return result


@GeofenceRouter.get("/get_geofence", dependencies=[Depends(authenticate_admin_user)])
async def get_geofence(
    course_title: str, date: datetime, geofence_service: GeofenceServiceDependency
):
    """Returns details of geofence for a given course title"""
    geofence_response = await geofence_service.get_geofence(course_title, date)
    return geofence_response


@GeofenceRouter.get(
    "/get_geofences", dependencies=[Depends(authenticate_user_by_session_token)]
)
async def get_geofences(geofence_service: GeofenceServiceDependency):
    """Returns all the geofences created"""
    geofences_response = await geofence_service.get_all_geofences()
    return geofences_response


@GeofenceRouter.get("/get_my_geofences")
async def get_my_geofences_created(
    admin: authenticate_admin, geofence_service: GeofenceServiceDependency
):
    """Returns a list of all geofences created by the given admin"""
    geofences_response = await geofence_service.get_all_geofences(admin["user_matric"])
    return geofences_response


@GeofenceRouter.post("/record_attendance")
async def record_attendance(
    attendance: AttendanceRecordModel,
    geofence_service: GeofenceServiceDependency,
    student: authenticate_student,
):

    recorded_attendance_response = await geofence_service.record_geofence_attendance(
        user_matric=student["user_matric"],
        attendance=attendance,
    )

    return recorded_attendance_response


@GeofenceRouter.get(
    "/get_attendances", response_model=Dict[str, List[AttendanceRecordOut]]
)
async def get_geofence_attendances(
    fence_code, admin: authenticate_admin, geofence_service: GeofenceServiceDependency
):
    """Returns the attendances for a given course"""
    attendances_response = await geofence_service.get_geofence_attendances(
        fence_code=fence_code, user_id=admin["user_matric"]
    )

    return attendances_response


@GeofenceRouter.put("/deactivate")
async def deactivate_geofence(
    admin: authenticate_admin,
    date: datetime,
    geofence_name: str,
    geofence_service: GeofenceServiceDependency,
):
    deactivate_message = await geofence_service.deactivate_geofence(
        geofence_name, date, admin["user_matric"]
    )

    return deactivate_message
