from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

import requests
import urllib3

from .errors import CNAPIError
from .logger import Logger
from .models import CNAuth
from .utils import ensure_url_scheme

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CNClient:
    def __init__(self, cfg: Dict[str, Any], logger: Logger) -> None:
        self.base_url = ensure_url_scheme(str(cfg["BASE_URL"]).rstrip("/"))
        self.username = str(cfg["USERNAME"])
        self.password = str(cfg["PASSWORD"])
        self.verify_tls = bool(cfg.get("VERIFY_TLS", True))
        self.timeout_sec = float(cfg.get("TIMEOUT_SEC", 8.0))
        self.retries = int(cfg.get("RETRIES", 2))
        self.backoff_sec = float(cfg.get("BACKOFF_SEC", 0.5))
        self.token_ttl_sec = int(cfg.get("TOKEN_TTL_SEC", 600))
        self.refresh_margin_sec = int(cfg.get("TOKEN_REFRESH_MARGIN_SEC", 30))
        self.logger = logger
        self.session = requests.Session()
        self.auth: Optional[CNAuth] = None

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        need_token: bool = True,
    ) -> Tuple[int, Dict[str, Any], float]:
        if need_token:
            self.ensure_login()

        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json"}
        if need_token and self.auth:
            headers["x-access-token"] = self.auth.token

        last_err: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                started_at = time.time()
                resp = self.session.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    json=json_body,
                    headers=headers,
                    auth=(self.username, self.password),
                    timeout=self.timeout_sec,
                    verify=self.verify_tls,
                )
                elapsed = time.time() - started_at

                if resp.status_code == 401 and need_token:
                    self.logger.info(f"401 received, refreshing token: {method.upper()} {path}")
                    self.login(force=True)
                    continue

                try:
                    data = resp.json() if resp.text else {}
                except Exception:
                    data = {"_raw_text": resp.text}

                self.logger.event(
                    {
                        "type": "http",
                        "method": method.upper(),
                        "url": url,
                        "params": params,
                        "json_body": json_body,
                        "status_code": resp.status_code,
                        "elapsed_sec": round(elapsed, 3),
                        "resp": data,
                    }
                )

                if resp.status_code >= 400:
                    raise CNAPIError(f"HTTP {resp.status_code} {method.upper()} {url}: {resp.text[:300]}")

                return resp.status_code, data, elapsed
            except Exception as exc:
                last_err = exc
                if attempt < self.retries:
                    time.sleep(self.backoff_sec * (2**attempt))
                else:
                    break

        raise CNAPIError(f"Request failed: {method.upper()} {url}. Last error: {last_err}")

    def login(self, force: bool = False) -> CNAuth:
        if (not force) and self.auth and (not self.auth.expired()):
            return self.auth

        _, data, _ = self._request("GET", "/login", need_token=False)
        if "public_id" not in data or "token" not in data:
            raise CNAPIError(f"Login response missing public_id/token: {data}")

        self.auth = CNAuth(
            public_id=str(data["public_id"]),
            token=str(data["token"]),
            login_time=time.time(),
            token_ttl_sec=self.token_ttl_sec,
            refresh_margin_sec=self.refresh_margin_sec,
        )
        self.logger.info(f"Login OK. public_id={self.auth.public_id}")
        return self.auth

    def ensure_login(self) -> None:
        if self.auth is None or self.auth.expired():
            self.login(force=True)

    def get_status(self, lift_id: Optional[int] = None) -> Dict[str, Any]:
        self.ensure_login()
        assert self.auth is not None
        path = f"/lift/{self.auth.public_id}"
        _, data, _ = self._request("GET", path, params=None if lift_id is None else {"lift_id": int(lift_id)})
        return data

    def get_config(self, lift_id: Optional[int] = None) -> Dict[str, Any]:
        self.ensure_login()
        assert self.auth is not None
        path = f"/config/{self.auth.public_id}"
        _, data, _ = self._request("GET", path, params=None if lift_id is None else {"lift_id": int(lift_id)})
        return data

    def put_command(self, lift_id: int, command: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        self.ensure_login()
        assert self.auth is not None
        body = {"lift_id": int(lift_id), "command": command}
        self.logger.info(f"PUT command lift_id={lift_id} command={command} dry_run={dry_run}")
        if dry_run:
            return {"_dry_run": True, **body}

        _, data, _ = self._request("PUT", f"/lift/{self.auth.public_id}", json_body=body)
        if "accept_status" in data and int(data["accept_status"]) != 0:
            raise CNAPIError(f"Command rejected (accept_status={data.get('accept_status')}): {data}")
        return data
