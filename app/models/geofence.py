from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String, Float, DateTime, func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..common import generate_id
from ..database import Base


class Geofence(Base):
    __tablename__ = "geofences"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_id)
    fence_code: Mapped[str] = mapped_column(String(15), unique=True)
    name: Mapped[str] = mapped_column(String(60))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    radius: Mapped[float] = mapped_column(Float)
    fence_type: Mapped[str] = mapped_column(String(60))
    start_time: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True))
    end_time: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True))
    status: Mapped[str] = mapped_column(String(60))
    time_created: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.now(tz=ZoneInfo("UTC"))
    )
    creator_matric: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.user_matric")
    )

    creator = relationship("User", back_populates="geofences")
    student_attendances = relationship("AttendanceRecord", back_populates="geofence")
