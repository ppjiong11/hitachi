#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Manual robot full-flow runner for Hitachi CN.

Flow:
1. Call elevator to REQUEST_FLOOR.
2. Open door after elevator arrives.
3. Wait for manual confirmation that robot has entered.
4. Set amrincar=1.
5. Send destination floor.
6. Close door and start moving.
7. Open door after elevator arrives at destination.
8. Wait for manual confirmation that robot has exited.
9. Set amrincar=0.
10. Close door and clear state.
"""

from __future__ import annotations

from hitachi_cn.client import CNClient
from hitachi_cn.config import clone_config
from hitachi_cn.errors import CNAPIError
from hitachi_cn.logger import Logger
from hitachi_cn.parsers import single_liftstatus
from hitachi_cn.workflows import (
    reset_lift_state,
    run_snapshot,
    send_command_and_wait_registration,
    wait_until,
)


CONFIG = clone_config(
    BASE_URL="http://192.168.88.254:8081",
    USERNAME="WVCOND",
    PASSWORD="WV12345",
    VERIFY_TLS=False,
    LIFT_ID=1,
    REQUEST_FLOOR=1,
    DEST_FLOOR=2,
    USE_REAR=False,
    RUN_SNAPSHOT=False,
    DRY_RUN=False,
    CONFIRM_BEFORE_MOVE=True,
    ALLOW_NON_NORMAL_MODE=False,
    NORMAL_OPERATION_MODE=4,
    POLL_INTERVAL_SEC=0.25,
    STABLE_N=2,
    REGISTER_TIMEOUT_SEC=10.0,
    CALL_TIMEOUT_SEC=120.0,
    DEST_TIMEOUT_SEC=300.0,
    DOOR_OPEN_TIMEOUT_SEC=30.0,
    CLOSE_DOOR_TIMEOUT_SEC=45.0,
    RESET_BEFORE_START=True,
    RESET_AFTER_FINISH=True,
)


def main() -> None:
    logger = Logger()
    logger.info("--- Hitachi CN Manual Robot Runner ---")
    client = CNClient(CONFIG, logger)
    client.login()

    lift_id = int(CONFIG["LIFT_ID"])
    request_floor = int(CONFIG["REQUEST_FLOOR"])
    dest_floor = int(CONFIG["DEST_FLOOR"])
    use_rear = bool(CONFIG["USE_REAR"])
    dry_run = bool(CONFIG["DRY_RUN"])
    poll_interval = float(CONFIG["POLL_INTERVAL_SEC"])
    stable_n = int(CONFIG["STABLE_N"])
    register_timeout = float(CONFIG["REGISTER_TIMEOUT_SEC"])
    normal_mode = int(CONFIG["NORMAL_OPERATION_MODE"])

    req_key = "rearrequestfloor" if use_rear else "requestfloor"
    dst_key = "reardestinationfloor" if use_rear else "destinationfloor"
    door_cmd = "rearopen" if use_rear else "frontopen"
    door_status_field = "door2Opened" if use_rear else "door1Opened"

    state = single_liftstatus(client.get_status(lift_id), lift_id=lift_id)
    mode = int(state.get("liftOperationMode", -1))
    if mode != normal_mode and not bool(CONFIG["ALLOW_NON_NORMAL_MODE"]):
        raise CNAPIError(f"Lift mode is {mode}, expected normal mode {normal_mode}.")

    if bool(CONFIG["RUN_SNAPSHOT"]):
        run_snapshot(client, logger, lift_id)

    if not dry_run and bool(CONFIG["RESET_BEFORE_START"]):
        reset_lift_state(client, logger, lift_id, "Pre-flight")

    try:
        logger.info(f"=== STAGE A: CALL LIFT TO FLOOR {request_floor} ===")
        if bool(CONFIG["CONFIRM_BEFORE_MOVE"]) and not dry_run:
            input(f">>> [Confirm] Press ENTER to send {req_key}={request_floor}...")

        send_command_and_wait_registration(
            client,
            logger,
            lift_id,
            {req_key: request_floor},
            dry_run=dry_run,
            poll_interval_sec=poll_interval,
            stable_n=stable_n,
            timeout_sec=register_timeout,
        )

        if not dry_run:
            wait_until(
                client,
                logger,
                lift_id,
                lambda status: int(status.get("liftArriveReqFloor", 0)) == 1,
                timeout_sec=float(CONFIG["CALL_TIMEOUT_SEC"]),
                poll_interval_sec=poll_interval,
                stable_n=stable_n,
                label="Arrived Request Floor",
            )

        logger.info("=== STAGE B: OPEN DOOR FOR ROBOT ENTRY ===")
        send_command_and_wait_registration(
            client,
            logger,
            lift_id,
            {door_cmd: 1},
            dry_run=dry_run,
            poll_interval_sec=poll_interval,
            stable_n=stable_n,
            timeout_sec=register_timeout,
        )

        if not dry_run:
            wait_until(
                client,
                logger,
                lift_id,
                lambda status: int(status.get(door_status_field, 0)) == 1,
                timeout_sec=float(CONFIG["DOOR_OPEN_TIMEOUT_SEC"]),
                poll_interval_sec=poll_interval,
                stable_n=stable_n,
                label="Door Open For Entry",
            )
            input(">>> [Manual] Robot has fully entered. Press ENTER to set amrincar=1...")

        logger.info("=== STAGE C: SET AMR IN CAR ===")
        client.put_command(lift_id, {"amrincar": 1}, dry_run=dry_run)

        logger.info("=== STAGE D: SEND DESTINATION FLOOR ===")
        send_command_and_wait_registration(
            client,
            logger,
            lift_id,
            {dst_key: dest_floor},
            dry_run=dry_run,
            poll_interval_sec=poll_interval,
            stable_n=stable_n,
            timeout_sec=register_timeout,
        )

        if not dry_run:
            input(">>> [Manual] Destination is set. Press ENTER to close door and start transit...")

        logger.info("=== STAGE E: CLOSE DOOR AND START TRANSIT ===")
        send_command_and_wait_registration(
            client,
            logger,
            lift_id,
            {door_cmd: 0},
            dry_run=dry_run,
            poll_interval_sec=poll_interval,
            stable_n=stable_n,
            timeout_sec=register_timeout,
        )
        if not dry_run:
            wait_until(
                client,
                logger,
                lift_id,
                lambda status: int(status.get(door_status_field, 0)) == 0,
                timeout_sec=float(CONFIG["CLOSE_DOOR_TIMEOUT_SEC"]),
                poll_interval_sec=poll_interval,
                stable_n=stable_n,
                label="Door Closed Before Transit",
            )

        if not dry_run:
            wait_until(
                client,
                logger,
                lift_id,
                lambda status: int(status.get("liftArriveDestFloor", 0)) == 1,
                timeout_sec=float(CONFIG["DEST_TIMEOUT_SEC"]),
                poll_interval_sec=poll_interval,
                stable_n=stable_n,
                label="Arrived Destination Floor",
            )

        logger.info("=== STAGE F: OPEN DOOR FOR ROBOT EXIT ===")
        send_command_and_wait_registration(
            client,
            logger,
            lift_id,
            {door_cmd: 1},
            dry_run=dry_run,
            poll_interval_sec=poll_interval,
            stable_n=stable_n,
            timeout_sec=register_timeout,
        )

        if not dry_run:
            wait_until(
                client,
                logger,
                lift_id,
                lambda status: int(status.get(door_status_field, 0)) == 1,
                timeout_sec=float(CONFIG["DOOR_OPEN_TIMEOUT_SEC"]),
                poll_interval_sec=poll_interval,
                stable_n=stable_n,
                label="Door Open For Exit",
            )
            input(">>> [Manual] Robot has fully exited. Press ENTER to set amrincar=0...")

        logger.info("=== STAGE G: CLEAR AMR IN CAR ===")
        client.put_command(lift_id, {"amrincar": 0}, dry_run=dry_run)

        if not dry_run:
            input(">>> [Manual] amrincar is cleared. Press ENTER to close door and finish...")

        logger.info("=== STAGE H: CLOSE DOOR AND CLEAR STATE ===")
        send_command_and_wait_registration(
            client,
            logger,
            lift_id,
            {door_cmd: 0},
            dry_run=dry_run,
            poll_interval_sec=poll_interval,
            stable_n=stable_n,
            timeout_sec=register_timeout,
        )

        if not dry_run:
            wait_until(
                client,
                logger,
                lift_id,
                lambda status: int(status.get(door_status_field, 0)) == 0,
                timeout_sec=float(CONFIG["CLOSE_DOOR_TIMEOUT_SEC"]),
                poll_interval_sec=poll_interval,
                stable_n=stable_n,
                label="Door Closed After Exit",
            )

        if not dry_run:
            send_command_and_wait_registration(
                client,
                logger,
                lift_id,
                {req_key: 0, dst_key: 0},
                dry_run=False,
                poll_interval_sec=poll_interval,
                stable_n=stable_n,
                timeout_sec=register_timeout,
            )

        logger.info("=== MANUAL ROBOT FLOW FINISHED ===")
    except KeyboardInterrupt:
        logger.error("Interrupted by user.")
        raise
    finally:
        if not dry_run and bool(CONFIG["RESET_AFTER_FINISH"]):
            reset_lift_state(client, logger, lift_id, "Final Reset")


if __name__ == "__main__":
    main()
