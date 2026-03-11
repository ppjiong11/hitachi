#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Main field runner entrypoint for the Hitachi CN project."""

from __future__ import annotations

from hitachi_cn.app import run_field_runner
from hitachi_cn.config import clone_config


CONFIG = clone_config()


def main() -> None:
    run_field_runner(CONFIG)


if __name__ == "__main__":
    main()
