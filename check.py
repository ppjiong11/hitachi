#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Simple status checker for Hitachi CN."""

from __future__ import annotations

from hitachi_cn.client import CNClient
from hitachi_cn.logger import Logger
from hitachi_cn.utils import pretty


CONFIG = {
    "BASE_URL": "http://192.168.88.254:8081",  #10.25.0.26:8081   http://192.168.88.254:8081
    "USERNAME": "WVCOND",
    "PASSWORD": "WV12345",
    "VERIFY_TLS": False,
    "TIMEOUT_SEC": 10.0,
    "RETRIES": 2,
    "BACKOFF_SEC": 0.5,
    "TOKEN_TTL_SEC": 600,
    "TOKEN_REFRESH_MARGIN_SEC": 30,
}


CHECK = {
    # Which lift to query. Set to None to query all lifts.
    "LIFT_ID": 1,

    # Whether to also print config fields after status fields.
    "SHOW_CONFIG": False,
}


def main() -> None:
    logger = Logger()
    client = CNClient(CONFIG, logger)
    client.login()

    lift_id = CHECK["LIFT_ID"]
    logger.info("=== STATUS ===")
    logger.info(pretty(client.get_status(lift_id=lift_id)))

    if bool(CHECK["SHOW_CONFIG"]):
        logger.info("=== CONFIG ===")
        logger.info(pretty(client.get_config(lift_id=lift_id)))


if __name__ == "__main__":
    main()



#liftoperation mode 4 是状态正常 才能进行呼梯

#    "frontDestFloorRegistered": 0, 要先发指令，然后如果这个参数是1 代表该楼层注册了，我们需要再发
#    "frontDoorOpenRegistered": 0,
#    "frontReqFloorRegistered": 0,