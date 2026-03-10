import time
from unittest.mock import patch

PAYLOAD = {
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jdoe@ucsd.edu",
    "pid": "A12345678",
    "rfid": "AABBCCDD",
}


def test_create_account_success(client):
    c, _ = client
    resp = c.post("/accounts", json=PAYLOAD)
    assert resp.status_code == 201
    assert resp.json() == {"status": "ok"}


def test_create_account_writes_to_sheets(client):
    c, _ = client
    with patch("services.sheets.append_user_row") as mock_sheet:
        resp = c.post("/accounts", json=PAYLOAD)
        assert resp.status_code == 201
        mock_sheet.assert_called_once()
        row = mock_sheet.call_args[0][0]
        assert row[0] == "Jane Doe"
        assert row[2] == PAYLOAD["rfid"]
        assert row[3] == PAYLOAD["pid"]
        assert row[5] == PAYLOAD["email"]


def test_create_account_updates_redis(client):
    c, _ = client
    c.post("/accounts", json=PAYLOAD)

    resp = c.get(f"/check-in/uuid/{PAYLOAD['rfid']}")
    assert resp.status_code == 200
    assert resp.json()["status"] != "no_account"


def test_create_account_sheets_failure_returns_502(client):
    c, _ = client
    with patch("services.sheets.append_user_row", side_effect=RuntimeError("sheets down")):
        resp = c.post("/accounts", json=PAYLOAD)
    assert resp.status_code == 502


def test_create_account_fires_fabman_async(client):
    c, _ = client
    with patch("services.fabman.create_member") as mock_fabman:
        resp = c.post("/accounts", json=PAYLOAD)
        assert resp.status_code == 201
        time.sleep(0.2)
        mock_fabman.assert_called_once_with(
            PAYLOAD["first_name"],
            PAYLOAD["last_name"],
            PAYLOAD["email"],
            PAYLOAD["rfid"],
        )
