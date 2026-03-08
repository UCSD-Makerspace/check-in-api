import os
import logging
from datetime import datetime

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

FABMAN_API_URL = "https://fabman.io/api/v1"

router = APIRouter()


class MemberRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    rfid_tag: str


@router.post("/members", status_code=201)
def create_member(body: MemberRequest):
    headers = {"Authorization": f"Bearer {os.environ['FABMAN_API_TOKEN']}"}
    space = int(os.environ["FABMAN_SPACE"])
    account = int(os.environ["FABMAN_ACCOUNT"])
    package = int(os.environ["FABMAN_DIB_PACKAGE"])
    email = body.email.lower()
    today = datetime.now().strftime("%Y-%m-%d")

    attempt = requests.post(
        f"{FABMAN_API_URL}/members",
        headers=headers,
        json={
            "firstName": body.first_name,
            "lastName": body.last_name,
            "emailAddress": email,
            "space": space,
            "account": account,
        },
    )
    get_existing = requests.get(
        f"{FABMAN_API_URL}/members", headers=headers, params={"q": email}
    )

    if attempt.status_code == 201:
        logging.info(f"Fabman account created for {body.first_name}")
    elif get_existing.ok and get_existing.json():
        logging.info(f"{email} already had an account, using existing")
    else:
        raise HTTPException(
            status_code=502,
            detail=f"Fabman member creation failed: {attempt.status_code}",
        )

    members = get_existing.json()
    if not members:
        raise HTTPException(status_code=502, detail="Could not retrieve Fabman member ID")
    member_id = members[0]["id"]

    pkg = requests.post(
        f"{FABMAN_API_URL}/members/{member_id}/packages",
        headers=headers,
        json={"package": package, "fromDate": today},
    )
    key = requests.post(
        f"{FABMAN_API_URL}/members/{member_id}/key",
        headers=headers,
        json={"token": body.rfid_tag, "type": "nfca"},
    )

    if pkg.status_code != 201:
        logging.warning(f"Package add failed: {pkg.status_code} {pkg.json()}")
    if key.status_code != 201:
        logging.warning(f"Key assignment failed: {key.status_code} {key.json()}")

    return {
        "member_id": member_id,
        "package_added": pkg.status_code == 201,
        "key_assigned": key.status_code == 201,
    }
