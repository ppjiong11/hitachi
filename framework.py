#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Minimal framework entrypoint for quick CN API operations."""

from __future__ import annotations

from hitachi_cn.app import run_framework_mode
from project_config import CONFIG, RUN


def main() -> None:
    run_framework_mode(CONFIG, RUN)


if __name__ == "__main__":
    main()
