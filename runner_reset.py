#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Emergency reset entrypoint."""

from __future__ import annotations

from hitachi_cn.app import run_field_runner
from hitachi_cn.config import clone_config
from runner_final import CONFIG as BASE_CONFIG


CONFIG = clone_config(
    BASE_CONFIG,
    RUN_SNAPSHOT=False,
    RUN_DOOR_TEST=False,
    RUN_TRIP_TEST=False,
    RUN_RESET_ONLY=True,
)


def main() -> None:
    run_field_runner(CONFIG)


if __name__ == "__main__":
    main()
