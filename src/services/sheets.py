import os
from typing import Optional

import gspread
from oauth2client.service_account import ServiceAccountCredentials

GOOGLE_CREDS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH")
ACTIVITY_SHEET_URL = os.environ["ACTIVITY_SHEET_URL"]
ACTIVITY_SHEET_TAB = os.environ["ACTIVITY_SHEET_TAB"]
USER_DB_NAME = os.environ["USER_DB_NAME"]
USER_DB_TAB = os.environ["USER_DB_TAB"]
WAIVER_DB_NAME = os.environ["WAIVER_DB_NAME"]
WAIVER_DB_TAB = os.environ["WAIVER_DB_TAB"]

_client: Optional[gspread.Client] = None


def get_client() -> gspread.Client:
    global _client
    if _client is None:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_PATH, scope)
        _client = gspread.authorize(creds)
    return _client


def read_users() -> list[dict]:
    return get_client().open(USER_DB_NAME).worksheet(USER_DB_TAB).get_all_records(numericise_ignore=["all"])


def read_waivers() -> list[dict]:
    return get_client().open(WAIVER_DB_NAME).worksheet(WAIVER_DB_TAB).get_all_records(numericise_ignore=["all"])


def append_user_row(row: list):
    get_client().open(USER_DB_NAME).worksheet(USER_DB_TAB).append_row(row)


def append_activity_row(row: list):
    sheet = get_client().open_by_url(ACTIVITY_SHEET_URL).worksheet(ACTIVITY_SHEET_TAB)
    next_row = len(sheet.get_all_values()) + 1
    sheet.update(f"A{next_row}", [row])
