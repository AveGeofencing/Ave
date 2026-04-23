from pydantic import BaseModel
from typing import List, Dict


class BoundingBox(BaseModel):
    Width: float
    Height: float
    Left: float
    Top: float


class AgeRange(BaseModel):
    Low: int
    High: int


class AttributeBool(BaseModel):
    Value: bool
    Confidence: float


class Gender(BaseModel):
    Value: str
    Confidence: float


class Emotion(BaseModel):
    Type: str
    Confidence: float


class Landmark(BaseModel):
    Type: str
    X: float
    Y: float


class Pose(BaseModel):
    Roll: float
    Yaw: float
    Pitch: float


class ImageQuality(BaseModel):
    Brightness: float
    Sharpness: float


class EyeDirection(BaseModel):
    Yaw: float
    Pitch: float
    Confidence: float


class FaceDetail(BaseModel):
    BoundingBox: BoundingBox
    AgeRange: AgeRange
    Smile: AttributeBool
    Eyeglasses: AttributeBool
    Sunglasses: AttributeBool
    Gender: Gender
    Beard: AttributeBool
    Mustache: AttributeBool
    EyesOpen: AttributeBool
    MouthOpen: AttributeBool
    Emotions: List[Emotion]
    Landmarks: List[Landmark]
    Pose: Pose
    Quality: ImageQuality
    Confidence: float
    FaceOccluded: AttributeBool
    EyeDirection: EyeDirection


class ResponseMetadata(BaseModel):
    RequestId: str
    HTTPStatusCode: int
    HTTPHeaders: Dict[str, str]
    RetryAttempts: int


class RekognitionResponse(BaseModel):
    FaceDetails: List[FaceDetail]
    ResponseMetadata: ResponseMetadata