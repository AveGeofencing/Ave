from pydantic import BaseModel, ConfigDict, Field, AwareDatetime


class GeofenceCreateModel(BaseModel):
    name: str
    latitude: float
    longitude: float
    radius: float
    fence_type: str
    start_time: AwareDatetime
    end_time: AwareDatetime

    model_config = ConfigDict(from_attributes=True)

