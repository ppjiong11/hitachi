#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Example configuration file for delivery and environment handover."""

from hitachi_cn.config import DEFAULT_FRAMEWORK_RUN, clone_config


CONFIG = clone_config(
    BASE_URL="http://your-cn-host:8081",
    USERNAME="your_username",
    PASSWORD="your_password",
    VERIFY_TLS=False,
    LIFT_ID=1,
    REQUEST_FLOOR=5,
    DEST_FLOOR=10,
    RUN_SNAPSHOT=True,
    RUN_DOOR_TEST=False,
    RUN_TRIP_TEST=False,
    RUN_RESET_ONLY=False,
    DRY_RUN=True,
    CONFIRM_BEFORE_MOVE=True,
    ALLOW_NON_NORMAL_MODE=True,
)


RUN = dict(DEFAULT_FRAMEWORK_RUN)
