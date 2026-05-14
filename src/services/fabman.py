import logging
import os
import time
from datetime import datetime

import requests

FABMAN_API_URL = "https://fabman.io/api/v1"
DEV_MODE = os.environ.get("DEV_MODE", "").lower() == "true"


def _headers() -> dict:
    return {"Authorization": f"Bearer {os.environ['FABMAN_API_TOKEN']}"}


def create_member(first_name: str, last_name: str, email: str, rfid_tag: str) -> dict:
    if DEV_MODE:
        logging.info(f"[DEV] Skipping Fabman account creation for {first_name} {last_name}")
        return {"member_id": 0, "package_added": True, "key_assigned": True}

    email = email.lower()
    today = datetime.now().strftime("%Y-%m-%d")
    headers = _headers()
    space = int(os.environ["FABMAN_SPACE"])
    account = int(os.environ["FABMAN_ACCOUNT"])
    package = int(os.environ["FABMAN_DIB_PACKAGE"])

    start = time.time()
    attempt = requests.post(
        f"{FABMAN_API_URL}/members",
        headers=headers,
        json={
            "firstName": first_name,
            "lastName": last_name,
            "emailAddress": email,
            "space": space,
            "account": account,
        },
    )
    logging.info(f"[Fabman] POST /members {attempt.status_code} {(time.time() - start) * 1000:.0f}ms")

    start = time.time()
    get_existing = requests.get(
        f"{FABMAN_API_URL}/members", headers=headers, params={"q": email}
    )
    logging.info(f"[Fabman] GET /members {get_existing.status_code} {(time.time() - start) * 1000:.0f}ms")

    if attempt.status_code == 201:
        logging.info(f"fabman account created for {first_name}")
    elif get_existing.ok and get_existing.json():
        logging.info(f"{email} already had an account, using existing")
    else:
        raise RuntimeError(f"Fabman member creation failed: {attempt.status_code}")

    members = get_existing.json()
    if not members:
        raise RuntimeError("Could not retrieve Fabman member ID")
    member_id = members[0]["id"]

    start = time.time()
    pkg = requests.post(
        f"{FABMAN_API_URL}/members/{member_id}/packages",
        headers=headers,
        json={"package": package, "fromDate": today},
    )
    logging.info(f"[Fabman] POST /members/{member_id}/packages {pkg.status_code} {(time.time() - start) * 1000:.0f}ms")

    start = time.time()
    key = requests.post(
        f"{FABMAN_API_URL}/members/{member_id}/key",
        headers=headers,
        json={"token": rfid_tag, "type": "nfca"},
    )
    logging.info(f"[Fabman] POST /members/{member_id}/key {key.status_code} {(time.time() - start) * 1000:.0f}ms")

    if pkg.status_code != 201:
        logging.warning(f"package add failed: {pkg.status_code} {pkg.json()}")
    if key.status_code != 201:
        logging.warning(f"key assignment failed: {key.status_code} {key.json()}")

    return {
        "member_id": member_id,
        "package_added": pkg.status_code == 201,
        "key_assigned": key.status_code == 201,
    }
