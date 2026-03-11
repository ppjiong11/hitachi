from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


DEFAULT_CONFIG: Dict[str, Any] = {
    "BASE_URL": "http://192.168.88.253:8081",
    "USERNAME": "WVCOND",
    "PASSWORD": "WV12345",
    "VERIFY_TLS": False,
    "TIMEOUT_SEC": 10.0,
    "RETRIES": 2,
    "BACKOFF_SEC": 0.5,
    "TOKEN_TTL_SEC": 600,
    "TOKEN_REFRESH_MARGIN_SEC": 30,
    "POLL_INTERVAL_SEC": 0.5,
    "STABLE_N": 2,
    "DOOR_HOLD_SEC": 3.0,
    "LIFT_ID": 1,
    "REQUEST_FLOOR": 10,
    "DEST_FLOOR": 9,
    "USE_REAR": False,
    "RUN_SNAPSHOT": True,
    "RUN_DOOR_TEST": True,
    "RUN_TRIP_TEST": True,
    "RUN_RESET_ONLY": False,
    "DRY_RUN": False,
    "CONFIRM_BEFORE_MOVE": True,
    "ALLOW_NON_NORMAL_MODE": True,
}


DEFAULT_FRAMEWORK_RUN: Dict[str, Any] = {
    "MODE": "status",
    "LIFT_ID": 1,
    "COMMAND_LIFT_ID": 1,
    "COMMAND_JSON": {"frontopen": 1},
    "FLOW_LIFT_ID": 1,
    "REQUEST_FLOOR": 5,
    "DEST_FLOOR": 10,
    "USE_REAR": False,
    "HALL_CALL_DISABLE": True,
    "HOLD_DOOR": True,
    "POLL_INTERVAL_SEC": 1.0,
    "TIMEOUT_REQ_SEC": 180,
    "TIMEOUT_DEST_SEC": 300,
}


def clone_config(base: Dict[str, Any] | None = None, **overrides: Any) -> Dict[str, Any]:
    data = deepcopy(base or DEFAULT_CONFIG)
    data.update(overrides)
    return data
