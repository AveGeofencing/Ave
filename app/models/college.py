from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class College(Base):
    __tablename__ =  "college"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
