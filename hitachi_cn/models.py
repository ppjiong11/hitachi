from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class CNAuth:
    public_id: str
    token: str
    login_time: float
    token_ttl_sec: int
    refresh_margin_sec: int

    def expired(self) -> bool:
        return (time.time() - self.login_time) >= (self.token_ttl_sec - self.refresh_margin_sec)
