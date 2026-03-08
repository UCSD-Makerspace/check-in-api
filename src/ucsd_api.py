import os
import time
from typing import Optional

import requests
from authlib.integrations.requests_client import OAuth2Session
from fastapi import APIRouter, HTTPException

UCSD_API_URL = os.environ["UCSD_API_URL"]

_ucsd_client: Optional[OAuth2Session] = None
_ucsd_token: Optional[dict] = None

router = APIRouter()


def get_ucsd_token() -> str:
    global _ucsd_client, _ucsd_token
    if _ucsd_client is None:
        _ucsd_client = OAuth2Session(
            os.environ["UCSD_CLIENT_ID"],
            os.environ["UCSD_CLIENT_SECRET"],
            token_url=UCSD_API_URL + "token",
        )
        _ucsd_token = _ucsd_client.fetch_token(
            UCSD_API_URL + "token", grant_type="client_credentials"
        )
    elif _ucsd_token["expires_at"] < time.time() + 60:
        _ucsd_token = _ucsd_client.fetch_token(
            UCSD_API_URL + "token", grant_type="client_credentials"
        )
    return _ucsd_token["access_token"]


def ucsd_safe_get(url: str, retries: int = 2) -> Optional[requests.Response]:
    token = get_ucsd_token()
    for _ in range(retries):
        try:
            resp = requests.get(
                url, headers={"Authorization": f"Bearer {token}"}, timeout=4
            )
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


@router.get("/students/barcode/{barcode}")
def student_by_barcode(barcode: str):
    barcode_resp = ucsd_safe_get(
        f"{UCSD_API_URL}student_contact_info/v1/students/{barcode}/student_id"
    )
    if not barcode_resp:
        raise HTTPException(status_code=502, detail="UCSD API unavailable")
    if not barcode_resp.ok:
        raise HTTPException(status_code=404, detail="Student not found")

    pid = barcode_resp.json()["studentId"]
    resp = ucsd_safe_get(
        f"{UCSD_API_URL}student_contact_info/v1/students/contactinfo_by_pids?studentIds={pid}"
    )
    if not resp or not resp.ok:
        raise HTTPException(status_code=502, detail="UCSD API unavailable")
    return _parse_student(resp.json()[0], pid)


@router.get("/students/pid/{pid}")
def student_by_pid(pid: str):
    resp = ucsd_safe_get(
        f"{UCSD_API_URL}student_contact_info/v1/students/contactinfo_by_pids?studentIds={pid}"
    )
    if not resp:
        raise HTTPException(status_code=502, detail="UCSD API unavailable")
    if not resp.ok or not resp.json():
        raise HTTPException(status_code=404, detail="Student not found")
    return _parse_student(resp.json()[0], pid)
