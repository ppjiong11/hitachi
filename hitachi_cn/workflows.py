from __future__ import annotations

import time
from typing import Any, Callable, Dict

from .client import CNClient
from .errors import CNAPIError
from .logger import Logger
from .parsers import single_liftstatus
from .utils import pretty


REGISTERED_FIELD_BY_COMMAND = {
    "frontopen": "frontDoorOpenRegistered",
    "rearopen": "rearDoorOpenRegistered",
    "requestfloor": "frontReqFloorRegistered",
    "rearrequestfloor": "rearReqFloorRegistered",
    "destinationfloor": "frontDestFloorRegistered",
    "reardestinationfloor": "rearDestFloorRegistered",
}


def wait_until(
    client: CNClient,
    logger: Logger,
    lift_id: int,
    predicate: Callable[[Dict[str, Any]], bool],
    *,
    timeout_sec: float,
    poll_interval_sec: float,
    stable_n: int,
    label: str,
) -> Dict[str, Any]:
    logger.info(f"Waiting: {label} (timeout={timeout_sec}s, poll={poll_interval_sec}s, stable_n={stable_n})")
    started_at = time.time()
    ok_count = 0
    last_status: Dict[str, Any] = {}
    while True:
        last_status = client.get_status(lift_id=lift_id)
        current = single_liftstatus(last_status, lift_id=lift_id)
        if predicate(current):
            ok_count += 1
        else:
            ok_count = 0

        if ok_count >= stable_n:
            logger.info(f"Condition met: {label}")
            return last_status

        if time.time() - started_at > timeout_sec:
            raise CNAPIError(f"Timeout waiting: {label}. Last status:\n{pretty(last_status)}")

        time.sleep(poll_interval_sec)


def send_command_and_wait_registration(
    client: CNClient,
    logger: Logger,
    lift_id: int,
    command: Dict[str, Any],
    *,
    dry_run: bool,
    poll_interval_sec: float,
    stable_n: int,
    timeout_sec: float,
) -> Dict[str, Any]:
    logger.info(f"SEND COMMAND payload={command} lift_id={lift_id} dry_run={dry_run}")
    response = client.put_command(lift_id, command, dry_run=dry_run)
    if dry_run:
        return response

    for key, value in command.items():
        registered_field = REGISTERED_FIELD_BY_COMMAND.get(key)
        if not registered_field:
            continue
        expected = 1 if int(value) != 0 else 0
        wait_until(
            client,
            logger,
            lift_id,
            lambda status, field=registered_field, target=expected: int(status.get(field, 0)) == target,
            timeout_sec=timeout_sec,
            poll_interval_sec=poll_interval_sec,
            stable_n=stable_n,
            label=f"{registered_field} == {expected}",
        )

    return response


def reset_lift_state(client: CNClient, logger: Logger, lift_id: int, label: str = "Cleanup") -> None:
    logger.info(f"--- RESET LIFT STATE [{label}] ---")
    reset_command = {
        "requestfloor": 0,
        "destinationfloor": 0,
        "rearrequestfloor": 0,
        "reardestinationfloor": 0,
        "frontopen": 0,
        "rearopen": 0,
        "amrincar": 0,
        "hallcalldisable": 0,
    }
    try:
        client.put_command(lift_id, reset_command)
    except Exception as exc:
        logger.error(f"Reset failed: {exc}")


def run_snapshot(client: CNClient, logger: Logger, lift_id: int) -> None:
    logger.info("=== SNAPSHOT START ===")
    status_single = client.get_status(lift_id=lift_id)
    logger.info("Status(single lift):\n" + pretty(status_single))
    client.get_status(lift_id=None)
    config_single = client.get_config(lift_id=lift_id)
    logger.info("Config(single lift):\n" + pretty(config_single))
    client.get_config(lift_id=None)

    current = single_liftstatus(status_single, lift_id=lift_id)
    logger.info(
        "Analysis: "
        f"Mode={current.get('liftOperationMode')}, "
        f"Ready={current.get('amrReady')}, "
        f"CurrentFloor={current.get('liftCurrentFloor')}"
    )
    logger.info("=== SNAPSHOT END ===")


