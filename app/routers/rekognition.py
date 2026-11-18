from typing import Annotated

import boto3
from fastapi import APIRouter, Depends, HTTPException

from app.schemas import UserOutputModel
from app.settings import APP_SETTINGS
from app.utils import logger
from app.utils.security_dependencies import get_current_user

router = APIRouter(prefix="/rekognition", tags=["Rekognition"])
rekognition = boto3.client("rekognition", region_name=APP_SETTINGS.AWS_REGION)


@router.post("/create-session")
async def create_session(_: Annotated[UserOutputModel, Depends(get_current_user)]):
    try:
        response = rekognition.create_face_liveness_session()
        return {"sessionId": response["SessionId"]}
    except Exception:
        logger.exception("Failed to create Rekognition liveness session")
        raise HTTPException(status_code=500, detail="Unable to create liveness session")
