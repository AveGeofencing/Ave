from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    user_matric: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(60), unique=True)
    is_email_verified: Mapped[str] = mapped_column(Boolean(False))
    username: Mapped[str] = mapped_column(String(60))
    hashed_password: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(15))

    geofences = relationship("Geofence", back_populates="creator")
    sessions = relationship("Session", back_populates="user")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user")
    attendances = relationship("AttendanceRecord", back_populates="user")
