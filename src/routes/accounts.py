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

    @model_validator(mode="after")
    def check_barcode_or_pid(self):
        if not self.barcode and not self.pid:
            raise ValueError("Either barcode or pid must be provided")
        return self


@router.post("/accounts", status_code=201)
def create_account(body: AccountRequest):
    if body.barcode:
        student = ucsd.fetch_student_by_barcode(body.barcode)
    else:
        student = ucsd.fetch_student_by_pid(body.pid)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    email = next((e for e in student["emails"] if e.endswith("@ucsd.edu")), student["emails"][0] if student["emails"] else "")
    full_name = f"{student['first_name']} {student['last_name']}"
    timestamp = datetime.now(_PST).strftime("%m/%d/%Y %H:%M:%S")
    row = [full_name, email, timestamp, body.rfid, student["pid"]]

    try:
        sheets_service.append_user_row(row)
    except Exception as e:
        logging.error(f"Failed to write user row: {e}")
        raise HTTPException(status_code=502, detail="Google Sheets unavailable")

    cache.add_user(body.rfid, student["pid"], full_name, timestamp, email)

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
