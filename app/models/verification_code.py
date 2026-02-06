from ..common import generate_id
from ..database import Base
from sqlalchemy.orm import Mapped, mapped_column

class VerificationCode(Base):
    __tablename__ = "verificationcodes"

    id: Mapped[str] = mapped_column(primary_key=True, default=generate_id)
    code: Mapped[str] = mapped_column(unique=True)
    user_id: Mapped[str] = mapped_column(unique=True)