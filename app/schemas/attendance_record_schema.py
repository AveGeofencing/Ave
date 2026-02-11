from pydantic import BaseModel


class AttendanceRecordModel(BaseModel):
    lat: float
    long: float
    fence_code: str


class AttendanceRecordOut(BaseModel):
    username: str
    user_matric: str
    fence_code: str
