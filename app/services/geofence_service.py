from datetime import datetime
import random
import string
from typing import Annotated, Dict, Optional
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ..database import get_db_session
from ..schemas import GeofenceCreateModel, AttendanceRecordModel
from ..repositories import GeofenceRepository, UserRepository
from ..utils import check_user_in_circular_geofence


class GeofenceService:
    def __init__(
        self,
        geofence_repository: Annotated[GeofenceRepository, Depends()],
        user_repository: Annotated[UserRepository, Depends()],
        conn: Annotated[AsyncSession, Depends(get_db_session)]
    ):
        self.geofence_repo: GeofenceRepository = geofence_repository
        self.user_repo: UserRepository = user_repository
        self.conn: AsyncSession = conn

    async def create_geofence(
        self,
        creator_matric: str,
        geofence: GeofenceCreateModel,
    ):  # SINGULAR
        async with self.conn.begin():
            characters = string.ascii_letters + string.digits
            fence_code = "".join(random.choice(characters) for _ in range(6)).lower()

            existing_geofence = await self.geofence_repo.get_geofence(
                course_title=geofence.name, date=geofence.start_time, conn=self.conn
            )

            if existing_geofence:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Geofence '{geofence.name}' already exist for today"
                )

            start_time_utc = geofence.start_time.astimezone(ZoneInfo("UTC"))
            end_time_utc = geofence.end_time.astimezone(ZoneInfo("UTC"))
            NOW = datetime.now(ZoneInfo("UTC"))

            if start_time_utc >= end_time_utc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid duration for geofence. Please adjust duration and try again."
                )

            if end_time_utc < NOW:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="End time cannot be in the past."
                )

            added_geofence = await self.geofence_repo.create_geofence(
                conn=self.conn,
                geofence=geofence,
                fence_code=fence_code,
                creator_matric=creator_matric,
                start_time_utc=start_time_utc,
                end_time_utc=end_time_utc,
                now=NOW
            )

            return {"Code": fence_code, "name": added_geofence.name}


    async def get_all_geofences(
        self, user_id: Optional[str] = None
    ) -> Dict[str, any]:  # PLURAL
        if user_id is not None:
            geofences = await self.geofence_repo.get_all_geofences_by_user(
                user_id=user_id, conn=self.conn
            )
        else:
            geofences = await self.geofence_repo.get_all_geofences(conn=self.conn)

        if not geofences:
            return {"geofences": []}

        return {"geofences": geofences}


    async def get_geofence(
        self, course_title: str, date: datetime
    ) -> Dict[str, any]:  # SINGULAR
        geofence = await self.geofence_repo.get_geofence(course_title, date, conn=self.conn)
        if not geofence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Geofence not found.")

        return {"geofence": geofence}


    async def get_geofence_by_fence_code(self, fence_code: str):
        geofence = await self.geofence_repo.get_geofence_by_fence_code(
            fence_code=fence_code, conn=self.conn
        )
        if not geofence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Geofence not found.")

        return geofence


    async def get_geofence_attendances(
        self, fence_code: str, user_id: str
    ) -> Dict[str, any]:
        geofence = await self.geofence_repo.get_geofence_by_fence_code(
            fence_code=fence_code, conn=self.conn
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

        attendance_list = []
        attendances = await self.geofence_repo.get_geofence_attendances(
            fence_code=fence_code, conn=self.conn
        )

        if attendances:
            for attendance in attendances:
                attendance_list.append(
                    {
                        "user_matric": attendance.user_matric,
                        "username": attendance.user.username,
                        "fence_code": attendance.fence_code,
                    }
                )

        return {"attendance": attendance_list}


    async def record_geofence_attendance(
        self,
        attendance: AttendanceRecordModel,
        user_matric: str,
    ):
        async with self.conn.begin():
            user = await self.user_repo.get_user_by_email_or_matric(matric=user_matric, conn=self.conn)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

            geofence = await self.geofence_repo.get_geofence_by_fence_code(
                fence_code=attendance.fence_code, conn=self.conn
            )
            if not geofence:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Invalid fence code: {attendance.fence_code}",
                )

            if geofence.status.lower() != "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Geofence is not active for attendance."
                )

            matric_fence_code = geofence.fence_code + user.user_matric
            existing_record = await self.geofence_repo.get_attendance_record_for_student_for_geofence(
                matric_fence_code=matric_fence_code, conn=self.conn
            )
            if existing_record:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You have already recorded attendance for this class",
                )

            if not check_user_in_circular_geofence(
                attendance.lat, attendance.long, geofence
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is not within geofence, attendance not recorded",
                )

            await self.geofence_repo.record_geofence_attendance(
                attendance=attendance,
                user_matric=user.user_matric,
                geofence_name=geofence.name,
                matric_fence_code=matric_fence_code,
                conn=self.conn
            )

            return {"message": "Attendance recorded successfully"}


    async def deactivate_geofence(
        self, geofence_name: str, date: datetime, user_matric: str
    ):
        async with self.conn.begin():
            geofence = await self.geofence_repo.get_geofence(geofence_name, date, conn=self.conn)

            if geofence is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"Geofence {geofence_name} not found."
                )
            if user_matric != geofence.creator_matric:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this class as you are not the creator.",
                )

            if geofence.status == "inactive":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Geofence is already inactive")

            await self.geofence_repo.deactivate_geofence(
                geofence_code=geofence.name, conn=self.conn
            )
            return {"message": "Geofence deactivated successfully"}


