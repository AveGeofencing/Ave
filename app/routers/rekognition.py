from PIL import Image
import io
import boto3

from fastapi import HTTPException, APIRouter

router = APIRouter(prefix="/rekognition", tags=["Rekognition"])
rekognition = boto3.client("rekognition", region_name="us-east-1")


def get_image(image_bytes):

        # Convert to image
        image = Image.open(io.BytesIO(image_bytes))

        # Example: save it
        image.save("reference.jpg")


@router.post("/create-session")
def create_session():
    try:
        response = rekognition.create_face_liveness_session()
        return {"sessionId": response["SessionId"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-results/{session_id}")
def get_results(session_id: str):
    try:
        response = rekognition.get_face_liveness_session_results(
            SessionId=session_id
        )
        get_image(response["ReferenceImage"]["Bytes"])

        return {
            "status": response["Status"],
            "confidence": response.get("Confidence", 0),
            # "referenceImage": response.get("ReferenceImage", None),
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))