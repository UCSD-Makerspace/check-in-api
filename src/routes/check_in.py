from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

_PST = ZoneInfo("America/Los_Angeles")

from fastapi import APIRouter

from api_models import CheckInNoAccount, CheckInNoWaiver, CheckInOk, CheckInRequest, CheckInResponse
from services import cache

router = APIRouter()


@router.post("/check-in")
def checkin(body: CheckInRequest) -> CheckInResponse:
    user = cache.get_user_by_email(body.email)
    if user is None:
        return CheckInNoAccount()
    if not cache.has_waiver(user):
        return CheckInNoWaiver(name=user.name)

    now = datetime.now(_PST)
    cache.get_activity_queue().enqueue([
        now.strftime("%m/%d/%Y %H:%M:%S"),
        int(now.timestamp()),
        user.name,
        body.email,
        "User Check-In",
        "",
        user.first_enr_term,
        user.last_enr_term,
    ], body.email)

    cache.get_enrollment_queue().enqueue(user)

    return CheckInOk(
        name=user.name,
        student_id=user.student_id,
        timestamp=user.timestamp,
        email=user.email,
        first_enr_term=user.first_enr_term,
        last_enr_term=user.last_enr_term,
    )
