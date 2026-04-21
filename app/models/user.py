from sqlalchemy import Boolean, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..common import generate_id
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_id)
    user_matric: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(60), unique=True)
    username: Mapped[str] = mapped_column(String(60))
    hashed_password: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(15))
    department_id: Mapped[int] = mapped_column(ForeignKey("department.id"))
    bucket_image_key: Mapped[str] = mapped_column(String(255), nullable=False)

    geofences = relationship("Geofence", back_populates="creator")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user")
    attendances = relationship("AttendanceRecord", back_populates="user")
