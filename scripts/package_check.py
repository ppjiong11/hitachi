#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Lightweight project self-check used before delivery."""

from __future__ import annotations

import compileall
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    ok = compileall.compile_dir(root / "hitachi_cn", quiet=1)
    ok = compileall.compile_file(str(root / "runner_final.py"), quiet=1) and ok
    ok = compileall.compile_file(str(root / "runner_reset.py"), quiet=1) and ok
    ok = compileall.compile_file(str(root / "framework.py"), quiet=1) and ok
    ok = compileall.compile_file(str(root / "runner.py"), quiet=1) and ok
    ok = compileall.compile_file(str(root / "project_config.py"), quiet=1) and ok
    print("package check:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
