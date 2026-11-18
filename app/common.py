import string

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from pynanoid import generate
from starlette.responses import Response

from .settings import APP_SETTINGS
from .utils import logger

ph: PasswordHasher = PasswordHasher()


def generate_id(size: int = 10):
    alphabet = string.ascii_letters + string.digits
    return generate(alphabet=alphabet, size=size)


def hash_password(password: str) -> str:
    return ph.hash(password)


def is_password_correct(user_password: str, supplied_password: str) -> bool:
    try:
        return ph.verify(user_password, supplied_password)
    except VerificationError:
        logger.warning("Password verification failed")
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
        secure=APP_SETTINGS.COOKIE_SECURE,
        samesite=APP_SETTINGS.COOKIE_SAMESITE,
        domain=APP_SETTINGS.COOKIE_DOMAIN,
        path=path,
        max_age=max_age,
    )
