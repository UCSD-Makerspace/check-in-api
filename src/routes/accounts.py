import logging
import threading
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import cache, fabman, sheets as sheets_service

router = APIRouter()


class AccountRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    pid: str
    rfid: str


@router.post("/accounts", status_code=201)
def create_account(body: AccountRequest):
    full_name = f"{body.first_name} {body.last_name}"
    timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    row = [full_name, timestamp, body.rfid, body.pid, body.email]

    try:
        sheets_service.append_user_row(row)
    except Exception as e:
        logging.error(f"Failed to write user row: {e}")
        raise HTTPException(status_code=502, detail="Google Sheets unavailable")

    cache.add_user(body.rfid, body.pid, full_name, timestamp, body.email)

    threading.Thread(
        target=_create_fabman_member,
        args=(body.first_name, body.last_name, body.email, body.rfid),
        daemon=True,
    ).start()

    return {"status": "ok"}


def _create_fabman_member(first_name: str, last_name: str, email: str, rfid: str):
    try:
        fabman.create_member(first_name, last_name, email, rfid)
    except Exception as e:
        logging.error(f"Fabman account creation failed: {e}")
