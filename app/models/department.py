from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .college import College

class Department(Base):
    __tablename__ =  "department"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    college_id: Mapped[int] = mapped_column(ForeignKey("college.id"))

    college: Mapped["College"] = relationship("College", back_populates="departments")