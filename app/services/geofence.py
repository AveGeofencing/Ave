from datetime import datetime
import random
import string
from typing import Annotated, Dict, Sequence
from zoneinfo import ZoneInfo

import boto3
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ..database import get_db_session
from ..models import AttendanceRecord
from ..schemas import GeofenceCreateModel, AttendanceRecordModel
from ..repositories import GeofenceRepository, UserRepository
from ..schemas.geofence import GeofenceOutputModel
from ..schemas.rekognition import CompareFacesResponse, FaceLivenessSessionResult
from ..utils import check_user_in_circular_geofence, logger

rekognition_client = boto3.client("rekognition", region_name="us-east-1")
s3_client = boto3.client("s3", region_name="eu-west-2")


class GeofenceService:
    def __init__(
        self,
        geofence_repository: Annotated[GeofenceRepository, Depends()],
        user_repository: Annotated[UserRepository, Depends()],
        conn: Annotated[AsyncSession, Depends(get_db_session)]
    ):
        self.geofence_repo: GeofenceRepository = geofence_repository
        self.user_repo: UserRepository = user_repository
        self.conn: AsyncSession = conn

    async def create_geofence(
        self,
        creator_matric: str,
        geofence: GeofenceCreateModel,
    ):  # SINGULAR
        async with self.conn.begin():
            characters = string.ascii_letters + string.digits
            fence_code = "".join(random.choice(characters) for _ in range(6)).lower()

            #TODO: Add check for existing geofence
            # existing_geofence = await self.geofence_repo.get_geofence(
            #     course_title=geofence.name, date=geofence.start_time, conn=self.conn
            # )
            #
            # if existing_geofence:
            #     raise HTTPException(
            #         status_code=status.HTTP_409_CONFLICT,
            #         detail=f"Geofence '{geofence.name}' already exist for today"
            #     )

            start_time_utc = geofence.start_time.astimezone(ZoneInfo("UTC"))
            end_time_utc = geofence.end_time.astimezone(ZoneInfo("UTC"))
            NOW = datetime.now(ZoneInfo("UTC"))

            if start_time_utc >= end_time_utc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid duration for geofence. Please adjust duration and try again."
                )

            if end_time_utc < NOW:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="End time cannot be in the past."
                )

            added_geofence = await self.geofence_repo.create_geofence(
                conn=self.conn,
                geofence=geofence,
                fence_code=fence_code,
                creator_matric=creator_matric,
                start_time_utc=start_time_utc,
                end_time_utc=end_time_utc,
                now=NOW
            )

            return {"id": added_geofence.id ,"code": fence_code, "name": added_geofence.name}


    async def get_all_geofences(
        self, user_matric: str
    ) -> Dict[str, list[ None | GeofenceOutputModel ]]:
        geofences = await self.geofence_repo.get_all_geofences(conn=self.conn)

        return {
            "geofences": [
                GeofenceOutputModel(
                    id=geofence.id,
                    name=geofence.name,
                    status=geofence.status,
                    latitude=geofence.latitude,
                    longitude=geofence.longitude,
                    radius=geofence.radius,
                    fence_type=geofence.fence_type,
                    start_time=geofence.start_time,
                    end_time=geofence.end_time,
                    has_registered=user_matric in {attendance.user_matric for attendance in geofence.student_attendances}
                )
                for geofence in geofences
            ]
        }

    async def get_all_my_geofences(
        self, user_matric: str
    ) -> list[
        None | GeofenceOutputModel
    ]:
        geofences = await self.geofence_repo.get_all_geofences_by_user(
            user_matric=user_matric, conn=self.conn
        )

        return [
                GeofenceOutputModel(
                    id=geofence.id,
                    name=geofence.name,
                    status=geofence.status,
                    latitude=geofence.latitude,
                    longitude=geofence.longitude,
                    radius=geofence.radius,
                    fence_type=geofence.fence_type,
                    start_time=geofence.start_time,
                    end_time=geofence.end_time,
                    fence_code=geofence.fence_code,
                )
                for geofence in geofences
            ]


    async def get_geofence(
        self, geofence_id: str,
    ):  # SINGULAR
        geofence = await self.geofence_repo.get_geofence(geofence_id=geofence_id, conn=self.conn)
        if not geofence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Geofence not found.")

        return GeofenceOutputModel(
            id=geofence.id,
            name=geofence.name,
            status=geofence.status,
            latitude=geofence.latitude,
            longitude=geofence.longitude,
            radius=geofence.radius,
            fence_type=geofence.fence_type,
            start_time=geofence.start_time,
            end_time=geofence.end_time,
            fence_code=geofence.fence_code,
        )


    async def get_geofence_by_fence_code(self, fence_code: str):
        geofence = await self.geofence_repo.get_geofence_by_fence_code(
            fence_code=fence_code, conn=self.conn
        )
        if not geofence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Geofence not found.")

        return geofence


    async def get_geofence_attendances(
        self, fence_id: str, user_id: str
    ) ->  list[AttendanceRecordModel | None]:
        geofence = await self.geofence_repo.get_geofence_by_id(
            geofence_id=fence_id, conn=self.conn
        )
        if not geofence:
            raise HTTPException(
                status_code=404,
                detail=f"Geofence not found",
            )

        if geofence.creator_matric != user_id:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to view this geofence's attendance.",
            )

        attendance_list = []
        attendances: Sequence[AttendanceRecord] = await self.geofence_repo.get_geofence_attendances(
            fence_code=geofence.fence_code, conn=self.conn
        )

        if attendances:
            for attendance in attendances:
                attendance_list.append(
                    {
                        "user_matric": attendance.user_matric,
                        "username": attendance.user.username,
                        "timestamp": attendance.timestamp,
                    }
                )

        return attendance_list


    async def record_geofence_attendance(
        self,
        attendance: AttendanceRecordModel,
        user_matric: str,
    ):
        async with self.conn.begin():
            user = await self.user_repo.get_user_by_email_or_matric(matric=user_matric, conn=self.conn)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

            try:
                response = rekognition_client.get_face_liveness_session_results(SessionId=attendance.liveness_session_id)
                formatted_liveness_response: FaceLivenessSessionResult = FaceLivenessSessionResult.model_validate(response)
            except Exception as e:
                logger.error(e)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error verifying liveness")

            if formatted_liveness_response.Status != "SUCCEEDED":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error verifying liveness")

            logger.debug(f"Confidence in user liveness: {formatted_liveness_response.Confidence}")

            liveness_threshold = 70
            if formatted_liveness_response.Confidence < liveness_threshold:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="There might not be a real user in the video feed. Try again")


            reference_image = formatted_liveness_response.ReferenceImage
            if not reference_image:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error verifying liveness")

            s3_key = f"base_user_reference_photos/users/{user.user_matric}/profile_photo.jpg"

            try:
                s3_object = s3_client.get_object(Bucket="ave-base-bucket", Key=s3_key)
                source_bytes = s3_object["Body"].read()

                similarity_threshold = 80
                compare_faces_response = rekognition_client.compare_faces(
                    TargetImage={"Bytes": reference_image.Bytes},
                    SourceImage={"Bytes": source_bytes},
                    SimilarityThreshold=similarity_threshold,
                )
            except Exception as e:
                logger.error(f"Error verifying face: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="Facial verification failed")

            formated_compare_faces_response: CompareFacesResponse = CompareFacesResponse.model_validate(
                compare_faces_response
            )
            if not formated_compare_faces_response.FaceMatches:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Facial verification failed")

            if len(formated_compare_faces_response.FaceMatches) > 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Too many faces in the captured video feed. Try again")

            logger.debug(f"Similarity threshold for user: {user.user_matric} - {formated_compare_faces_response.FaceMatches[0].Similarity}")

            if formated_compare_faces_response.FaceMatches[0].Similarity < similarity_threshold:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Facial verification failed")


            geofence = await self.geofence_repo.get_geofence_by_id(
                geofence_id=attendance.geofence_id, conn=self.conn
            )

            if not geofence:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Geofence does not exist",
                )

            if not geofence.fence_code == attendance.fence_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid fence code",
                )

            if geofence.status.lower() != "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Geofence is not active for attendance."
                )

            matric_fence_code = geofence.fence_code + user.user_matric
            existing_record = await self.geofence_repo.get_attendance_record_for_student_for_geofence(
                user_matric=user.user_matric, fence_code=geofence.fence_code, conn=self.conn
            )

            if existing_record:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You have already recorded attendance for this class",
                )

            if not check_user_in_circular_geofence(
                attendance.lat, attendance.long, geofence
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is not within geofence, attendance not recorded",
                )

            await self.geofence_repo.record_geofence_attendance(
                attendance=attendance,
                user_matric=user.user_matric,
                geofence_name=geofence.name,
                matric_fence_code=matric_fence_code,
                conn=self.conn
            )

            return {"message": "Attendance recorded successfully"}


    async def deactivate_geofence(
        self, geofence_id: str, user_matric: str
    ):
        async with self.conn.begin():
            geofence = await self.geofence_repo.get_geofence(geofence_id=geofence_id, conn=self.conn)

            if geofence is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"Geofence not found."
                )
            if user_matric != geofence.creator_matric:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this class as you are not the creator.",
                )

            if geofence.status == "inactive":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Geofence is already inactive")

            await self.geofence_repo.deactivate_geofence(
                fence_id=geofence.id, conn=self.conn
            )
            return {"message": "Geofence deactivated successfully"}


