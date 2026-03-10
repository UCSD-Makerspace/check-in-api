import os
import time
from typing import Optional

import requests
from authlib.integrations.requests_client import OAuth2Session

UCSD_API_URL = os.environ.get("UCSD_API_URL", "")
DEV_MODE = os.environ.get("DEV_MODE", "").lower() == "true"

_ucsd_client: Optional[OAuth2Session] = None
_ucsd_token: Optional[dict] = None


def get_token() -> str:
    global _ucsd_client, _ucsd_token
    if _ucsd_client is None:
        _ucsd_client = OAuth2Session(
            os.environ["UCSD_CLIENT_ID"],
            os.environ["UCSD_CLIENT_SECRET"],
            token_url=UCSD_API_URL + "token",
        )
        _ucsd_token = _ucsd_client.fetch_token(UCSD_API_URL + "token", grant_type="client_credentials")
    elif _ucsd_token["expires_at"] < time.time() + 60:
        _ucsd_token = _ucsd_client.fetch_token(UCSD_API_URL + "token", grant_type="client_credentials")
    return _ucsd_token["access_token"]


def safe_get(url: str, retries: int = 2) -> Optional[requests.Response]:
    token = get_token()
    for _ in range(retries):
        try:
            resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=4)
            if resp.ok:
                return resp
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            pass
        time.sleep(0.5)
    return None


def _parse_student(data: dict, pid: str) -> dict:
    return {
        "pid": pid,
        "first_name": data["name"]["firstName"],
        "last_name": data["name"]["lastName"],
        "emails": [e["emailAddress"] for e in data["emailAddressList"]],
        "first_enr_term": data["name"]["firstEnrTrm"],
        "last_enr_term": data["name"]["lastEnrTrm"],
    }


def fetch_student_by_pid(pid: str) -> Optional[dict]:
    if DEV_MODE:
        return {
            "pid": pid,
            "first_name": "Dev",
            "last_name": "User",
            "emails": ["devuser@ucsd.edu"],
            "first_enr_term": "FA20",
            "last_enr_term": "SP25",
        }
    resp = safe_get(
        f"{UCSD_API_URL}student_contact_info/v1/students/contactinfo_by_pids?studentIds={pid}"
    )
    if not resp or not resp.json():
        return None
    return _parse_student(resp.json()[0], pid)


def get_enrollment_terms(student_id: str) -> tuple[str, str]:
    if DEV_MODE:
        return "FA20", "SP25"
    normalized = "A" + student_id.strip().lower().lstrip("a")
    student = fetch_student_by_pid(normalized)
    if student is None:
        return "", ""
    return student["first_enr_term"], student["last_enr_term"]
