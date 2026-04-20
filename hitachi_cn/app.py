from __future__ import annotations

from typing import Any, Dict

from .client import CNClient
from .config import DEFAULT_FRAMEWORK_RUN
from .errors import CNAPIError
from .logger import Logger
from .utils import pretty
from .workflows import (
    run_call_test,
    reset_lift_state,
    run_demo_flow,
    run_door_test,
    run_snapshot,
    run_strict_trip_test,
)


def run_field_runner(cfg: Dict[str, Any]) -> Logger:
    logger = Logger()
    logger.info("--- Hitachi CN Field Runner ---")
    client = CNClient(cfg, logger)
    client.login()
    lift_id = int(cfg["LIFT_ID"])
    try:
        if bool(cfg.get("RUN_RESET_ONLY", False)):
            reset_lift_state(client, logger, lift_id, "MANUAL TRIGGER")
            return logger

        if bool(cfg.get("RUN_SNAPSHOT", False)):
            run_snapshot(client, logger, lift_id)

        if bool(cfg.get("RUN_DOOR_TEST", False)):
            if bool(cfg.get("CONFIRM_BEFORE_MOVE", False)):
                input(">>> Press ENTER to start DOOR TEST...")
            run_door_test(client, logger, lift_id, cfg)

        if bool(cfg.get("RUN_CALL_TEST", False)):
            if bool(cfg.get("CONFIRM_BEFORE_MOVE", False)):
                input(">>> Press ENTER to start CALL TEST...")
            run_call_test(client, logger, cfg)

        if bool(cfg.get("RUN_TRIP_TEST", False)):
            if bool(cfg.get("CONFIRM_BEFORE_MOVE", False)):
                input(">>> Press ENTER to start TRIP TEST...")
            run_strict_trip_test(client, logger, cfg)
    except KeyboardInterrupt:
        logger.error("Interrupted by user, attempting emergency reset.")
        reset_lift_state(client, logger, lift_id, "Emergency Stop")
    except Exception as exc:
        logger.error(f"Runner failed: {exc}")
        raise
    return logger


def run_framework_mode(cfg: Dict[str, Any], run_cfg: Dict[str, Any] | None = None) -> Logger:
    logger = Logger()
    client = CNClient(cfg, logger)
    mode_cfg = dict(DEFAULT_FRAMEWORK_RUN)
    if run_cfg:
        mode_cfg.update(run_cfg)
    mode = str(mode_cfg.get("MODE", "")).strip()

    if mode == "login":
        auth = client.login(force=True)
        logger.info(pretty({"public_id": auth.public_id, "token": auth.token, "login_time": auth.login_time}))
        return logger

    if mode == "status":
        logger.info(pretty(client.get_status(mode_cfg.get("LIFT_ID"))))
        return logger

    if mode == "config":
        logger.info(pretty(client.get_config(mode_cfg.get("LIFT_ID"))))
        return logger

    if mode == "command":
        lift_id = int(mode_cfg["COMMAND_LIFT_ID"])
        command = mode_cfg["COMMAND_JSON"]
        if not isinstance(command, dict):
            raise CNAPIError("RUN.COMMAND_JSON must be a dict")
        logger.info(pretty(client.put_command(lift_id, command)))
        return logger

    if mode == "demo_flow":
        client.login()
        run_demo_flow(client, logger, mode_cfg)
        return logger

    raise CNAPIError(f"Unknown RUN.MODE: {mode}")
