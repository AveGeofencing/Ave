from datetime import datetime

from pydantic import BaseModel, Field


class AttendanceRecordModel(BaseModel):
    geofence_id: str = Field(min_length=1, max_length=255)
    lat: float = Field(ge=-90, le=90)
    long: float = Field(ge=-180, le=180)
    fence_code: str = Field(min_length=1, max_length=15)
    liveness_session_id: str = Field(min_length=1, max_length=255)


class AttendanceRecordOut(BaseModel):
    username: str
    user_matric: str
    timestamp: datetime
