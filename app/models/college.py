from typing import TYPE_CHECKING, List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .department import Department

class College(Base):
    __tablename__ =  "college"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)

    departments: Mapped[List["Department"]] = relationship("Department", back_populates="college")