from fastapi import HTTPException
import pytest
from unittest.mock import AsyncMock

from ..services import UserService
from ..exceptions import *
from ..schemas import UserCreateModel


@pytest.mark.asyncio
async def test_user_already_exists():
    mock_user_repo = AsyncMock()
    mock_user_repo.get_user_by_email_or_matric.return_value = {
        "email": "test@example.com",
        "user_matric": "2021/10097",
    }

    user_service = UserService(user_repository=mock_user_repo)

    user_data = UserCreateModel(
        email="test@example.com",
        username="Adedara",
        user_matric="2021/10097",
        password="test",
        role="admin",
        verification_code="120202",
    )

    with pytest.raises(
        HTTPException,
        match="User with this email or matric number already exists",
    ):
        await user_service.create_new_user(user_data)


@pytest.mark.asyncio

async def test_invalid_verification_code():
    mock_user_repo = AsyncMock()
    mock_user_repo.get_user_by_email_or_matric.return_value = None

    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = "120201"

    user_service = UserService(
        user_repository=mock_user_repo,
        redis_client=mock_redis_client,
    )
    user_data = UserCreateModel(
        email="test@example.com",
        username="Adedara",
        user_matric="2021/10097",
        password="testtesttest",
        role="admin",
        verification_code="120202"
    )

    with pytest.raises(
        HTTPException,
        match="Invalid verification code",
    ):
        await user_service.create_new_user(user_data)
