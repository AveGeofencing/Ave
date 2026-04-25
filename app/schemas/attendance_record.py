from datetime import datetime

from pydantic import BaseModel


class AttendanceRecordModel(BaseModel):
    geofence_id: str
    lat: float
    long: float
    fence_code: str
    liveness_session_id: str


class AttendanceRecordOut(BaseModel):
    username: str
    user_matric: str
    timestamp: datetime
