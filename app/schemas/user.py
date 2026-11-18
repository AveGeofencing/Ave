from typing import Literal

from fastapi.params import Form
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreateModel(BaseModel):
    user_id: str | None = None
    email: EmailStr | None = None
    username: str = Field(min_length=1, max_length=60)
    user_matric: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    role: Literal["student"] = "student"
    department_id: int = Field(gt=0)
    model_config = ConfigDict(from_attributes=True)


class UserOutputModel(BaseModel):
    user_id: str
    email: EmailStr
    username: str
    user_matric: str
    role: str

    model_config = ConfigDict(from_attributes=True)


def user_create_form(
    username: str = Form(...),
    user_matric: str = Form(...),
    password: str = Form(...),
    department_id: int = Form(...),
) -> UserCreateModel:
    return UserCreateModel(
        email=None,
        user_id=None,
        username=username,
        user_matric=user_matric,
        password=password,
        department_id=department_id,
    )
