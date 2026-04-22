from typing import Annotated

from fastapi import UploadFile
from fastapi.params import File
from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreateModel(BaseModel):
    user_id: str
    email: EmailStr
    username: str
    user_matric: str
    password: str
    role: str
    department_id: int
    photo_upload: Annotated[UploadFile, File()]
    model_config = ConfigDict(from_attributes=True)

class UserOutputModel(BaseModel):
    user_id: str
    email: str
    username: str
    user_matric: str
    role: str

    model_config = ConfigDict(from_attributes=True)