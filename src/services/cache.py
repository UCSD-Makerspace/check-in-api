import dataclasses
import json
import logging
import os
import threading
import time
from queue import Queue
from typing import Optional

import redis

from services import sheets as sheets_service, ucsd as ucsd_service, ucsd as ucsd_service

REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))  # TODO: probably default not needed
REDIS_DB = int(os.environ.get("REDIS_DB", 0))

_redis_client: Optional[redis.Redis] = None
_activity_queue: Optional["ActivityQueue"] = None
_enrollment_queue: Optional["EnrollmentQueue"] = None


@dataclasses.dataclass
class User:
    email: str
    name: str
    timestamp: str
    student_id: str = ""
    uuid: str = ""
    first_enr_term: str = ""
    last_enr_term: str = ""


class EnrollmentQueue:
    def __init__(self):
        self._q: Queue = Queue()
        self._pending: set = set()
        self._lock = threading.Lock()
        threading.Thread(target=self._worker, daemon=True).start()

    def enqueue(self, user: "User"):
        if not user.student_id:
            return
        with self._lock:
            if user.student_id in self._pending:
                return
            self._pending.add(user.student_id)
        self._q.put(user)

    def _worker(self):
        while True:
            user = self._q.get()
            try:
                first_enr_trm, last_enr_trm = ucsd_service.get_enrollment_terms(user.student_id)
                updated = dataclasses.replace(user, first_enr_term=first_enr_trm, last_enr_term=last_enr_trm)
                add_user(updated)
                logging.info(f"updated enrollment terms for {user.student_id}: {first_enr_trm}/{last_enr_trm}")
            except Exception as e:
                logging.error(f"failed to update enrollment terms for {user.student_id}: {e}")
            finally:
                with self._lock:
                    self._pending.discard(user.student_id)


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
                logging.debug(f"skipping duplicate activity for tag {tag}")
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
                    logging.error(f"failed to write activity (attempt {attempt + 1}): {e}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
        )
    return _redis_client


def get_enrollment_queue() -> "EnrollmentQueue":
    return _enrollment_queue


def get_activity_queue() -> ActivityQueue:
    return _activity_queue


def refresh():
    logging.info("cache refresh starting")

    logging.info("fetching user data from Google Sheets")
    users = sheets_service.read_users()
    logging.info(f"fetched {len(users)} user records")

    logging.info("fetching waiver data from Google Sheets")
    waivers = sheets_service.read_waivers()
    logging.info(f"fetched {len(waivers)} waiver records")

    r = get_redis()
    r.flushdb()

    add_users([
        User(
            uuid=row.get("Card UUID", "").strip(),
            student_id=row.get("Student ID", ""),
            name=row.get("Name", ""),
            timestamp=row.get("Timestamp", ""),
            email=row.get("Email Address", ""),
        )
        for row in users
        if row.get("Email Address", "").strip()
    ])

    pipe = r.pipeline()
    for row in waivers:
        pid = row.get("A_Number", "").strip().lower().lstrip("a")
        email = row.get("Email", "").strip().lower()
        if pid:
            pipe.sadd("waiver_pids", pid)
        if email:
            pipe.sadd("waiver_emails", email)
    pipe.execute()

    mem = r.info("memory")["used_memory_human"]
    logging.info(f"cache refresh complete (Redis using {mem})")


def _refresh_loop():
    while True:
        time.sleep(3600)
        try:
            refresh()
        except Exception as e:
            logging.error(f"failed to refresh cache: {e}")


def start():
    global _activity_queue, _enrollment_queue
    refresh()
    _activity_queue = ActivityQueue()
    _enrollment_queue = EnrollmentQueue()
    threading.Thread(target=_refresh_loop, daemon=True).start()


def get_user_by_uuid(uuid: str) -> Optional[User]:
    r = get_redis()
    email = r.hget("users_by_uuid", uuid)
    if email is None:
        return None
    data = r.hget("users", email)
    return User(**json.loads(data)) if data else None


def get_user_by_pid(pid: str) -> Optional[User]:
    normalized = pid.strip().lower().lstrip("a")
    r = get_redis()
    email = r.hget("users_by_pid", normalized)
    if email is None:
        return None
    data = r.hget("users", email)
    return User(**json.loads(data)) if data else None


def has_waiver(user: User) -> bool:
    normalized_pid = user.student_id.strip().lower().lstrip("a")
    normalized_email = user.email.strip().lower()
    r = get_redis()
    return bool(
        r.sismember("waiver_pids", normalized_pid)
        or r.sismember("waiver_emails", normalized_email)
    )


def add_users(users: list[User]):
    pipe = get_redis().pipeline()
    for user in users:
        normalized_email = user.email.strip().lower()
        normalized_pid = user.student_id.strip().lower().lstrip("a")
        pipe.hset("users", normalized_email, json.dumps(dataclasses.asdict(user)))
        if user.uuid:
            pipe.hset("users_by_uuid", user.uuid, normalized_email)
        if normalized_pid:
            pipe.hset("users_by_pid", normalized_pid, normalized_email)
    pipe.execute()


def add_user(user: User):
    add_users([user])
