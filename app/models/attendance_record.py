from datetime import datetime
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import mapped_column, Mapped, relationship

from ..common import generate_id
from ..database import Base


class AttendanceRecord(Base):
    __tablename__ = "attendancerecords"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_id)
    user_matric: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.user_matric", ondelete="CASCADE", onupdate="CASCADE")
    )
    fence_code: Mapped[str] = mapped_column(
        String(15), ForeignKey("geofences.fence_code", ondelete="CASCADE", onupdate="CASCADE")
    )
    geofence_name: Mapped[str] = mapped_column(String(60))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    matric_fence_code: Mapped[str] = mapped_column(String(60))

    user = relationship("User", back_populates="attendances")
    geofence = relationship("Geofence", back_populates="student_attendances")