def run_door_test(client: CNClient, logger: Logger, lift_id: int, cfg: Dict[str, Any]) -> None:
    logger.info("=== DOOR TEST START ===")
    use_rear = bool(cfg["USE_REAR"])
    door_cmd = "rearopen" if use_rear else "frontopen"
    door_status_field = "door2Opened" if use_rear else "door1Opened"
    action = str(cfg.get("DOOR_TEST_ACTION", "cycle")).strip().lower()
    action_map = {
        "1": "open",
        "open": "open",
        "0": "close",
        "close": "close",
        "cycle": "cycle",
    }
    action = action_map.get(action, action)
    dry_run = bool(cfg["DRY_RUN"])
    poll_interval = float(cfg["POLL_INTERVAL_SEC"])
    stable_n = int(cfg["STABLE_N"])
    register_timeout = float(cfg.get("REGISTER_TIMEOUT_SEC", 10.0))
    if action not in {"open", "close", "cycle"}:
        raise CNAPIError(f"Unknown DOOR_TEST_ACTION: {action}")

    try:
        if action in {"open", "cycle"}:
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
                    timeout_sec=20.0,
                    poll_interval_sec=poll_interval,
                    stable_n=stable_n,
                    label="Door Open",
                )

        if action == "open":
            logger.info(f"Door open command sent. Keep-open time is managed by the controller until you send {door_cmd}=0.")
            logger.info("=== DOOR TEST END ===")
            return

        if action == "cycle" and not dry_run:
            time.sleep(float(cfg["DOOR_HOLD_SEC"]))

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
                timeout_sec=45.0,
                poll_interval_sec=poll_interval,
                stable_n=stable_n,
                label="Door Closed",
            )
    finally:
        if not dry_run and action == "cycle":
            send_command_and_wait_registration(
                client,
                logger,
                lift_id,
                {door_cmd: 0},
                dry_run=False,
                poll_interval_sec=poll_interval,
                stable_n=stable_n,
                timeout_sec=register_timeout,
            )
    logger.info("=== DOOR TEST END ===")


def run_call_test(client: CNClient, logger: Logger, cfg: Dict[str, Any]) -> None:
    lift_id = int(cfg["LIFT_ID"])
    request_floor = int(cfg["REQUEST_FLOOR"])
    use_rear = bool(cfg["USE_REAR"])
    dry_run = bool(cfg["DRY_RUN"])
    poll_interval = float(cfg["POLL_INTERVAL_SEC"])
    stable_n = int(cfg["STABLE_N"])
    register_timeout = float(cfg.get("REGISTER_TIMEOUT_SEC", 10.0))
    normal_mode = int(cfg.get("NORMAL_OPERATION_MODE", 4))
    clear_after_test = bool(cfg.get("CLEAR_CALL_AFTER_TEST", True))
    wait_arrival = bool(cfg.get("WAIT_FOR_CALL_ARRIVAL", True))
    req_key = "rearrequestfloor" if use_rear else "requestfloor"

    logger.info(f"=== CALL TEST START Lift {lift_id}: request_floor={request_floor} ===")
    state = single_liftstatus(client.get_status(lift_id), lift_id=lift_id)
    mode = int(state.get("liftOperationMode", -1))
    if mode != normal_mode and not bool(cfg["ALLOW_NON_NORMAL_MODE"]):
        raise CNAPIError(f"Lift mode is {mode}, expected normal mode {normal_mode}.")

    if bool(cfg["CONFIRM_BEFORE_MOVE"]) and not dry_run:
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

    if not dry_run and wait_arrival:
        wait_until(
            client,
            logger,
            lift_id,
            lambda status: int(status.get("liftArriveReqFloor", 0)) == 1,
            timeout_sec=float(cfg.get("CALL_TIMEOUT_SEC", 120.0)),
            poll_interval_sec=poll_interval,
            stable_n=stable_n,
            label="Arrived Request Floor",
        )

    if not dry_run and clear_after_test:
        send_command_and_wait_registration(
            client,
            logger,
            lift_id,
            {req_key: 0},
            dry_run=False,
            poll_interval_sec=poll_interval,
            stable_n=stable_n,
            timeout_sec=register_timeout,
        )

    logger.info("=== CALL TEST END ===")


