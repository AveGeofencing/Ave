from typing import Annotated

from PIL import Image
import io
import boto3

from fastapi import HTTPException, APIRouter
from fastapi.params import Depends

from app.schemas import UserOutputModel
from app.utils.security_dependencies import get_current_user

router = APIRouter(prefix="/rekognition", tags=["Rekognition"])
rekognition = boto3.client("rekognition", region_name="us-east-1")

@router.post("/create-session")
def create_session(_: Annotated[UserOutputModel, Depends(get_current_user)]):
    try:
        response = rekognition.create_face_liveness_session()
        return {"sessionId": response["SessionId"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-results/{session_id}")
def get_results(session_id: str, _: Annotated[UserOutputModel, Depends(get_current_user)]):
    try:
        response = rekognition.get_face_liveness_session_results(
            SessionId=session_id
        )

        return {
            "status": response["Status"],
            "confidence": response.get("Confidence", 0),
            # "referenceImage": response.get("ReferenceImage", None),
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))