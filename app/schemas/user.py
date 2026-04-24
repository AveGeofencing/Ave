from fastapi import HTTPException
from fastapi.params import Form
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from starlette import status


class UserCreateModel(BaseModel):
    user_id: str | None
    email: str | None
    username: str
    user_matric: str
    password: str
    role: str
    department_id: int
    model_config = ConfigDict(from_attributes=True)

    @field_validator("password")
    @classmethod
    def check_password_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v


class UserOutputModel(BaseModel):
    user_id: str
    email: str
    username: str
    user_matric: str
    role: str

    model_config = ConfigDict(from_attributes=True)

def user_create_form(
        username: str = Form(...),
        user_matric: str = Form(...),
        password: str = Form(...),
        role: str = Form(...),
        department_id: int = Form(...)
) -> UserCreateModel:
    return UserCreateModel(
        email=None,
        user_id=None,
        username=username,
        user_matric=user_matric,
        password=password,
        role=role,
        department_id=department_id,
    )
