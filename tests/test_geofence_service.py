from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.schemas import AttendanceRecordModel, GeofenceCreateModel
from app.services.geofence import GeofenceService


class FakeConnection:
    def begin(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False


class FakeUserRepository:
    def __init__(self, user):
        self.user = user

    async def get_user_by_email_or_matric(self, **_):
        return self.user


class FakeGeofenceRepository:
    def __init__(self, geofence=None, existing_record=None):
        self.geofence = geofence
        self.existing_record = existing_record

    async def get_geofence_by_id(self, **_):
        return self.geofence

    async def get_attendance_record_for_student_for_geofence(self, **_):
        return self.existing_record

    async def create_geofence(self, **kwargs):
        return SimpleNamespace(id="fence-1", name=kwargs["geofence"].name)


def make_geofence(**overrides):
    now = datetime.now(UTC)
    values = {
        "fence_code": "abc123",
        "status": "active",
        "latitude": 6.5244,
        "longitude": 3.3792,
        "radius": 1_000,
        "name": "CSC 101",
        "start_time": now - timedelta(hours=1),
        "end_time": now + timedelta(hours=1),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def make_attendance(**overrides):
    values = {
        "geofence_id": "fence-1",
        "lat": 6.5244,
        "long": 3.3792,
        "fence_code": "abc123",
        "liveness_session_id": "session-1",
    }
    values.update(overrides)
    return AttendanceRecordModel(**values)


def make_service(user=None, geofence=None, existing_record=None):
    return GeofenceService(
        geofence_repository=FakeGeofenceRepository(geofence, existing_record),
        user_repository=FakeUserRepository(user),
        conn=FakeConnection(),
    )


async def test_record_attendance_rejects_unknown_user():
    service = make_service(user=None)

    with pytest.raises(HTTPException) as exc:
        await service.record_geofence_attendance(make_attendance(), "MAT-001")

    assert exc.value.status_code == 404


async def test_record_attendance_rejects_unknown_geofence():
    service = make_service(user=SimpleNamespace(user_matric="MAT-001"), geofence=None)

    with pytest.raises(HTTPException) as exc:
        await service.record_geofence_attendance(make_attendance(), "MAT-001")

    assert exc.value.status_code == 404


async def test_record_attendance_rejects_invalid_fence_code():
    service = make_service(
        user=SimpleNamespace(user_matric="MAT-001"),
        geofence=make_geofence(),
    )

    with pytest.raises(HTTPException) as exc:
        await service.record_geofence_attendance(
            make_attendance(fence_code="wrong1"), "MAT-001"
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid fence code"


async def test_record_attendance_rejects_inactive_geofence():
    service = make_service(
        user=SimpleNamespace(user_matric="MAT-001"),
        geofence=make_geofence(status="inactive"),
    )

    with pytest.raises(HTTPException) as exc:
        await service.record_geofence_attendance(make_attendance(), "MAT-001")

    assert exc.value.status_code == 400


async def test_record_attendance_rejects_closed_time_window():
    now = datetime.now(UTC)
    service = make_service(
        user=SimpleNamespace(user_matric="MAT-001"),
        geofence=make_geofence(
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await service.record_geofence_attendance(make_attendance(), "MAT-001")

    assert exc.value.status_code == 400


async def test_record_attendance_rejects_duplicate_record():
    service = make_service(
        user=SimpleNamespace(user_matric="MAT-001"),
        geofence=make_geofence(),
        existing_record=object(),
    )

    with pytest.raises(HTTPException) as exc:
        await service.record_geofence_attendance(make_attendance(), "MAT-001")

    assert exc.value.status_code == 409


async def test_record_attendance_rejects_user_outside_geofence():
    service = make_service(
        user=SimpleNamespace(user_matric="MAT-001"),
        geofence=make_geofence(),
    )

    with pytest.raises(HTTPException) as exc:
        await service.record_geofence_attendance(
            make_attendance(lat=0, long=0), "MAT-001"
        )

    assert exc.value.status_code == 400


async def test_create_geofence_rejects_invalid_duration():
    now = datetime.now(UTC)
    service = make_service()
    geofence = GeofenceCreateModel(
        name="CSC 101",
        latitude=6.5,
        longitude=3.3,
        radius=100,
        fence_type="class",
        start_time=now + timedelta(hours=2),
        end_time=now + timedelta(hours=1),
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_geofence("MAT-001", geofence)

    assert exc.value.status_code == 400


async def test_create_geofence_rejects_past_end_time():
    now = datetime.now(UTC)
    service = make_service()
    geofence = GeofenceCreateModel(
        name="CSC 101",
        latitude=6.5,
        longitude=3.3,
        radius=100,
        fence_type="class",
        start_time=now - timedelta(hours=2),
        end_time=now - timedelta(hours=1),
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_geofence("MAT-001", geofence)

    assert exc.value.status_code == 400
