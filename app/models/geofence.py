from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from sqlalchemy import TIMESTAMP, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..common import generate_id
from ..database import Base

if TYPE_CHECKING:
    from .attendance_record import AttendanceRecord

class Geofence(Base):
    __tablename__ = "geofences"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_id)
    fence_code: Mapped[str] = mapped_column(String(15), unique=True)
    name: Mapped[str] = mapped_column(String(60))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    radius: Mapped[float] = mapped_column(Float)
    fence_type: Mapped[str] = mapped_column(String(60))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(60))
    time_created: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(tz=ZoneInfo("UTC"))
    )
    creator_matric: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.user_matric")
    )

    creator = relationship("User", back_populates="geofences")
    student_attendances: Mapped[list["AttendanceRecord"]] = relationship("AttendanceRecord", back_populates="geofence")
