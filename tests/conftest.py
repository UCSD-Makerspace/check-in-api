import os

_DUMMY_ENV = {
    "ACTIVITY_SHEET_URL": "https://dummy",
    "ACTIVITY_SHEET_TAB": "dummy",
    "USER_DB_NAME": "dummy",
    "USER_DB_TAB": "dummy",
    "WAIVER_DB_NAME": "dummy",
    "WAIVER_DB_TAB": "dummy",
    "REDIS_HOST": "localhost",
}
for _k, _v in _DUMMY_ENV.items():
    os.environ.setdefault(_k, _v)

from unittest.mock import patch

import fakeredis
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def fake_redis():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def client(fake_redis):
    with (
        patch("services.cache.get_redis", return_value=fake_redis),
        patch("services.cache.refresh"),
        patch("services.sheets.append_user_row"),
        patch("services.sheets.append_activity_row"),
        patch("services.ucsd.get_enrollment_terms", return_value=("FA20", "SP25")),
        patch("services.fabman.create_member"),
    ):
        from app import app
        with TestClient(app) as c:
            yield c, fake_redis
