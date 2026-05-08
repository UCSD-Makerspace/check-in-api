import logging
import threading
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

_PST = ZoneInfo("America/Los_Angeles")

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator

from services import cache, fabman, sheets as sheets_service, ucsd

router = APIRouter()


class AccountRequest(BaseModel):
    rfid: str
    barcode: Optional[str] = None
    pid: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None

    @model_validator(mode="after")
    def check_inputs(self):
        has_lookup = self.barcode or self.pid
        has_manual = self.first_name and self.last_name and self.email
        if not has_lookup and not has_manual:
            raise ValueError("Either barcode, pid, or first/last/email must be provided")
        return self


def _student_response(student: dict) -> dict:
    email = next((e for e in student["emails"] if e.endswith("@ucsd.edu")),
                 student["emails"][0] if student["emails"] else "")
    return {
        "first_name": student["first_name"],
        "last_name": student["last_name"],
        "email": email,
        "pid": student["pid"],
    }


@router.get("/accounts/lookup/pid/{pid}")
def lookup_student_by_pid(pid: str):
    student = ucsd.fetch_student_by_pid(pid)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return _student_response(student)


@router.get("/accounts/lookup/barcode/{barcode}")
def lookup_student_by_barcode(barcode: str):
    student = ucsd.fetch_student_by_barcode(barcode)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return _student_response(student)


@router.post("/accounts", status_code=201)
def create_account(body: AccountRequest):
    if body.barcode:
        student = ucsd.fetch_student_by_barcode(body.barcode)
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")
    elif body.pid:
        student = ucsd.fetch_student_by_pid(body.pid)
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")
    else:
        student = {
            "pid": "",
            "first_name": body.first_name,
            "last_name": body.last_name,
            "emails": [body.email],
        }

    email = next((e for e in student["emails"] if e.endswith("@ucsd.edu")),
                 student["emails"][0] if student["emails"] else "")
    full_name = f"{student['first_name']} {student['last_name']}"
    timestamp = datetime.now(_PST).strftime("%m/%d/%Y %H:%M:%S")
    row = [full_name, email, timestamp, body.rfid, student["pid"]]

    try:
        sheets_service.append_user_row(row)
    except Exception as e:
        logging.error(f"Failed to write user row: {e}")
        raise HTTPException(status_code=502, detail="Google Sheets unavailable")

    cache.add_user(cache.User(uuid=body.rfid, student_id=student["pid"], name=full_name, timestamp=timestamp, email=email))

    threading.Thread(
        target=_create_fabman_member,
        args=(student["first_name"], student["last_name"], email, body.rfid),
        daemon=True,
    ).start()

    return {"status": "ok"}


def _create_fabman_member(first_name: str, last_name: str, email: str, rfid: str):
    try:
        fabman.create_member(first_name, last_name, email, rfid)
    except Exception as e:
        logging.error(f"Fabman account creation failed: {e}")
