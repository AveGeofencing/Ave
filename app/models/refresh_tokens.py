import datetime
from zoneinfo import ZoneInfo

import uuid
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing_extensions import TYPE_CHECKING
from uuid import UUID

from ..common import generate_id
from ..database import Base

if TYPE_CHECKING:
    from .user import User

class Token(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=generate_id)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.datetime.now(tz=ZoneInfo("UTC")),
    )
    user_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    jti: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, default=uuid.uuid4
    )
