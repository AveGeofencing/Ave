from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from ..database import get_db_session
from ..models import Geofence, AttendanceRecord
from ..schemas import AttendanceRecordModel, GeofenceCreateModel

from fastapi import Depends
from sqlalchemy import and_, func, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

DATABASE_DEPENDENCY = Annotated[AsyncSession, Depends(get_db_session)]


class GeofenceRepository:

    @classmethod
    async def create_geofence(
        cls,
        conn: AsyncSession,
        geofence: GeofenceCreateModel,
        fence_code: str,
        creator_matric: str,
        start_time_utc,
        end_time_utc,
        now,
    ):
        if now < start_time_utc:
            status = "scheduled"
        elif start_time_utc <= now < end_time_utc:
            status = "active"
        else:
            status = "inactive"

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
            status=status,
            time_created=now,
        )

        conn.add(new_geofence)
        await conn.flush()
        await conn.refresh(new_geofence)

        return new_geofence

    @classmethod
    async def get_all_geofences(cls, conn: AsyncSession):
        stmt = select(Geofence).options(selectinload(Geofence.student_attendances))
        result = await conn.execute(stmt)

        geofences = result.scalars().all()
        return geofences

    @classmethod
    async def get_all_geofences_by_user(cls, user_matric: str, conn: AsyncSession):
        stmt = select(Geofence).filter(Geofence.creator_matric == user_matric)
        result = await conn.execute(stmt)
        geofence_by_user = result.scalars().all()

        return geofence_by_user

    @classmethod
    async def get_geofence(cls, geofence_id: str, conn: AsyncSession) -> Geofence:
        stmt = (
            select(Geofence)
            .options(selectinload(Geofence.student_attendances))
            .where(
                Geofence.id == geofence_id
            )
        )

        result = await conn.execute(stmt)
        geofence = result.scalars().one_or_none()

        return geofence

    @classmethod
    async def get_geofence_by_fence_code(cls, fence_code: str, conn: AsyncSession):
        stmt = (
            select(Geofence)
            .where(Geofence.fence_code == fence_code)
            .options(selectinload(Geofence.student_attendances))
        )
        result = await conn.execute(stmt)
        geofence = result.scalars().one_or_none()
        return geofence

    @classmethod
    async def record_geofence_attendance(
        cls,
        attendance: AttendanceRecordModel,
        user_matric: str,
        geofence_name: str,
        matric_fence_code: str,
        conn: AsyncSession
    ):
        attendance = AttendanceRecord(
            user_matric=user_matric,
            fence_code=attendance.fence_code,
            geofence_name=geofence_name,
            timestamp=datetime.now(ZoneInfo("UTC")),
            matric_fence_code=matric_fence_code,
        )
        conn.add(attendance)
        await conn.flush()
        await conn.refresh(attendance)

        return attendance

    @classmethod
    async def get_attendance_record_for_student_for_geofence(
        cls, fence_code: str, user_matric: str, conn: AsyncSession
    ):
        stmt = select(AttendanceRecord).where(
            and_(
                AttendanceRecord.fence_code == fence_code,
                AttendanceRecord.user_matric == user_matric
            )
        )
        result = await conn.execute(stmt)
        attendance_record = result.scalars().one_or_none()

        return attendance_record

    @classmethod
    async def deactivate_geofence(cls, fence_id: str, conn: AsyncSession):
        stmt = update(Geofence).where(Geofence.id == fence_id).values(status="inactive")
        await conn.execute(stmt)
        await conn.flush()


    @classmethod
    async def get_geofence_attendances(cls, fence_code: str, conn: AsyncSession):
        stmt = (
            select(AttendanceRecord)
            .options(selectinload(AttendanceRecord.user))
            .where(AttendanceRecord.fence_code == fence_code)
        )
        result = await conn.execute(stmt)

        attendances = result.scalars().all()
        return attendances

    @classmethod
    async def get_geofence_by_id(cls, geofence_id: str, conn: AsyncSession):
        stmt = select(Geofence).where(Geofence.id == geofence_id)
        result = await conn.execute(stmt)
        geofence = result.scalars().one_or_none()
        return geofence

