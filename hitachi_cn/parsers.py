from __future__ import annotations

from typing import Any, Dict

from .errors import CNAPIError


def single_liftstatus(resp: Dict[str, Any], lift_id: int | None = None) -> Dict[str, Any]:
    status = resp.get("liftstatus")
    if isinstance(status, dict):
        return status
    if isinstance(status, list):
        if lift_id is not None:
            for item in status:
                if isinstance(item, dict) and int(item.get("liftID", -1)) == lift_id:
                    return item
        for item in status:
            if isinstance(item, dict):
                return item
    raise CNAPIError(f"Unexpected liftstatus payload: {status!r}")
