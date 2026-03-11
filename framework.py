#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Minimal framework entrypoint for quick CN API operations."""

from __future__ import annotations

from hitachi_cn.app import run_framework_mode
from hitachi_cn.config import DEFAULT_FRAMEWORK_RUN, clone_config


CONFIG = clone_config()
RUN = dict(DEFAULT_FRAMEWORK_RUN)


def main() -> None:
    run_framework_mode(CONFIG, RUN)


if __name__ == "__main__":
    main()
