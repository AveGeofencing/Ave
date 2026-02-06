from datetime import datetime
from sqlalchemy import TIMESTAMP, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..common import generate_id
from ..database import Base


class PasswordResetToken(Base):
    __tablename__ = "passwordresettokens"

    id: Mapped[str] = mapped_column(Integer, primary_key=True, index=True, default=generate_id)
    user_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.user_matric"), nullable=False
    )  # Link to the user
    token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )  # The reset token
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )  # Token expiration time
    is_used: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # Whether the token has been used

    user = relationship("User", back_populates="password_reset_tokens")
