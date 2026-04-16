from datetime import datetime
from typing import Annotated, Dict, List
from fastapi import APIRouter, Depends

from ..schemas import GeofenceCreateModel, AttendanceRecordModel, AttendanceRecordOut, UserOutputModel
from ..utils.security_dependencies import (
    authenticate_admin_user,
    authenticate_student_user,
    get_current_user,
)
from ..services import GeofenceService

authenticate_admin = Annotated[UserOutputModel, Depends(authenticate_admin_user)]
authenticate_student = Annotated[UserOutputModel, Depends(authenticate_student_user)]
GeofenceServiceDependency = Annotated[GeofenceService, Depends()]


router = APIRouter(prefix="/geofence", tags=["Geofence"])


@router.post("/create_geofence")
async def create_geofence(
    geofence: GeofenceCreateModel,
    geofence_service: GeofenceServiceDependency,
    admin: authenticate_admin,
):
    result = await geofence_service.create_geofence(admin.user_matric, geofence)
    return result

@router.get(
    "/get_geofences"
)
async def get_geofences(geofence_service: GeofenceServiceDependency, user: Annotated[UserOutputModel, Depends(get_current_user)]):
    """Returns all the geofence created"""
    geofences_response = await geofence_service.get_all_geofences(
        user_matric=user.user_matric
    )
    return geofences_response


@router.get("/get_my_geofences")
async def get_my_geofences_created(
    admin: authenticate_admin, geofence_service: GeofenceServiceDependency
):
    """Returns a list of all geofences created by the given admin"""
    geofences_response = await geofence_service.get_all_my_geofences(admin.user_matric)
    return geofences_response


@router.post("/record-attendance")
async def record_attendance(
    attendance: AttendanceRecordModel,
    geofence_service: GeofenceServiceDependency,
    student: authenticate_student,
):

    recorded_attendance_response = await geofence_service.record_geofence_attendance(
        user_matric=student.user_matric,
        attendance=attendance,
    )

    return recorded_attendance_response


@router.get(
    "/get_attendances", response_model=List[AttendanceRecordOut]
)
async def get_geofence_attendances(
    fence_id: str, admin: authenticate_admin, geofence_service: GeofenceServiceDependency
):
    """Returns the attendances for a given course"""
    attendances_response = await geofence_service.get_geofence_attendances(
        fence_id=fence_id, user_id=admin.user_matric
    )

    return attendances_response


@router.put("/deactivate")
async def deactivate_geofence(
    admin: authenticate_admin,
    geofence_id: str,
    geofence_service: GeofenceServiceDependency,
):
    deactivate_message = await geofence_service.deactivate_geofence(
        geofence_id, admin.user_matric
    )

    return deactivate_message

@router.get("/{geofence_id}", dependencies=[Depends(authenticate_admin_user)])
async def get_geofence(
    geofence_id: str, geofence_service: GeofenceServiceDependency
):
    """Returns details of geofence for a given course title"""
    geofence_response = await geofence_service.get_geofence(geofence_id=geofence_id)
    return geofence_response