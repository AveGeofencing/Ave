from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.schemas import AttendanceRecordModel, GeofenceCreateModel, UserCreateModel


def test_user_signup_cannot_assign_admin_role():
    with pytest.raises(ValidationError):
        UserCreateModel(
            username="student",
            user_matric="MAT-001",
            password="correct-horse-battery",
            role="admin",
            department_id=1,
        )


def test_user_signup_rejects_short_password():
    with pytest.raises(ValidationError):
        UserCreateModel(
            username="student",
            user_matric="MAT-001",
            password="short",
            department_id=1,
        )


def test_geofence_requires_timezone_aware_times():
    now = datetime.now(UTC)

    with pytest.raises(ValidationError):
        GeofenceCreateModel(
            name="CSC 101",
            latitude=6.5,
            longitude=3.3,
            radius=100,
            fence_type="class",
            start_time=now.replace(tzinfo=None),
            end_time=now + timedelta(hours=1),
        )


def test_geofence_rejects_invalid_coordinates():
    now = datetime.now(UTC)

    with pytest.raises(ValidationError):
        GeofenceCreateModel(
            name="CSC 101",
            latitude=100,
            longitude=3.3,
            radius=100,
            fence_type="class",
            start_time=now,
            end_time=now + timedelta(hours=1),
        )


def test_attendance_rejects_invalid_coordinates():
    with pytest.raises(ValidationError):
        AttendanceRecordModel(
            geofence_id="fence-1",
            lat=91,
            long=3.3,
            fence_code="abc123",
            liveness_session_id="session-1",
        )
