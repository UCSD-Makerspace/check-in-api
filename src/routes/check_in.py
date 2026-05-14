from datetime import datetime
from zoneinfo import ZoneInfo

_PST = ZoneInfo("America/Los_Angeles")

from fastapi import APIRouter

from services import cache

router = APIRouter()


def _build_response(user: cache.User, tag: str) -> dict:
    if not cache.has_waiver(user):
        return {"status": "no_waiver", "name": user.name}

    now = datetime.now(_PST)
    cache.get_activity_queue().enqueue([
        now.strftime("%m/%d/%Y %H:%M:%S"),
        int(now.timestamp()),
        user.name,
        tag,
        "User Check-In",
        "",
        user.first_enr_term,
        user.last_enr_term,
    ], tag)

    cache.get_enrollment_queue().enqueue(user)

    return {
        "status": "ok",
        "name": user.name,
        "student_id": user.student_id,
        "timestamp": user.timestamp,
        "email": user.email,
        "first_enr_term": user.first_enr_term,
        "last_enr_term": user.last_enr_term,
    }


@router.get("/check-in/uuid/{uuid}")
def checkin_by_uuid(uuid: str):
    d = cache.get_user_by_uuid(uuid)
    if d is None:
        return {"status": "no_account"}
    return _build_response(d, uuid)


@router.get("/check-in/pid/{pid}")
def checkin_by_pid(pid: str):
    d = cache.get_user_by_pid(pid)
    if d is None:
        return {"status": "no_account"}
    return _build_response(d, "No ID")
