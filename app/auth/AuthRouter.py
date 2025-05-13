import logging
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from typing import Annotated

from .sessions import SessionHandler, get_session_handler
from .APIKeys import get_api_key
from ..utils.config import get_app_settings

from passlib.context import CryptContext


AuthRouter = APIRouter(prefix="/auth", tags=["auth"])
# Dependency
password_request_form = Annotated[OAuth2PasswordRequestForm, Depends()]
api_key_dependency = Annotated[str, Depends(get_api_key)]
SessionHandlerDependency = Annotated[SessionHandler, Depends(get_session_handler)]
settings = get_app_settings()

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SESSION_TIMEOUT_MINUTES = 24 * 60

logger = logging.getLogger("uvicorn")


@AuthRouter.post("/token", dependencies=[Depends(get_api_key)])
async def login(
    response: Response,
    form_data: password_request_form,
    session_handler: SessionHandlerDependency,
):

    user_login_response = await session_handler.login(
        user_matric=form_data.username,
        email=form_data.username,
        password=form_data.password,
    )

    session_token = user_login_response["session_token"]
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        # domain=settings.COOKIE_DOMAIN,
        secure=True,  # Set to True for HTTPS
        samesite="none",
        max_age=SESSION_TIMEOUT_MINUTES * 60,
    )

    return user_login_response


@AuthRouter.delete("/logout")
async def logout(
    request: Request, response: Response, session_handler: SessionHandlerDependency
) -> dict:
    """
    This function handles the logout process for a user. It retrieves the session token from the request cookies,
    checks if it exists, and then deactivates the session using the SessionHandler.

    Parameters:
    - request (Request): The FastAPI Request object containing the cookies.

    Returns:
    - dict: A dictionary containing a message indicating the logout status.
    """
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="No session token provided.")

    log_out_message = await session_handler.deactivate_session(session_token)

    response.delete_cookie("session_token")
    return {"message": log_out_message}


@AuthRouter.get("/get_user_by_token")
async def get_user_by_session_token(
    request: Request, session_handler: SessionHandlerDependency
):
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=401, detail="No session token provided")

    user_data = await session_handler.get_user_by_session(session_token)

    if not user_data:
        raise HTTPException(status_code=401, detail="Session expired")
    return user_data
