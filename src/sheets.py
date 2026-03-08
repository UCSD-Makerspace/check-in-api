import os
import logging
from typing import List, Optional

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

GOOGLE_CREDS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH")
ACTIVITY_SHEET_URL = os.environ["ACTIVITY_SHEET_URL"]
ACTIVITY_SHEET_TAB = os.environ["ACTIVITY_SHEET_TAB"]
USER_DB_NAME = os.environ["USER_DB_NAME"]
USER_DB_TAB = os.environ["USER_DB_TAB"]
WAIVER_DB_NAME = os.environ["WAIVER_DB_NAME"]
WAIVER_DB_TAB = os.environ["WAIVER_DB_TAB"]

_sheets_client: Optional[gspread.Client] = None

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


@router.get("/users")
def get_users():
    try:
        sheet = get_sheets_client().open(USER_DB_NAME).worksheet(USER_DB_TAB)
        return sheet.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        logging.error(f"Failed to fetch users: {e}")
        raise HTTPException(status_code=502, detail="Google Sheets unavailable")


@router.get("/waivers")
def get_waivers():
    try:
        sheet = get_sheets_client().open(WAIVER_DB_NAME).worksheet(WAIVER_DB_TAB)
        return sheet.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        logging.error(f"Failed to fetch waivers: {e}")
        raise HTTPException(status_code=502, detail="Google Sheets unavailable")


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
        sheet.append_row(body.row)
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Failed to append activity: {e}")
        raise HTTPException(status_code=502, detail="Google Sheets unavailable")
