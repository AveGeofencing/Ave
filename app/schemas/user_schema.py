from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreateModel(BaseModel):
    email: EmailStr
    username: str
    user_matric: str
    password: str
    role: str

    model_config = ConfigDict(from_attributes=True)

class UserOutputModel(BaseModel):
    user_id: str
    email: str
    username: str
    user_matric: str
    role: str

    model_config = ConfigDict(from_attributes=True)