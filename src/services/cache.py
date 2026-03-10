import json
import logging
import os
import threading
import time
from queue import Queue
from typing import Optional

import redis

from services import sheets as sheets_service

REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")

_redis_client: Optional[redis.Redis] = None
_activity_queue: Optional["ActivityQueue"] = None


class ActivityQueue:
    _DEDUP_WINDOW = 5

    def __init__(self):
        self._q: Queue = Queue()
        self._last_tag: Optional[str] = None
        self._last_time: float = 0
        self._lock = threading.Lock()
        threading.Thread(target=self._writer, daemon=True).start()

    def enqueue(self, row: list, tag: str):
        now = time.time()
        with self._lock:
            if tag == self._last_tag and now - self._last_time < self._DEDUP_WINDOW:
                logging.debug(f"Skipping duplicate activity for tag {tag}")
                return
            self._last_tag = tag
            self._last_time = now
        self._q.put(row)

    def _writer(self):
        while True:
            row = self._q.get()
            for attempt in range(3):
                try:
                    sheets_service.append_activity_row(row)
                    break
                except Exception as e:
                    logging.error(f"Failed to write activity (attempt {attempt + 1}): {e}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)


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


def get_activity_queue() -> ActivityQueue:
    return _activity_queue


def refresh():
    logging.info("Fetching user data from Google Sheets...")
    users = sheets_service.read_users()
    logging.info(f"Fetched {len(users)} user records")

    logging.info("Fetching waiver data from Google Sheets...")
    waivers = sheets_service.read_waivers()
    logging.info(f"Fetched {len(waivers)} waiver records")

    r = get_redis()
    pipe = r.pipeline()
    pipe.delete("users", "users_by_pid", "waiver_anumbers", "waiver_emails")

    for row in users:
        card_uuid = row.get("Card UUID", "").strip()
        if not card_uuid:
            continue
        student_id = row.get("Student ID", "").strip().lower().lstrip("a")
        pipe.hset("users", card_uuid, json.dumps({
            "name": row.get("Name", ""),
            "timestamp": row.get("Timestamp", ""),
            "student_id": row.get("Student ID", ""),
            "email": row.get("Email Address", ""),
        }))
        if student_id:
            pipe.hset("users_by_pid", student_id, card_uuid)

    for row in waivers:
        a_number = row.get("A_Number", "").strip().lower().lstrip("a")
        email = row.get("Email", "").strip().lower()
        if a_number:
            pipe.sadd("waiver_anumbers", a_number)
        if email:
            pipe.sadd("waiver_emails", email)

    pipe.execute()
    mem = r.info("memory")["used_memory_human"]
    logging.info(f"Cache refreshed (Redis using {mem})")


def _refresh_loop():
    while True:
        time.sleep(3600)
        try:
            refresh()
        except Exception as e:
            logging.error(f"Failed to refresh cache: {e}")


def start():
    global _activity_queue
    refresh()
    _activity_queue = ActivityQueue()
    threading.Thread(target=_refresh_loop, daemon=True).start()


def get_user_by_uuid(uuid: str) -> Optional[dict]:
    data = get_redis().hget("users", uuid)
    return json.loads(data) if data else None


def get_user_by_pid(pid: str) -> Optional[dict]:
    normalized = pid.strip().lower().lstrip("a")
    r = get_redis()
    uuid = r.hget("users_by_pid", normalized)
    if uuid is None:
        return None
    data = r.hget("users", uuid)
    return json.loads(data) if data else None


def has_waiver(student_id: str, email: str) -> bool:
    normalized_pid = student_id.strip().lower().lstrip("a")
    normalized_email = email.strip().lower()
    r = get_redis()
    return bool(
        r.sismember("waiver_anumbers", normalized_pid)
        or r.sismember("waiver_emails", normalized_email)
    )


def add_user(uuid: str, student_id: str, name: str, timestamp: str, email: str):
    normalized_pid = student_id.strip().lower().lstrip("a")
    r = get_redis()
    r.hset("users", uuid, json.dumps({
        "name": name,
        "timestamp": timestamp,
        "student_id": student_id,
        "email": email,
    }))
    if normalized_pid:
        r.hset("users_by_pid", normalized_pid, uuid)
