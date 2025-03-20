from pydantic import BaseModel, EmailStr


class UserCreateModel(BaseModel):
    email: EmailStr
    username: str
    user_matric: str
    password: str
    role: str
    verification_code: str

    class Config:
        from_attributes = True
