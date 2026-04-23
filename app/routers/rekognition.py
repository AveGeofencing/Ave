import boto3

from fastapi import HTTPException, APIRouter
from fastapi.params import Depends
from typing import Annotated

from app.schemas import UserOutputModel
from app.services import UserService
from app.utils.security_dependencies import get_current_user

router = APIRouter(prefix="/rekognition", tags=["Rekognition"])
rekognition = boto3.client("rekognition", region_name="us-east-1")

@router.post("/create-session")
async def create_session(_: Annotated[UserOutputModel, Depends(get_current_user)]):
    try:
        response = rekognition.create_face_liveness_session()
        return {"sessionId": response["SessionId"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-results/{session_id}")
async def get_results(
        session_id: str,
        user: Annotated[UserOutputModel, Depends(get_current_user)],
        user_service: Annotated[UserService, Depends()]
):
    return await user_service.compare_and_verify_face(
        user=user,
        session_id=session_id
    )