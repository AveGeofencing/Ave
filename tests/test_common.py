from starlette.responses import Response

from app.common import hash_password, is_password_correct, set_custom_cookie
from app.settings import APP_SETTINGS


def test_password_hash_round_trip():
    hashed = hash_password("correct-horse-battery")

    assert hashed != "correct-horse-battery"
    assert is_password_correct(hashed, "correct-horse-battery")
    assert not is_password_correct(hashed, "wrong-password")


def test_custom_cookie_uses_security_settings():
    response = Response()

    set_custom_cookie(response, key="refresh_token", value="token", path="/", max_age=60)

    header = response.headers["set-cookie"]
    assert "refresh_token=token" in header
    assert "HttpOnly" in header
    assert f"SameSite={APP_SETTINGS.COOKIE_SAMESITE}" in header
