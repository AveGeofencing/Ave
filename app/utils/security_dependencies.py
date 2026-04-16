from typing import Annotated

from fastapi import HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer
from starlette import status

from app.exceptions import InvalidTokenError
from app.infra.token_utils import AccessToken
from app.schemas import UserOutputModel

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: Annotated[str, Depends(oauth_scheme)],
) -> UserOutputModel:
    """
    Gets its token parameter from a FastAPI Dependency that checks the request for an "Authorization" header
    :param token:
    :return: user_data: str
    """
    try:
        payload: UserOutputModel = await AccessToken.decode(token)
        return payload
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired.")

async def authenticate_student_user(
    user_data: UserOutputModel = Depends(get_current_user),
) -> UserOutputModel:
    if not user_data:
        raise HTTPException(status_code=404, detail="Session expired.")

    if user_data.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Endpoint can only be accessed by students"
        )

    return user_data

async def authenticate_admin_user(
    user_data: UserOutputModel = Depends(get_current_user),
) -> UserOutputModel:
    if not user_data:
        raise HTTPException(status_code=401, detail="Session expired.")
    if user_data.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Endpoint can only be accessed by admins"
        )

    return user_data