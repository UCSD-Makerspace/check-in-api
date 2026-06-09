from __future__ import annotations

from typing import cast

from fastapi import APIRouter

from api_models import TrafficLightRequest, TrafficLightResponse, TrafficLightState
from services.cache import get_redis

router = APIRouter()

REDIS_KEY = "traffic_light_state"
TTL = 30


@router.post("/traffic-light")
def set_state(body: TrafficLightRequest) -> TrafficLightResponse:
    get_redis().setex(REDIS_KEY, TTL, body.state.value)
    return TrafficLightResponse(state=body.state)


@router.get("/traffic-light")
def get_state() -> TrafficLightResponse:
    raw = cast(str | None, get_redis().get(REDIS_KEY)) or TrafficLightState.OFF.value
    return TrafficLightResponse(state=TrafficLightState(raw))
