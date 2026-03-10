import time
from unittest.mock import patch

from helpers import seed_user, seed_waiver_by_pid, seed_waiver_by_email

UUID = "AABBCCDD"
PID = "A12345678"
NAME = "Jane Doe"
EMAIL = "jdoe@ucsd.edu"


def test_checkin_uuid_no_account(client):
    c, _ = client
    resp = c.get(f"/check-in/uuid/{UUID}")
    assert resp.status_code == 200
    assert resp.json() == {"status": "no_account"}


def test_checkin_uuid_no_waiver(client):
    c, r = client
    seed_user(r, UUID, PID, NAME, EMAIL)

    resp = c.get(f"/check-in/uuid/{UUID}")
    assert resp.status_code == 200
    assert resp.json() == {"status": "no_waiver", "name": NAME}


def test_checkin_uuid_ok_waiver_by_pid(client):
    c, r = client
    seed_user(r, UUID, PID, NAME, EMAIL)
    seed_waiver_by_pid(r, PID)

    resp = c.get(f"/check-in/uuid/{UUID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["name"] == NAME
    assert data["student_id"] == PID
    assert data["email"] == EMAIL
    assert data["first_enr_term"] == "FA20"
    assert data["last_enr_term"] == "SP25"


def test_checkin_uuid_ok_waiver_by_email(client):
    c, r = client
    seed_user(r, UUID, PID, NAME, EMAIL)
    seed_waiver_by_email(r, EMAIL)

    resp = c.get(f"/check-in/uuid/{UUID}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_checkin_pid_no_account(client):
    c, _ = client
    resp = c.get(f"/check-in/pid/{PID}")
    assert resp.status_code == 200
    assert resp.json() == {"status": "no_account"}


def test_checkin_pid_ok(client):
    c, r = client
    seed_user(r, UUID, PID, NAME, EMAIL)
    seed_waiver_by_pid(r, PID)

    resp = c.get(f"/check-in/pid/{PID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["name"] == NAME


def test_checkin_pid_normalizes_a_prefix(client):
    c, r = client
    seed_user(r, UUID, PID, NAME, EMAIL)
    seed_waiver_by_pid(r, PID)

    resp = c.get(f"/check-in/pid/a12345678")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_activity_dedup(client):
    c, r = client
    seed_user(r, UUID, PID, NAME, EMAIL)
    seed_waiver_by_pid(r, PID)

    with patch("services.sheets.append_activity_row") as mock_append:
        c.get(f"/check-in/uuid/{UUID}")
        c.get(f"/check-in/uuid/{UUID}")

        time.sleep(0.2)

        assert mock_append.call_count == 1