def run_strict_trip_test(client: CNClient, logger: Logger, cfg: Dict[str, Any]) -> None:
    lift_id = int(cfg["LIFT_ID"])
    req_floor = int(cfg["REQUEST_FLOOR"])
    dst_floor = int(cfg["DEST_FLOOR"])
    dry_run = bool(cfg["DRY_RUN"])
    use_rear = bool(cfg["USE_REAR"])
    req_key = "rearrequestfloor" if use_rear else "requestfloor"
    dst_key = "reardestinationfloor" if use_rear else "destinationfloor"
    door_cmd = "rearopen" if use_rear else "frontopen"
    door_status_field = "door2Opened" if use_rear else "door1Opened"
    poll_interval = float(cfg["POLL_INTERVAL_SEC"])
    stable_n = int(cfg["STABLE_N"])
    register_timeout = float(cfg.get("REGISTER_TIMEOUT_SEC", 10.0))
    normal_mode = int(cfg.get("NORMAL_OPERATION_MODE", 4))

    logger.info(f"=== TRIP TEST START Lift {lift_id}: {req_floor} -> {dst_floor} ===")
    state = single_liftstatus(client.get_status(lift_id), lift_id=lift_id)
    mode = int(state.get("liftOperationMode", -1))
    if mode != normal_mode and not bool(cfg["ALLOW_NON_NORMAL_MODE"]):
        raise CNAPIError(f"Lift mode is {mode}, expected normal mode {normal_mode}.")

    if not dry_run:
        reset_lift_state(client, logger, lift_id, "Pre-flight")
        time.sleep(1.0)

    try:
        logger.info(f"--- Stage A: Pickup at {req_floor} ---")
        if bool(cfg["CONFIRM_BEFORE_MOVE"]) and not dry_run:
            input(f">>> [Confirm] Press ENTER to request pickup at {req_floor}...")
        send_command_and_wait_registration(
            client,
            logger,
            lift_id,
            {req_key: req_floor},
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
                timeout_sec=120.0,
                poll_interval_sec=poll_interval,
                stable_n=stable_n,
                label="Arrived Pickup",
            )
            send_command_and_wait_registration(
                client,
                logger,
                lift_id,
                {door_cmd: 1},
                dry_run=False,
                poll_interval_sec=poll_interval,
                stable_n=stable_n,
                timeout_sec=register_timeout,
            )
            wait_until(
                client,
                logger,
                lift_id,
                lambda status: int(status.get(door_status_field, 0)) == 1,
                timeout_sec=30.0,
                poll_interval_sec=poll_interval,
                stable_n=stable_n,
                label="Door Fully Open",
            )

        send_command_and_wait_registration(
            client,
            logger,
            lift_id,
            {req_key: 0, door_cmd: 1},
            dry_run=dry_run,
            poll_interval_sec=poll_interval,
            stable_n=stable_n,
            timeout_sec=register_timeout,
        )

        logger.info(f"--- Stage B: Transit to {dst_floor} ---")
        if not dry_run:
            input(">>> [Check] Robot enters car. Press ENTER to GO...")

        client.put_command(lift_id, {"amrincar": 1}, dry_run=dry_run)
        send_command_and_wait_registration(
            client,
            logger,
            lift_id,
            {dst_key: dst_floor},
            dry_run=dry_run,
            poll_interval_sec=poll_interval,
            stable_n=stable_n,
            timeout_sec=register_timeout,
        )
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
                lambda status: int(status.get("liftArriveDestFloor", 0)) == 1,
                timeout_sec=300.0,
                poll_interval_sec=poll_interval,
                stable_n=stable_n,
                label="Arrived Destination",
            )
            send_command_and_wait_registration(
                client,
                logger,
                lift_id,
                {door_cmd: 1},
                dry_run=False,
                poll_interval_sec=poll_interval,
                stable_n=stable_n,
                timeout_sec=register_timeout,
            )
            wait_until(
                client,
                logger,
                lift_id,
                lambda status: int(status.get(door_status_field, 0)) == 1,
                timeout_sec=30.0,
                poll_interval_sec=poll_interval,
                stable_n=stable_n,
                label="Door Fully Open (Dest)",
            )

        logger.info("--- Stage C: Exit ---")
        send_command_and_wait_registration(
            client,
            logger,
            lift_id,
            {dst_key: 0, door_cmd: 1},
            dry_run=dry_run,
            poll_interval_sec=poll_interval,
            stable_n=stable_n,
            timeout_sec=register_timeout,
        )
        if not dry_run:
            time.sleep(5.0)
        logger.info("Trip test success.")
    except Exception as exc:
        logger.error(f"Trip test failed: {exc}")
        raise
    finally:
        if not dry_run:
            reset_lift_state(client, logger, lift_id, "Final Reset")


