from datetime import datetime
from typing import Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class GeofenceCreateModel(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius: float = Field(gt=0, le=100_000)
    fence_type: str = Field(min_length=1, max_length=60)
    start_time: AwareDatetime
    end_time: AwareDatetime

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
    attendances: list = Field(default_factory=list)
