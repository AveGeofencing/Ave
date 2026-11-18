from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.utils import check_user_in_circular_geofence, generate_fence_code, is_geofence_open
from app.utils.geofence_utils import haversine


def test_haversine_known_distance():
    distance = haversine(6.5244, 3.3792, 6.6018, 3.3515)
    assert 8_000 < distance < 10_000


def test_check_user_in_circular_geofence():
    geofence = SimpleNamespace(latitude=6.5244, longitude=3.3792, radius=1_000)

    assert check_user_in_circular_geofence(6.5245, 3.3793, geofence)
    assert not check_user_in_circular_geofence(6.6018, 3.3515, geofence)


def test_generate_fence_code_is_six_lowercase_alphanumeric_characters():
    codes = {generate_fence_code() for _ in range(50)}

    assert len(codes) == 50
    assert all(len(code) == 6 for code in codes)
    assert all(code.islower() and code.isalnum() for code in codes)


def test_is_geofence_open_handles_timezones():
    now = datetime.now(UTC)

    assert is_geofence_open(now - timedelta(hours=1), now + timedelta(hours=1), now)
    assert not is_geofence_open(now + timedelta(hours=1), now + timedelta(hours=2), now)
    assert not is_geofence_open(now - timedelta(hours=2), now - timedelta(hours=1), now)
