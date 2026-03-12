#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Editable project configuration for field testing."""

from hitachi_cn.config import DEFAULT_FRAMEWORK_RUN, clone_config


CONFIG = clone_config(
    BASE_URL="http://192.168.88.253:8081",
    USERNAME="WVCOND",
    PASSWORD="WV12345",
    VERIFY_TLS=False,
    LIFT_ID=1,
    REQUEST_FLOOR=10,
    DEST_FLOOR=9,
    RUN_SNAPSHOT=True,
    RUN_DOOR_TEST=True,
    RUN_TRIP_TEST=True,
    RUN_RESET_ONLY=False,
    DRY_RUN=False,
    CONFIRM_BEFORE_MOVE=True,
    ALLOW_NON_NORMAL_MODE=True,
)


RUN = dict(DEFAULT_FRAMEWORK_RUN)
