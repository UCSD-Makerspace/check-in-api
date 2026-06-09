from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

_PST = ZoneInfo("America/Los_Angeles")

from fastapi import APIRouter, HTTPException

from api_models import AccountRequest, CreateAccountResponse, StudentResponse
from services import cache, fabman, sheets as sheets_service, ucsd

router = APIRouter()




@router.get("/accounts/rfid/{uuid}")
def get_account_by_rfid(uuid: str) -> StudentResponse:
    user = cache.get_user_by_uuid(uuid)
    if user is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return StudentResponse(student=cache.to_student(user))


@router.get("/accounts/pid/{pid}")
def get_account_by_pid(pid: str) -> StudentResponse:
    user = cache.get_user_by_pid(pid)
    if user is not None:
        return StudentResponse(student=cache.to_student(user))
    student = ucsd.fetch_student_by_pid(pid)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return StudentResponse(student=ucsd.to_student(student))


@router.get("/accounts/barcode/{barcode}")
def get_account_by_barcode(barcode: str) -> StudentResponse:
    student = ucsd.fetch_student_by_barcode(barcode)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    user = cache.get_user_by_pid(student["pid"])
    if user is not None:
        return StudentResponse(student=cache.to_student(user))
    return StudentResponse(student=ucsd.to_student(student))


@router.post("/accounts", status_code=201)
def create_account(body: AccountRequest) -> CreateAccountResponse:
    first_name = (body.first_name or "").strip()
    last_name = (body.last_name or "").strip()
    email = (body.email or "").strip().lower()
    pid = (body.pid or "").strip().upper()
    full_name = f"{first_name} {last_name}".strip()
    timestamp = datetime.now(_PST).strftime("%m/%d/%Y %H:%M:%S")
    row = [full_name, email, timestamp, body.rfid, pid]

    try:
        sheets_service.append_user_row(row)
    except Exception as e:
        logging.error(f"failed to write user row: {e}")
        raise HTTPException(status_code=502, detail="Google Sheets unavailable")

    cache.add_user(cache.User(uuid=body.rfid, student_id=pid, name=full_name, timestamp=timestamp, email=email))

    threading.Thread(
        target=_create_fabman_member,
        args=(first_name, last_name, email, body.rfid),
        daemon=True,
    ).start()

    return CreateAccountResponse(status="ok")


def _create_fabman_member(first_name: str, last_name: str, email: str, rfid: str) -> None:
    try:
        fabman.create_member(first_name, last_name, email, rfid)
    except Exception as e:
        logging.error(f"fabman account creation failed: {e}")
