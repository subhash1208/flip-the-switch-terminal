"""Shared machine-side loop for the scripted agents.

These stand in for the real Claude Code (Alice) and Codex (Bob) agents on the keyless judge path.
They are NOT LLMs and make no decisions: they answer the Bailiff's requests by running allow-listed
argv lists locally (no shell) and report the result. They re-check the allow-list themselves and
refuse anything else.

Approval is automatic, and it is labelled as such. Every reply carries the line
`APPROVAL: auto-approved (scripted agent, no human)`. No human approved anything on this path.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from bailiff.agent import Conn
from bailiff.allowlist import is_allowed, is_allowed_overlay
from bailiff.events import REQ, RES, Event, read_wire
from bailiff.redact import SECRET_WORDS

APPROVAL = "APPROVAL: auto-approved (scripted agent, no human)"
RUN_TIMEOUT_S = 20.0
_SECRET_ENV = re.compile("|".join(SECRET_WORDS), re.IGNORECASE)

Runner = Callable[[list[str], dict[str, str]], Awaitable[dict[str, Any]]]


async def run_local(argv: list[str], overlay: dict[str, str]) -> dict[str, Any]:
    """Run argv with no shell, in MACHINE_WORKDIR, with a timeout, merging the overlay."""
    env = {k: v for k, v in os.environ.items() if not _SECRET_ENV.search(k)}
    env.update(overlay)
    cwd = os.environ.get("MACHINE_WORKDIR", ".")
    try:
        done = await asyncio.to_thread(
            subprocess.run,
            argv,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"exit_code": None, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}
    return {"exit_code": done.returncode, "stdout": done.stdout, "stderr": done.stderr}


def fixture_runner(path: Path) -> Runner:
    """Canned command output from a fixture file, keyed by the argv string.

    Overlays (TZ, NODE_OPTIONS) are ignored by the fixture on purpose: they are decoys.
    An unknown command returns exit 127 so a missing fixture entry shows up as a failure.
    """
    commands: dict[str, dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))["commands"]

    async def run(argv: list[str], overlay: dict[str, str]) -> dict[str, Any]:
        key = " ".join(argv)
        hit = commands.get(key)
        if hit is None:
            return {"exit_code": 127, "stdout": "", "stderr": f"no canned output for: {key}"}
        return {
            "exit_code": hit["exit_code"],
            "stdout": hit.get("stdout", ""),
            "stderr": hit.get("stderr", ""),
        }

    return run


async def answer(req: dict[str, Any], machine: str, run: Runner) -> dict[str, Any]:
    """Answer one Bailiff request. Re-checks the allow-list and refuses anything outside it."""
    kind = req.get("kind")
    base: dict[str, Any] = {
        "request_id": req.get("request_id"),
        "machine": machine,
        "kind": kind,
        "exit_code": None,  # every reply carries it: the Bailiff's reply check keys on it
    }
    if kind == "attest":
        return {**base, "approval": APPROVAL}
    cmd = req.get("argv") if kind == "probe" else req.get("cmd")
    env = req.get("env") or {}
    if kind not in ("probe", "test", "ablation", "verify") or not isinstance(cmd, list):
        return {**base, "refused": "unknown request"}
    if not all(isinstance(a, str) for a in cmd) or not isinstance(env, dict):
        return {**base, "refused": "malformed request"}
    if not is_allowed(cmd) or not is_allowed_overlay(env):
        return {**base, "refused": "not on the allow-list"}
    return {
        **base,
        "approval": APPROVAL,
        **(await run(cmd, {str(k): str(v) for k, v in env.items()})),
    }


def _request_for(ev: Event, handle: str, machine: str) -> dict[str, Any] | None:
    if ev.type != "message" or ev.text is None or not ev.text.startswith(f"@{handle} "):
        return None
    req = read_wire(ev.text, REQ)
    return req if req is not None and req.get("machine") == machine else None


async def serve_machine(
    conn: Conn, room_id: str, machine: str, handle: str, run: Runner, bailiff: str = "bailiff"
) -> None:
    """Answer every request addressed to this machine's handle, until cancelled."""
    async for ev in conn.events():
        req = _request_for(ev, handle, machine)
        if req is None:
            continue
        reply = await answer(req, machine, run)
        await conn.post(
            room_id, f"@{bailiff} {RES} {json.dumps(reply, sort_keys=True)}\n{APPROVAL}"
        )
