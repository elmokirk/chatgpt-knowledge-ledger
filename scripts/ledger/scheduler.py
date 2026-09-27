from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from .util import atomic_write, canonical_json, immutable_write

CONFIG = Path("09 - System/State/scheduler.config.json")
REGISTRY = Path("09 - System/Registries/Sync Run Registry.json")
LOCK = Path("09 - System/State/Weekly Sync.lock")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _now(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("--now must include a UTC offset")
    return result


def _week(value: str) -> str:
    year, week, _ = _now(value).date().isocalendar()
    return f"{year}-W{week:02d}"


def status(vault: Path, now: str) -> dict:
    week = _week(now)
    registry = _read(vault / REGISTRY)
    complete = registry.get("weeks", {}).get(week, {}).get("status") == "completed"
    return {"ok": True, "action": "noop" if complete else "due", "iso_week": week, "reason": "already_completed" if complete else "not_completed"}


def begin(vault: Path, now: str, account_id: str, project_ids: list[str]) -> dict:
    due = status(vault, now)
    if due["action"] == "noop":
        return due
    config = _read(vault / CONFIG)
    guard = config.get("identity_guard", {})
    expected = guard.get("expected_account_id")
    required = set(guard.get("required_chatgpt_project_ids", []))
    if not config.get("enabled"):
        return {"ok": False, "action": "abort", "reason": "scheduler_disabled", "iso_week": due["iso_week"]}
    if not expected or not required:
        return {"ok": False, "action": "abort", "reason": "identity_guard_incomplete", "iso_week": due["iso_week"]}
    if account_id != expected:
        return {"ok": False, "action": "abort", "reason": "account_mismatch", "iso_week": due["iso_week"]}
    if not required.issubset(set(project_ids)):
        return {"ok": False, "action": "abort", "reason": "workspace_sentinel_missing", "iso_week": due["iso_week"]}

    registry = _read(vault / REGISTRY)
    week = due["iso_week"]
    attempts = int(registry.get("weeks", {}).get(week, {}).get("attempts", 0)) + 1
    run_id = f"sync-{week}-{attempts:02d}"
    fingerprint = hashlib.sha256(canonical_json({"account_id": expected, "project_ids": sorted(required)})).hexdigest()
    lock = {"run_id": run_id, "iso_week": week, "started_at": now, "identity_fingerprint": fingerprint}
    lock_path = vault / LOCK
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        return {"ok": False, "action": "abort", "reason": "lock_exists", "iso_week": week}
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(lock, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")

    registry.setdefault("weeks", {})[week] = {"status": "running", "attempts": attempts, "run_id": run_id, "started_at": now, "identity_fingerprint": fingerprint}
    atomic_write(vault / REGISTRY, json.dumps(registry, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return {"ok": True, "action": "run", "iso_week": week, "run_id": run_id}


def finish(vault: Path, now: str, run_id: str, outcome: str, counts: dict, coverage_status: str) -> dict:
    if outcome not in {"completed", "failed", "blocked"}:
        raise ValueError("invalid outcome")
    lock_path = vault / LOCK
    lock = _read(lock_path)
    if lock.get("run_id") != run_id:
        raise ValueError("run_id does not own the lock")
    registry = _read(vault / REGISTRY)
    week = lock["iso_week"]
    entry = registry["weeks"][week]
    entry.update({"status": outcome, "completed_at": now, "counts": counts, "coverage_status": coverage_status})
    if outcome == "completed":
        registry["last_successful_run"] = run_id
    report = {"schema": "chatgpt-sync-run/v1", "run_id": run_id, "iso_week": week, "started_at": lock["started_at"], "completed_at": now, "status": outcome, "identity_fingerprint": lock["identity_fingerprint"], "counts": counts, "coverage_status": coverage_status}
    year = week[:4]
    immutable_write(vault / "09 - System" / "Runs" / year / f"{run_id}.json", json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    atomic_write(vault / REGISTRY, json.dumps(registry, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    lock_path.unlink()
    return {"ok": outcome == "completed", "action": "finished", "run_id": run_id, "status": outcome}
