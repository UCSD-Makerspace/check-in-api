import logging
import os
import threading
import time
from typing import List, Optional

import gspread
import pymysql
import pymysql.cursors
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
DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]

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


def get_db() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def _init_db():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    card_uuid VARCHAR(64) PRIMARY KEY,
                    name VARCHAR(255),
                    timestamp VARCHAR(64),
                    student_id VARCHAR(255),
                    email VARCHAR(255)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS waivers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    a_number VARCHAR(32),
                    email VARCHAR(255),
                    INDEX (a_number),
                    INDEX (email)
                )
            """)
    finally:
        conn.close()


def _refresh_cache():
    logging.info("Fetching user data from Google Sheets...")
    users = get_sheets_client().open(USER_DB_NAME).worksheet(USER_DB_TAB).get_all_records(numericise_ignore=["all"])
    logging.info(f"Fetched {len(users)} user records")

    logging.info("Fetching waiver data from Google Sheets...")
    waivers = get_sheets_client().open(WAIVER_DB_NAME).worksheet(WAIVER_DB_TAB).get_all_records(numericise_ignore=["all"])
    logging.info(f"Fetched {len(waivers)} waiver records")

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users")
            for row in users:
                card_uuid = row.get("Card UUID", "").strip()
                if not card_uuid:
                    continue
                cur.execute(
                    "REPLACE INTO users (card_uuid, name, timestamp, student_id, email) VALUES (%s, %s, %s, %s, %s)",
                    (card_uuid, row.get("Name", ""), row.get("Timestamp", ""), row.get("Student ID", ""), row.get("Email Address", "")),
                )

            cur.execute("DELETE FROM waivers")
            for row in waivers:
                a_number = row.get("A_Number", "").strip().lower().lstrip("a")
                email = row.get("Email", "").strip().lower()
                cur.execute("INSERT INTO waivers (a_number, email) VALUES (%s, %s)", (a_number, email))
    finally:
        conn.close()

    logging.info("Cache refreshed")


def _refresh_loop():
    while True:
        time.sleep(3600)
        try:
            _refresh_cache()
        except Exception as e:
            logging.error(f"Failed to refresh sheet cache: {e}")


def start_cache():
    _init_db()
    _refresh_cache()
    threading.Thread(target=_refresh_loop, daemon=True).start()


@router.get("/users/{uuid}")
def get_user(uuid: str):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name, timestamp, student_id, email FROM users WHERE card_uuid = %s",
                (uuid,),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"Name": row["name"], "Timestamp": row["timestamp"], "Student ID": row["student_id"], "Email Address": row["email"]}


@router.get("/waivers/check")
def check_waiver(pid: str, email: str):
    normalized_pid = pid.strip().lower().lstrip("a")
    normalized_email = email.strip().lower()
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM waivers WHERE a_number = %s OR email = %s",
                (normalized_pid, normalized_email),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    return {"has_waiver": row is not None}


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
