import string
from typing import Annotated

from fastapi.params import Depends
from pynanoid import generate
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from starlette.responses import Response

from .utils import logger

ph: PasswordHasher = PasswordHasher()

def generate_id(size: int = 10):
    alphabet = string.ascii_letters + string.digits
    return generate(alphabet=alphabet, size=size)

def hash_password(password: str) -> str:
    return ph.hash(password)

def is_password_correct(user_password: str, supplied_password: str) -> bool:
    try:
        if ph.verify(user_password, supplied_password):
            return True
    except VerifyMismatchError as e:
        logger.error(f"Invalid Password: {e}")
    return False

def set_custom_cookie(
    response: Response,
    key: str,
    value: str,
    path: str | None = None,
    max_age: int | None = None,
) -> None:
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=True,
        samesite="none",
        path=path,
        max_age=max_age,
    )

