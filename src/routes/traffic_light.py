from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from services.cache import get_redis

router = APIRouter()

REDIS_KEY = "traffic_light_color"
TTL = 30


class ColorPayload(BaseModel):
    color: Literal["red", "green", "yellow", "off"]


@router.post("/traffic-light")
def set_color(body: ColorPayload):
    get_redis().setex(REDIS_KEY, TTL, body.color)
    return {"color": body.color}


@router.get("/traffic-light")
def get_color():
    color = get_redis().get(REDIS_KEY) or "off"
    return {"color": color}
