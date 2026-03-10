from datetime import datetime

from fastapi import APIRouter

from services import cache, ucsd

router = APIRouter()


def _build_response(d: dict, tag: str) -> dict:
    if not cache.has_waiver(d["student_id"], d["email"]):
        return {"status": "no_waiver", "name": d["name"]}

    first_enr_trm, last_enr_trm = ucsd.get_enrollment_terms(d["student_id"])

    now = datetime.now()
    cache.get_activity_queue().enqueue([
        now.strftime("%m/%d/%Y %H:%M:%S"),
        int(now.timestamp()),
        d["name"],
        tag,
        "User Check-In",
        "",
        first_enr_trm,
        last_enr_trm,
    ], tag)

    return {
        "status": "ok",
        "name": d["name"],
        "student_id": d["student_id"],
        "timestamp": d["timestamp"],
        "email": d["email"],
        "first_enr_term": first_enr_trm,
        "last_enr_term": last_enr_trm,
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
