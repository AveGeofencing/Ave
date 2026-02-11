from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from ..settings import APP_SETTINGS
import logging

logger = logging.getLogger("uvicorn")

API_KEYS = APP_SETTINGS.API_KEYS.split(",")
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def get_api_key(
    api_key_header: str = Security(api_key_header),
) -> str:
    """Retrieve and validate an API key from the query parameters or HTTP header.

    Args:
        api_key_header: The API key passed in the HTTP header.

    Returns:
        The validated API key.

    Raises:
        HTTPException: If the API key is invalid or missing.
    """

    try:
        if api_key_header in API_KEYS:
            return api_key_header

        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API Key",
            )
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API Key",
        )
