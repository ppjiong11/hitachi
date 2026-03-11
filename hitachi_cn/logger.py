from __future__ import annotations

import json
import os
from typing import Any, Dict

from .utils import mkdir_p, ts


class Logger:
    def __init__(self, logs_dir: str = "logs", enable_jsonl: bool = True) -> None:
        mkdir_p(logs_dir)
        stamp = ts(compact=True)
        self.log_path = os.path.join(logs_dir, f"run_{stamp}.log")
        self.jsonl_path = os.path.join(logs_dir, f"run_{stamp}.jsonl")
        self.enable_jsonl = enable_jsonl

    def info(self, msg: str) -> None:
        line = f"[{ts()}] {msg}"
        print(line)
        with open(self.log_path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def error(self, msg: str) -> None:
        self.info(f"[ERROR] {msg}")

    def event(self, obj: Dict[str, Any]) -> None:
        if not self.enable_jsonl:
            return
        payload = dict(obj)
        payload["_ts"] = ts()
        with open(self.jsonl_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
