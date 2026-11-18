from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..common import generate_id
from ..database import Base


class UsedPasswordResetToken(Base):
    __tablename__ = "used_password_reset_tokens"

    id: Mapped[str] = mapped_column(primary_key=True, default=generate_id)
    value: Mapped[str] = mapped_column(String, unique=True)
