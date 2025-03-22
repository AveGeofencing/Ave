from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreateModel(BaseModel):
    email: EmailStr
    username: str
    user_matric: str
    password: str
    role: str
    verification_code: str

    model_config = ConfigDict(from_attributes=True)
