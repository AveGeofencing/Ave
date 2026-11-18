import uuid
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from ..common import generate_id
from ..database import Base


class Token(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=generate_id)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(tz=ZoneInfo("UTC")),
    )
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    jti: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, default=uuid.uuid4
    )
