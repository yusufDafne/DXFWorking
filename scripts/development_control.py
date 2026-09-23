#!/usr/bin/env python3
"""Control one-at-a-time system development tasks.

This tool manages a project-local task lock. It does not modify project design
context or generate DXF files.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEVELOPMENT_DIR = ROOT / "docs" / "development"
TASKS_PATH = DEVELOPMENT_DIR / "DEVELOPMENT_TASKS.md"
LOCK_PATH = DEVELOPMENT_DIR / "ACTIVE_TASK.lock"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_lock() -> dict | None:
    if not LOCK_PATH.exists():
        return None
    try:
        return json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid task lock: {LOCK_PATH}: {exc}") from exc


def claim(task_id: str, role: str, agent_id: str) -> None:
    if read_lock() is not None:
        current = read_lock()
        raise SystemExit(
            f"Task lock already held by {current['agent_id']} for {current['task_id']} "
            f"({current['role']}). Release it only after validation."
        )

    payload = {
        "task_id": task_id,
        "role": role,
        "agent_id": agent_id,
        "host": socket.gethostname(),
        "pid": os.getpid(),
        "started_at": now(),
    }
    DEVELOPMENT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(str(LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise SystemExit("Task lock was claimed concurrently; inspect ACTIVE_TASK.lock.") from exc
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2)
        stream.write("\n")
    print(json.dumps(payload, indent=2))


def release(task_id: str, agent_id: str) -> None:
    current = read_lock()
    if current is None:
        raise SystemExit("No active task lock exists.")
    if current["task_id"] != task_id or current["agent_id"] != agent_id:
        raise SystemExit("Only the lock owner may release this task lock.")
    LOCK_PATH.unlink()
    print(f"Released task lock: {task_id}")


def status() -> None:
    current = read_lock()
    if current is None:
        print("No active development task lock.")
        return
    print(json.dumps(current, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    claim_parser = subparsers.add_parser("claim")
    claim_parser.add_argument("task_id")
    claim_parser.add_argument("--role", required=True)
    claim_parser.add_argument("--agent-id", required=True)

    release_parser = subparsers.add_parser("release")
    release_parser.add_argument("task_id")
    release_parser.add_argument("--agent-id", required=True)

    subparsers.add_parser("status")
    args = parser.parse_args()

    if args.command == "claim":
        claim(args.task_id, args.role, args.agent_id)
    elif args.command == "release":
        release(args.task_id, args.agent_id)
    else:
        status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
