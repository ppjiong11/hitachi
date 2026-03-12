#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Compatibility entrypoint for the field runner."""

from __future__ import annotations

from hitachi_cn.app import run_field_runner
from hitachi_cn.config import clone_config
from project_config import CONFIG as BASE_CONFIG


CONFIG = clone_config(
    BASE_CONFIG,
    USERNAME="your_username",
    PASSWORD="your_password",
    RUN_DOOR_TEST=False,
    RUN_TRIP_TEST=False,
    DOOR_HOLD_SEC=5.0,
)


def main() -> None:
    run_field_runner(CONFIG)


if __name__ == "__main__":
    main()
