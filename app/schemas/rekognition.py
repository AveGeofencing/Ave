from pydantic import BaseModel
from typing import List, Dict, Optional


class BoundingBoxModel(BaseModel):
    Width: float
    Height: float
    Left: float
    Top: float


class AgeRangeModel(BaseModel):
    Low: int
    High: int


class AttributeBool(BaseModel):
    Value: bool
    Confidence: float


class GenderModel(BaseModel):
    Value: str
    Confidence: float


class Emotion(BaseModel):
    Type: str
    Confidence: float


class Landmark(BaseModel):
    Type: str
    X: float
    Y: float


class PoseModel(BaseModel):
    Roll: float
    Yaw: float
    Pitch: float


class ImageQuality(BaseModel):
    Brightness: float
    Sharpness: float


class EyeDirectionModel(BaseModel):
    Yaw: float
    Pitch: float
    Confidence: float


class FaceDetail(BaseModel):
    BoundingBox: BoundingBoxModel
    AgeRange: AgeRangeModel
    Smile: AttributeBool
    Eyeglasses: AttributeBool
    Sunglasses: AttributeBool
    Gender: GenderModel
    Beard: AttributeBool
    Mustache: AttributeBool
    EyesOpen: AttributeBool
    MouthOpen: AttributeBool
    Emotions: List[Emotion]
    Landmarks: List[Landmark]
    Pose: PoseModel
    Quality: ImageQuality
    Confidence: float
    FaceOccluded: AttributeBool
    EyeDirection: EyeDirectionModel


class ResponseMetadataModel(BaseModel):
    RequestId: str
    HTTPStatusCode: int
    HTTPHeaders: Dict[str, str]
    RetryAttempts: int


class QualityModel(BaseModel):
    Brightness: float
    Sharpness: float


class FaceModel(BaseModel):
    BoundingBox: BoundingBoxModel
    Confidence: float
    Landmarks: List[Landmark]
    Pose: PoseModel
    Quality: QualityModel


class FaceMatch(BaseModel):
    Face: FaceModel
    Similarity: float


class SourceImageFaceModel(BaseModel):
    BoundingBox: BoundingBoxModel
    Confidence: float


class DetectFacesResponse(BaseModel):
    FaceDetails: List[FaceDetail]
    ResponseMetadata: ResponseMetadataModel


class CompareFacesResponse(BaseModel):
    FaceMatches: List[FaceMatch]
    SourceImageFace: Optional[SourceImageFaceModel]
    UnmatchedFaces: List[FaceModel]  # can be empty
    ResponseMetadata: ResponseMetadataModel

from pydantic import BaseModel
from typing import Literal


class S3ObjectModel(BaseModel):
    Bucket: str
    Name: str
    Version: str

class ReferenceImageModel(BaseModel):
    Bytes: bytes | None = None
    S3Object: S3ObjectModel | None = None
    BoundingBox: BoundingBoxModel | None = None


class ChallengeModel(BaseModel):
    Type: Literal["FaceMovementAndLightChallenge", "FaceMovementChallenge"]
    Version: str


class FaceLivenessSessionResult(BaseModel):
    SessionId: str
    Status: Literal["CREATED", "IN_PROGRESS", "SUCCEEDED", "FAILED", "EXPIRED"]
    Confidence: float | None = None
    ReferenceImage: ReferenceImageModel | None = None
    AuditImages: list[ReferenceImage] | None = None
    Challenge: ChallengeModel | None = None