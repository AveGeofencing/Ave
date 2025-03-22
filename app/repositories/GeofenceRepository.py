from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from ..database import get_db_session
from ..models import Geofence, AttendanceRecord
from ..schemas import AttendanceRecordModel, GeofenceCreateModel

from fastapi import Depends
from sqlalchemy import and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

DatabaseDependency = Annotated[AsyncSession, Depends(get_db_session)]


class GeofenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_geofence(
        self,
        geofence: GeofenceCreateModel,
        fence_code: str,
        creator_matric: str,
        start_time_utc,
        end_time_utc,
        NOW,
    ):
        new_geofence = Geofence(
            fence_code=fence_code,
            name=geofence.name,
            creator_matric=creator_matric,
            latitude=geofence.latitude,
            longitude=geofence.longitude,
            radius=geofence.radius,
            fence_type=geofence.fence_type,
            start_time=start_time_utc,
            end_time=end_time_utc,
            status=(
                "scheduled"
                if NOW < start_time_utc
                else "active" if start_time_utc <= NOW < end_time_utc else "inactive"
            ),
            time_created=NOW,
        )

        self.session.add(new_geofence)
        await self.session.commit()
        await self.session.refresh(new_geofence)

        return new_geofence

    async def get_all_geofences(self):
        stmt = select(Geofence)
        result = await self.session.execute(stmt)

        geofences = result.scalars().all()
        return geofences

    async def get_all_geofences_by_user(self, user_id: str):
        stmt = select(Geofence).filter(Geofence.creator_matric == user_id)
        result = await self.session.execute(stmt)
        geofence_by_user = result.scalars().all()

        return geofence_by_user

    async def get_geofence(self, course_title: str, date: datetime) -> Geofence:
        stmt = (
            select(Geofence)
            .options(selectinload(Geofence.student_attendances))
            .filter(
                and_(
                    Geofence.name == course_title,
                    func.date(Geofence.start_time) == date.date(),
                )
            )
        )

        result = await self.session.execute(stmt)
        geofence = result.scalars().one_or_none()

        return geofence

    async def get_geofence_by_fence_code(self, fence_code: str):
        stmt = (
            select(Geofence)
            .options(selectinload(Geofence.student_attendances))
            .filter(Geofence.fence_code == fence_code)
        )
        result = await self.session.execute(stmt)
        geofence = result.scalars().one_or_none()
        return geofence

    async def record_geofence_attendance(
        self,
        attendance: AttendanceRecordModel,
        user_matric: str,
        geofence_name: str,
        matric_fence_code: str,
    ):
        attendance = AttendanceRecord(
            user_matric=user_matric,
            fence_code=attendance.fence_code,
            geofence_name=geofence_name,
            timestamp=datetime.now(ZoneInfo("UTC")),
            matric_fence_code=matric_fence_code,
        )
        self.session.add(attendance)
        await self.session.commit()
        await self.session.refresh(attendance)

        return attendance

    async def get_attendance_record_for_student_for_geofence(
        self, matric_fence_code: str
    ):
        stmt = select(AttendanceRecord).filter(
            AttendanceRecord.matric_fence_code == matric_fence_code
        )
        result = await self.session.execute(stmt)
        attendance_record = result.scalars().one_or_none()

        return attendance_record

    async def deactivate_geofence(self, geofence_name: str, date: datetime):
        geofence = await self.get_geofence(course_title=geofence_name, date=date)

        geofence.status = "inactive"

        self.session.add(geofence)
        await self.session.commit()
        await self.session.refresh(geofence)

    async def get_geofence_attendances(self, fence_code: str):
        stmt = (
            select(AttendanceRecord)
            .options(selectinload(AttendanceRecord.user))
            .filter(AttendanceRecord.fence_code == fence_code)
        )
        result = await self.session.execute(stmt)

        attendances = result.scalars().all()
        return attendances


def get_geofence_repository(db_session: DatabaseDependency) -> GeofenceRepository:
    return GeofenceRepository(session=db_session)