def run_demo_flow(client: CNClient, logger: Logger, run_cfg: Dict[str, Any]) -> None:
    lift_id = int(run_cfg["FLOW_LIFT_ID"])
    request_floor = int(run_cfg["REQUEST_FLOOR"])
    dest_floor = int(run_cfg["DEST_FLOOR"])
    use_rear = bool(run_cfg["USE_REAR"])
    hall_disable = bool(run_cfg["HALL_CALL_DISABLE"])
    hold_door = bool(run_cfg["HOLD_DOOR"])
    poll = float(run_cfg["POLL_INTERVAL_SEC"])
    t_req = float(run_cfg["TIMEOUT_REQ_SEC"])
    t_dst = float(run_cfg["TIMEOUT_DEST_SEC"])

    door_open_field = "door2Opened" if use_rear else "door1Opened"
    request_key = "rearrequestfloor" if use_rear else "requestfloor"
    dest_key = "reardestinationfloor" if use_rear else "destinationfloor"
    door_cmd_key = "rearopen" if use_rear else "frontopen"

    logger.info("=== DEMO FLOW Stage A ===")
    if hall_disable:
        client.put_command(lift_id, {"hallcalldisable": 1})
    client.put_command(lift_id, {request_key: request_floor})
    wait_until(
        client,
        logger,
        lift_id,
        lambda status: int(status.get("liftArriveReqFloor", 0)) == 1 and int(status.get(door_open_field, 0)) == 1,
        timeout_sec=t_req,
        poll_interval_sec=poll,
        stable_n=1,
        label="Arrive Request Floor + Door Open",
    )

    if hold_door:
        client.put_command(lift_id, {door_cmd_key: 1})

    input(">>> Confirm AMR entered the lift (press Enter)...")
    logger.info("=== DEMO FLOW Stage B ===")
    client.put_command(lift_id, {"amrincar": 1})
    client.put_command(lift_id, {dest_key: dest_floor})
    client.put_command(lift_id, {door_cmd_key: 0})
    wait_until(
        client,
        logger,
        lift_id,
        lambda status: int(status.get("liftArriveDestFloor", 0)) == 1 and int(status.get(door_open_field, 0)) == 1,
        timeout_sec=t_dst,
        poll_interval_sec=poll,
        stable_n=1,
        label="Arrive Destination + Door Open",
    )

    if hold_door:
        client.put_command(lift_id, {door_cmd_key: 1})

    input(">>> Confirm AMR exited the lift (press Enter)...")
    logger.info("=== DEMO FLOW Stage C ===")
    client.put_command(lift_id, {"amrincar": 0})
    client.put_command(lift_id, {door_cmd_key: 0})
    if hall_disable:
        client.put_command(lift_id, {"hallcalldisable": 0})
