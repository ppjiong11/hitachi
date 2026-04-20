#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Legacy compatibility entrypoint.

Use check.py for status queries.
Use runner_final.py for control and test flow.
"""

from __future__ import annotations

from check import main


if __name__ == "__main__":
    main()
