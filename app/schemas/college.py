from typing import List

from pydantic import BaseModel


class DepartmentSchema(BaseModel):
    id: int
    name: str

class CollegeSchema(BaseModel):
    id: int
    name: str
    departments: List[DepartmentSchema]