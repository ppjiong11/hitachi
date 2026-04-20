#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Standalone hall-call test for Hitachi CN."""

from __future__ import annotations

from hitachi_cn.app import run_field_runner
from hitachi_cn.config import clone_config


CONFIG = clone_config(
    BASE_URL="http://192.168.88.254:8081",
    USERNAME="WVCOND",
    PASSWORD="WV12345",
    VERIFY_TLS=False,
    LIFT_ID=1,
    REQUEST_FLOOR=2,
    USE_REAR=False,
    RUN_SNAPSHOT=False,
    RUN_DOOR_TEST=False,
    RUN_CALL_TEST=True,
    RUN_TRIP_TEST=False,
    RUN_RESET_ONLY=False,
    DRY_RUN=False,
    CONFIRM_BEFORE_MOVE=True,
    ALLOW_NON_NORMAL_MODE=False,
    NORMAL_OPERATION_MODE=4,
    POLL_INTERVAL_SEC=0.5,
    STABLE_N=2,
    REGISTER_TIMEOUT_SEC=10.0,
    CALL_TIMEOUT_SEC=120.0,
    WAIT_FOR_CALL_ARRIVAL=True,
    CLEAR_CALL_AFTER_TEST=True,
)


def main() -> None:
    run_field_runner(CONFIG)


if __name__ == "__main__":
    main()
