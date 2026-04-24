from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from starlette.requests import Request
from starlette.responses import Response

from app.schemas import UserCreateModel, UserOutputModel
from app.schemas.user import user_create_form
from app.services import UserService
from app.utils.security_dependencies import get_current_user

router = APIRouter(
    prefix="/auth"
)

password_request_form = Annotated[OAuth2PasswordRequestForm, Depends()]

@router.post("/register")
async def register_user(email: str, user_service: Annotated[UserService, Depends()]):
    return await user_service.register_user(email=email)

@router.post("/verify-email")
async def verify_token(response: Response, token: str, user_service: Annotated[UserService, Depends()]):
    return await user_service.verify_token(verification_token=token, response=response)

@router.post("/create-user", status_code=status.HTTP_201_CREATED,)
async def create_user(
        request: Request,
        response: Response,
        user_service: Annotated[UserService, Depends()],
        user: UserCreateModel = Depends(user_create_form),
        photo_ref_upload: UploadFile = File(...)):

    signup_session_token = request.cookies.get("signup_session_token")
    return await user_service.create_new_user(
        response=response,
        user=user,
        photo_upload=photo_ref_upload,
        token=signup_session_token
    )

@router.post("/login")
async def login(
    user_service: Annotated[UserService, Depends()],
    form_data: password_request_form,
    response: Response,
):
    return await user_service.login(
        email=form_data.username,
        user_matric=form_data.username,
        password=form_data.password,
        response=response
    )

@router.delete("/logout")
async def logout(
        response: Response,
        request: Request,
        user_service: Annotated[UserService, Depends()]
):
    return await user_service.logout(response=response, request=request)

@router.post("/refresh")
async def refresh_token(
        user_service: Annotated[UserService, Depends()],
        request: Request,
        response: Response
):
    return await user_service.refresh_token(request=request, response=response)

@router.get("/get-user")
async def get_user(user: Annotated[UserOutputModel, Depends(get_current_user)]):
    return user