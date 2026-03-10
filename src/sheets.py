import json
import logging
import os
import threading
import time
from typing import List, Optional

import gspread
import redis
from oauth2client.service_account import ServiceAccountCredentials
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ucsd_api import get_enrollment_terms

GOOGLE_CREDS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH")
ACTIVITY_SHEET_URL = os.environ["ACTIVITY_SHEET_URL"]
ACTIVITY_SHEET_TAB = os.environ["ACTIVITY_SHEET_TAB"]
USER_DB_NAME = os.environ["USER_DB_NAME"]
USER_DB_TAB = os.environ["USER_DB_TAB"]
WAIVER_DB_NAME = os.environ["WAIVER_DB_NAME"]
WAIVER_DB_TAB = os.environ["WAIVER_DB_TAB"]
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = int(os.environ.get("REDIS_PORT"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")

_sheets_client: Optional[gspread.Client] = None
_redis_client: Optional[redis.Redis] = None

router = APIRouter()


def get_sheets_client() -> gspread.Client:
    global _sheets_client
    if _sheets_client is None:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_PATH, scope)
        _sheets_client = gspread.authorize(creds)
    return _sheets_client


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True,
        )
    return _redis_client


def _refresh_cache():
    logging.info("Fetching user data from Google Sheets...")
    users = get_sheets_client().open(USER_DB_NAME).worksheet(USER_DB_TAB).get_all_records(numericise_ignore=["all"])
    logging.info(f"Fetched {len(users)} user records")

    logging.info("Fetching waiver data from Google Sheets...")
    waivers = get_sheets_client().open(WAIVER_DB_NAME).worksheet(WAIVER_DB_TAB).get_all_records(numericise_ignore=["all"])
    logging.info(f"Fetched {len(waivers)} waiver records")

    r = get_redis()
    pipe = r.pipeline()
    pipe.delete("users", "waiver_anumbers", "waiver_emails")

    user_count = 0
    for row in users:
        card_uuid = row.get("Card UUID", "").strip()
        if not card_uuid:
            continue
        pipe.hset("users", card_uuid, json.dumps({
            "name": row.get("Name", ""),
            "timestamp": row.get("Timestamp", ""),
            "student_id": row.get("Student ID", ""),
            "email": row.get("Email Address", ""),
        }))
        user_count += 1

    waiver_count = 0
    for row in waivers:
        a_number = row.get("A_Number", "").strip().lower().lstrip("a")
        email = row.get("Email", "").strip().lower()
        if a_number:
            pipe.sadd("waiver_anumbers", a_number)
        if email:
            pipe.sadd("waiver_emails", email)
        waiver_count += 1

    logging.info(f"Writing {user_count} users and {waiver_count} waivers to Redis...")
    pipe.execute()
    mem = r.info('memory')['used_memory_human']
    logging.info(f"Cache refreshed (Redis using {mem})")


def _refresh_loop():
    while True:
        time.sleep(3600)
        try:
            _refresh_cache()
        except Exception as e:
            logging.error(f"Failed to refresh sheet cache: {e}")


def start_cache():
    _refresh_cache()
    threading.Thread(target=_refresh_loop, daemon=True).start()


@router.get("/users/{uuid}")
def get_user(uuid: str):
    r = get_redis()
    data = r.hget("users", uuid)
    if data is None:
        raise HTTPException(status_code=404, detail="User not found")
    d = json.loads(data)
    first_enr_trm, last_enr_trm = get_enrollment_terms(d.get("student_id", ""))
    return {
        "Name": d["name"],
        "Timestamp": d["timestamp"],
        "Student ID": d["student_id"],
        "Email Address": d["email"],
        "firstEnrTrm": first_enr_trm,
        "lastEnrTrm": last_enr_trm,
    }


@router.get("/waivers/check")
def check_waiver(pid: str, email: str):
    normalized_pid = pid.strip().lower().lstrip("a")
    normalized_email = email.strip().lower()
    r = get_redis()
    has_waiver = r.sismember("waiver_anumbers", normalized_pid) or r.sismember("waiver_emails", normalized_email)
    return {"has_waiver": bool(has_waiver)}


class UserRow(BaseModel):
    row: List


@router.post("/users", status_code=201)
def append_user(body: UserRow):
    try:
        sheet = get_sheets_client().open(USER_DB_NAME).worksheet(USER_DB_TAB)
        sheet.append_row(body.row)
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Failed to append user row: {e}")
        raise HTTPException(status_code=502, detail="Google Sheets unavailable")


class ActivityRow(BaseModel):
    row: List


@router.post("/activity", status_code=201)
def append_activity(body: ActivityRow):
    try:
        sheet = get_sheets_client().open_by_url(ACTIVITY_SHEET_URL).worksheet(ACTIVITY_SHEET_TAB)
        next_row = len(sheet.get_all_values()) + 1
        sheet.update(f"A{next_row}", [body.row])
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Failed to append activity: {e}")
        raise HTTPException(status_code=502, detail="Google Sheets unavailable")
