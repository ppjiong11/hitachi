from __future__ import annotations

import datetime as dt
import json
import os
from typing import Any


def ensure_url_scheme(url: str) -> str:
    value = url.strip()
    if not value.startswith(("http://", "https://")):
        return f"http://{value}"
    return value


def pretty(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def ts(compact: bool = False) -> str:
    fmt = "%Y%m%d_%H%M%S" if compact else "%Y-%m-%d %H:%M:%S"
    return dt.datetime.now().strftime(fmt)


def mkdir_p(path: str) -> None:
    os.makedirs(path, exist_ok=True)
