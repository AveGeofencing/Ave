from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Department(Base):
    __tablename__ =  "department"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    college_id: Mapped[int] = mapped_column(ForeignKey("college.id"))