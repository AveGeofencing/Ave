from datetime import datetime, timezone
import logging
import random
import string
from typing import Annotated, Dict, Optional
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException
from ..exceptions import *
from ..schemas import GeofenceCreateModel, AttendanceRecordModel
from ..services import get_user_service, UserService
from ..repositories import GeofenceRepository, get_geofence_repository
from ..utils import check_user_in_circular_geofence


logger = logging.getLogger("uvicorn")

# Dependencies
GeofenceRepositoryDependency = Annotated[
    GeofenceRepository, Depends(get_geofence_repository)
]


class GeofenceService:
    def __init__(self, geofence_repository: GeofenceRepository):
        self.geofenceRepository: GeofenceRepository = geofence_repository

    async def create_geofence(
        self,
        creator_matric: str,
        geofence: GeofenceCreateModel,
    ):  # SINGULAR
        try:
            characters = string.ascii_letters + string.digits
            fence_code = "".join(random.choice(characters) for _ in range(6)).lower()

            existing_geofence = await self.geofenceRepository.get_geofence(
                geofence.name, geofence.start_time
            )
            if existing_geofence:
                raise GeofenceAlreadyExistException(
                    f"Geofence '{geofence.name}' already exist for today"
                )

            start_time_utc = geofence.start_time.astimezone(ZoneInfo("UTC"))
            end_time_utc = geofence.end_time.astimezone(ZoneInfo("UTC"))
            NOW = datetime.now(ZoneInfo("UTC"))
            if start_time_utc >= end_time_utc:
                raise InvalidDurationException(
                    "Invalid duration for geofence. Please adjust duration and try again."
                )

            if end_time_utc < NOW:
                raise InvalidDurationException("End time cannot be in the past.")

            added_geofence = await self.geofenceRepository.create_geofence(
                geofence, fence_code, creator_matric, start_time_utc, end_time_utc, NOW
            )

            return {"Code": fence_code, "name": added_geofence.name}
        except GeofenceAlreadyExistException as e:
            logger.error(
                f"Error while attempting to create new geofence with name {geofence.name}: {str(e)}"
            )
            raise HTTPException(status_code=400, detail=f"{str(e)}")
        except InvalidDurationException as e:
            logger.error(
                f"Error while attempting to create new geofence with name {geofence.name}: {str(e)}"
            )
            raise HTTPException(status_code=400, detail=f"{str(e)}")
        except Exception as e:
            logger.error(f"Something went wrong with creating geofence: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Something went wrong. Contact admin"
            )

    async def get_all_geofences(
        self, user_id: Optional[str] = None
    ) -> Dict[str, any]:  # PLURAL
        try:
            if user_id is not None:
                geofences = await self.geofenceRepository.get_all_geofences_by_user(
                    user_id
                )
            else:
                geofences = await self.geofenceRepository.get_all_geofences()

            if not geofences:
                return {"geofences": []}
            return {"geofences": geofences}

        except Exception as e:
            logger.error(f"Error fetching all geofences : {str(e)}")
            raise HTTPException(
                status_code=500, detail="Something went wrong, contact admin."
            )

    async def get_geofence(
        self, course_title: str, date: datetime
    ) -> Dict[str, any]:  # SINGULAR
        try:
            geofence = await self.geofenceRepository.get_geofence(course_title, date)
            if not geofence:
                return None

            return {"geofence": geofence}

        except Exception as e:
            logger.error(f"Something went wrong in fetching geofence: {str(e)}")

            raise HTTPException(
                status_code=500, detail="Something went wrong. Contact admin."
            )

    async def get_geofence_by_fence_code(self, fence_code: str):
        try:
            geofence = await self.geofenceRepository.get_geofence_by_fence_code(
                fence_code
            )
            if not geofence:
                return None
            return geofence

        except Exception as e:
            logger.error(
                f"Something went wrong with getting geofence with fence code {fence_code} : {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Something went wrong, contact admin"
            )

    async def get_geofence_attendances(
        self, fence_code: str, user_id: str
    ) -> Dict[str, any]:
        geofence = await self.geofenceRepository.get_geofence_by_fence_code(
            fence_code=fence_code
        )
        if not geofence:
            raise HTTPException(
                status_code=404,
                detail=f"Geofence with fence code {fence_code} not found",
            )

        if geofence.creator_matric != user_id:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to view this geofence's attendance.",
            )
        try:
            attendance_list = []
            attendances = await self.geofenceRepository.get_geofence_attendances(
                fence_code=fence_code
            )
            for attendance in attendances:
                attendance_list.append(
                    {
                        "user_matric": attendance.user_matric,
                        "username": attendance.user.username,
                        "fence_code": attendance.fence_code,
                    }
                )
            if not attendances:
                return {"attendance": []}
            return {"attendance": attendance_list}

        except Exception as e:
            logger.error(
                f"Something went wrong in fetching geofence attendances : {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Something went wrong, contact admin."
            )

    async def record_geofence_attendance(
        self,
        attendance: AttendanceRecordModel,
        user_matric: str,
        user_service: Annotated[UserService, Depends(get_user_service)],
    ):
        user = await user_service.get_user_by_email_or_matric(matric=user_matric)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        geofence = await self.geofenceRepository.get_geofence_by_fence_code(
            attendance.fence_code
        )
        if not geofence:
            raise HTTPException(
                status_code=404,
                detail=f"Invalid fence code: {attendance.fence_code}",
            )

        try:
            if geofence.status.lower() != "active":
                raise GeofenceStatusException("Geofence is not active for attendance.")

            matric_fence_code = geofence.fence_code + user["user_matric"]
            existing_record = await self.geofenceRepository.get_attendance_record_for_student_for_geofence(
                matric_fence_code
            )
            if existing_record:
                raise AlreadyRecordedAttendanceException(
                    "You have already recorded attendance for this class",
                )

            if not check_user_in_circular_geofence(
                attendance.lat, attendance.long, geofence
            ):
                raise UserNotInGeofenceException(
                    "User is not within geofence, attendance not recorded",
                )

            await self.geofenceRepository.record_geofence_attendance(
                attendance=attendance,
                user_matric=user["user_matric"],
                geofence_name=geofence.name,
                matric_fence_code=matric_fence_code,
            )
            return {"message": "Attendance recorded successfully"}

        except GeofenceStatusException as e:
            raise HTTPException(status_code=403, detail=f"{str(e)}")
        except AlreadyRecordedAttendanceException as e:
            raise HTTPException(status_code=403, detail=f"{str(e)}")
        except UserNotInGeofenceException as e:
            raise HTTPException(status_code=403, detail=f"{str(e)}")
        except Exception as e:
            logger.error(f"Something went wrong with recording attendance: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Something went wrong, contact admin"
            )

    async def deactivate_geofence(
        self, geofence_name: str, date: datetime, user_matric: str
    ):
        geofence = await self.geofenceRepository.get_geofence(geofence_name, date)

        if geofence is None:
            raise HTTPException(
                status_code=404, detail=f"Geofence {geofence_name} not found."
            )
        if user_matric != geofence.creator_matric:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete this class as you are not the creator.",
            )
        try:
            if geofence.status == "inactive":
                raise GeofenceStatusException("Geofence is already inactive")

            await self.geofenceRepository.deactivate_geofence(
                geofence_name=geofence.name, date=date
            )
            return {"message": "Geofence deactivated successfully"}

        except GeofenceStatusException as e:
            raise HTTPException(status_code=403, detail=f"{str(e)}")
        except Exception as e:
            logger.error(f"Something went wrong with deactivating geofence: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Something went wrong, contact admin."
            )


def get_geofence_service(
    geofence_repository: GeofenceRepositoryDependency,
) -> GeofenceService:
    return GeofenceService(geofence_repository=geofence_repository)
