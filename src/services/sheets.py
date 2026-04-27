import os
from typing import Optional

import gspread
from oauth2client.service_account import ServiceAccountCredentials

GOOGLE_CREDS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH")
ACTIVITY_SHEET_ID = os.environ["ACTIVITY_SHEET_ID"]
ACTIVITY_SHEET_TAB = os.environ["ACTIVITY_SHEET_TAB"]
USER_SHEET_ID = os.environ["USER_SHEET_ID"]
USER_SHEET_TAB = os.environ["USER_SHEET_TAB"]
WAIVER_SHEET_ID = os.environ["WAIVER_SHEET_ID"]
WAIVER_SHEET_TAB = os.environ["WAIVER_SHEET_TAB"]

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
    return (get_client().open_by_key(USER_SHEET_ID).worksheet(USER_SHEET_TAB)
            .get_all_records(numericise_ignore=["all"], head=2))


def read_waivers() -> list[dict]:
    return (get_client().open_by_key(WAIVER_SHEET_ID).worksheet(WAIVER_SHEET_TAB)
            .get_all_records(numericise_ignore=["all"]))


def append_user_row(row: list):
    get_client().open_by_key(USER_SHEET_ID).worksheet(USER_SHEET_TAB).append_row(row)


def append_activity_row(row: list):
    get_client().open_by_key(ACTIVITY_SHEET_ID).worksheet(ACTIVITY_SHEET_TAB).append_row(row)
