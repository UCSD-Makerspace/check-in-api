import json


def seed_user(r, uuid, pid, name, email, timestamp="01/01/2024 12:00:00"):
    r.hset("users", uuid, json.dumps({
        "name": name,
        "timestamp": timestamp,
        "student_id": pid,
        "email": email,
    }))
    normalized = pid.strip().lower().lstrip("a")
    if normalized:
        r.hset("users_by_pid", normalized, uuid)


def seed_waiver_by_pid(r, pid):
    r.sadd("waiver_anumbers", pid.strip().lower().lstrip("a"))


def seed_waiver_by_email(r, email):
    r.sadd("waiver_emails", email.strip().lower())
