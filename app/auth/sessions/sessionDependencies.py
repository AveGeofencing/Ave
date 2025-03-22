from typing import Annotated
from fastapi import Depends, Request, HTTPException
from . import SessionHandler, get_session_handler


def get_session_id(request: Request):
    session_token = request.cookies.get("session_token")
    if session_token is None:
        raise HTTPException(status_code=401, detail="Session has expired. Log in again")

    return session_token


async def authenticate_user_by_session_token(
    session_handler: Annotated[SessionHandler, Depends(get_session_handler)],
    session_token: str = Depends(get_session_id),
):
    if not session_token:
        raise HTTPException(status_code=401, detail="No session token provided")

    user_data = await session_handler.get_user_by_session(session_token)

    return user_data


async def authenticate_student_user(
    user_data: dict = Depends(authenticate_user_by_session_token),
) -> dict:
    if not user_data:
        raise HTTPException(status_code=404, detail="No session token. Login again")

    if user_data["role"] != "student":
        raise HTTPException(
            status_code=401, detail="Endpoint can only be accessed by students"
        )

    return user_data


async def authenticate_admin_user(
    user_data: dict = Depends(authenticate_user_by_session_token),
) -> dict:
    if not user_data:
        raise HTTPException(status_code=401, detail="No session token. Login again")
    if user_data["role"] != "admin":
        raise HTTPException(
            status_code=401, detail="Endpoint can only be accessed by admins"
        )

    return user_data
