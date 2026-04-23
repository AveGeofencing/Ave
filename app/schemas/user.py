from fastapi.params import Form
from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreateModel(BaseModel):
    user_id: str
    email: EmailStr
    username: str
    user_matric: str
    password: str
    role: str
    department_id: int
    model_config = ConfigDict(from_attributes=True)

class UserOutputModel(BaseModel):
    user_id: str
    email: str
    username: str
    user_matric: str
    role: str

    model_config = ConfigDict(from_attributes=True)

def user_create_form(
        user_id: str = Form(...),
        email: EmailStr = Form(...),
        username: str = Form(...),
        user_matric: str = Form(...),
        password: str = Form(...),
        role: str = Form(...),
        department_id: int = Form(...)
) -> UserCreateModel:
    return UserCreateModel(
        user_id=user_id,
        email=email,
        username=username,
        user_matric=user_matric,
        password=password,
        role=role,
        department_id=department_id,
    )
