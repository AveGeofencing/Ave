from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, AwareDatetime


class GeofenceCreateModel(BaseModel):
    name: str
    latitude: float
    longitude: float
    radius: float
    fence_type: str
    start_time: datetime
    end_time: datetime

    model_config = ConfigDict(from_attributes=True)

class GeofenceOutputModel(BaseModel):
    id: str
    name: str
    status: str
    latitude: float
    longitude: float
    radius: float
    fence_type: str
    fence_code: Optional[str] = None
    start_time: datetime
    end_time: datetime
    has_registered: bool = False
    attendances: list | None = []
