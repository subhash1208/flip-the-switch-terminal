"""The Bailiff: a neutral arbiter that runs one ParityCourt case in a Switch room.

Run as an agent process:

    python -m bailiff.agent

Environment (values are never logged):
    BAILIFF_BASE_URL       the server's bridge address (GET /health should answer)
    BAILIFF_AGENT_ID       this agent's id
    BAILIFF_API_KEY        this agent's own API key
    BAILIFF_CONNECTION_ID  a UUID, reused on every reconnect
    ROOM_ID                the room to claim and work in
    RECEIPT_PATH           where receipt.json is written (default ./receipt.json)
    ALICE_HANDLE, BOB_HANDLE   machine agents' handles (default alice-claude, bob-codex)
    STEP_TIMEOUT           seconds to wait for each machine reply (default 60)
    BAILIFF_TURN_CAP       optional whole number; past it the case stops and an inconclusive
                           receipt is written (default off)

A human opens a case with `!open case <title>` or `@bailiff open case <title>`. The Bailiff then
creates the case-file room document, asks each machine agent for allow-listed probes, diffs the
fingerprints, runs one ablation on Bob, asks Bob to re-run the test with the culprit applied,
collects attestations, and writes the receipt. It holds no approval power of its own.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from bailiff.ablation import NOT_ABLATED_MASKED, classify, plan_ablation
from bailiff.allowlist import is_allowed, is_allowed_overlay
from bailiff.events import REQ, RES, Event, message_id, read_wire
from bailiff.fingerprint import diff_fingerprints, parse_fingerprint, raw_compared
from bailiff.models import StepResult, Suspect
from bailiff.receipt import build_receipt, save_receipt, step_to_dict, validate_receipt
from bailiff.redact import mask_bounded, mask_secret_lines, redact
from bailiff.state import CaseState, TurnCapExceeded
from bailiff.transport import ReconnectExhausted, SwitchConnection, TakenOver

MACHINES = {"alice": "alice-claude", "bob": "bob-codex"}
PROBES: dict[str, list[str]] = {
    "uname": ["uname", "-a"],
    "node": ["node", "-v"],
    "env": ["env"],
    "ignorecase": ["git", "config", "core.ignorecase"],
    "tz": ["printenv", "TZ"],
    "node_options": ["printenv", "NODE_OPTIONS"],
}
TEST_CMD = ["node", "test.js"]
STEP_TIMEOUT = 60.0
TRIGGERS = ("!open case", "@bailiff open case")
DOC_NOTE = "Case file kept by the Bailiff. Only the Bailiff edits it."


class Conn(Protocol):
    """What the flow needs from a connection: SwitchConnection and FakeConnection both fit."""

    malformed: int

    def events(self) -> AsyncIterator[Event]: ...

    async def op(self, operation: str, /, **args: Any) -> dict[str, Any]: ...

    async def post(self, room_id: str, text: str) -> int: ...


Inbox = asyncio.Queue[Event | BaseException]


@dataclass
class _Ctx:
    conn: Conn
    state: CaseState
    inbox: Inbox
    machines: dict[str, str]
    probes: dict[str, list[str]]
    test_cmd: list[str]
    timeout: float


async def _pump(conn: Conn, inbox: Inbox, transcript: list[tuple[str, str]]) -> None:
    """Feed events into a queue. Timeouts then never cancel the event generator itself.

    Each message is also kept in the transcript, masked as the room stores it, for the receipt's
    privacy record.
    """
    try:
        async for ev in conn.events():
            if ev.text is not None:
                transcript.append((ev.sender or "unknown", mask_bounded(ev.text)[0]))
            inbox.put_nowait(ev)
    except Exception as exc:  # e.g. TakenOver: hand it to the flow so it stops
        inbox.put_nowait(exc)


async def _stop(pump: asyncio.Task[None]) -> None:
    pump.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await pump


async def _next(inbox: Inbox) -> Event:
    item = await inbox.get()
    if isinstance(item, BaseException):
        raise item
    return item


def _trigger_title(ev: Event) -> str | None:
    if ev.type != "message" or ev.text is None:
        return None
    text = ev.text.strip()
    for trigger in TRIGGERS:
        if text.lower().startswith(trigger):
            return text[len(trigger) :].strip(" :#-") or "untitled"
    return None


def _suspect_dict(s: Suspect) -> dict[str, Any]:
    return {
        "name": s.name,
        "alice": s.alice,
        "bob": s.bob,
        "verdict": s.verdict,
        "note": s.note,
    }


def _code(reply: dict[str, Any] | None) -> int | None:
    value = reply.get("exit_code") if reply else None
    return value if isinstance(value, int) else None


def _not_run(machine: str, cmd: list[str]) -> dict[str, Any]:
    return {
        "machine": machine,
        "cmd": list(cmd),
        "exit_code": None,
        "outcome": "fail",
        "stderr_excerpt": "not run: the case stopped before this test ran",
    }


async def _write_doc(ctx: _Ctx) -> None:
    """Create the case file once, then update it. Only this agent may edit a document it created."""
    s = ctx.state
    text, hits = redact(s.to_room_document())
    s.doc_redactions = hits
    name = f"case-{s.case_id}"
    if s.doc_created:
        await ctx.conn.op("update_room_document", name=name, content=text)
    else:
        await ctx.conn.op("create_room_document", name=name, content=text, instructions=DOC_NOTE)
        s.doc_created = True


async def _advance(ctx: _Ctx, new: str) -> None:
    ctx.state.transition(new)
    await _write_doc(ctx)


async def _allowed(
    ctx: _Ctx, machine: str, argv: list[str], env: dict[str, str] | None = None
) -> bool:
    if is_allowed(argv) and (env is None or is_allowed_overlay(env)):
        return True
    ctx.state.redactions += await ctx.conn.post(
        ctx.state.room_id, f"REFUSED for {machine}: {' '.join(argv)} is not on the allow-list"
    )
    return False


async def _ask(
    ctx: _Ctx, machine: str, kind: str, **fields: Any
) -> tuple[Event, dict[str, Any]] | None:
    """Send one request to a machine agent and wait for its matching reply. None on timeout."""
    request_id = uuid.uuid4().hex
    payload = {"kind": kind, "request_id": request_id, "machine": machine, **fields}
    ctx.state.turn()
    body = json.dumps(payload, sort_keys=True)
    ctx.state.redactions += await ctx.conn.post(
        ctx.state.room_id, f"@{ctx.machines[machine]} {REQ} {body}"
    )
    try:
        async with asyncio.timeout(ctx.timeout):
            while True:
                ev = await _next(ctx.inbox)
                reply = read_wire(ev.text, RES)
                if not (
                    reply
                    and reply.get("request_id") == request_id
                    and reply.get("machine") == machine
                ):
                    continue
                if ev.sender == ctx.machines[machine]:
                    return ev, reply
                ctx.conn.malformed += 1  # a reply from anyone but that machine's own agent
    except TimeoutError:
        return None


async def _probe(ctx: _Ctx, machine: str, name: str, argv: list[str]) -> str | None:
    if not await _allowed(ctx, machine, argv):
        ctx.state.probes.append(
            {
                "machine": machine,
                "probe": name,
                "argv": argv,
                "exit_code": None,
                "outcome": "refused",
            }
        )
        return None
    got = await _ask(ctx, machine, "probe", argv=argv)
    reply = got[1] if got else None
    code = _code(reply)
    ctx.state.probes.append(
        {
            "machine": machine,
            "probe": name,
            "argv": argv,
            "exit_code": code,
            "outcome": "pass" if code == 0 else "fail",
        }
    )
    if reply is None:
        return None
    raw = str(reply.get("stdout", ""))
    ctx.state.redactions += mask_bounded(raw)[1]
    return raw


async def _run_test(ctx: _Ctx, machine: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "machine": machine,
        "cmd": list(ctx.test_cmd),
        "exit_code": None,
        "outcome": "fail",
        "stderr_excerpt": "",
    }
    if not await _allowed(ctx, machine, ctx.test_cmd):
        return record
    got = await _ask(ctx, machine, "test", cmd=ctx.test_cmd)
    if got is None:
        return record
    code = _code(got[1])
    # Mask the whole stderr before the tail is taken: a tail cut first can start inside a secret
    # and lose the key that would have masked it.
    masked, line_hits = mask_secret_lines(str(got[1].get("stderr", "")))
    text, hits = redact(masked)
    ctx.state.redactions += line_hits + hits
    record.update(
        exit_code=code, outcome="pass" if code == 0 else "fail", stderr_excerpt=text[-400:]
    )
    return record


async def _fingerprint(
    ctx: _Ctx,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Masked fingerprints for display, and the raw compared values that decide equality."""
    fingerprints: dict[str, dict[str, Any]] = {}
    raw: dict[str, dict[str, Any]] = {}
    for machine in ctx.machines:
        collected: dict[str, str] = {}
        for name, argv in ctx.probes.items():
            out = await _probe(ctx, machine, name, argv)
            if out is not None:
                collected[" ".join(argv)] = out
        fingerprints[machine] = parse_fingerprint(machine, collected)
        raw[machine] = raw_compared(collected)
        ctx.state.machines[machine] = {
            "agent_handle": ctx.machines[machine],
            "fingerprint": fingerprints[machine],
        }
    ctx.state.baseline = await _run_test(ctx, "alice")
    ctx.state.failure = await _run_test(ctx, "bob")
    return fingerprints, raw


async def _ablate(ctx: _Ctx, suspects: list[Suspect]) -> dict[str, Any] | None:
    """Run each planned step on Bob. Returns the first step that passes, if any."""
    results: list[StepResult] = []
    for step in plan_ablation(suspects, failing_machine="bob", base=None):
        cmd, env = list(step.runner.cmd), dict(step.runner.env)
        got = None
        if await _allowed(ctx, "bob", cmd, env):
            got = await _ask(ctx, "bob", "ablation", cmd=cmd, env=env)
        code = _code(got[1] if got else None)
        outcome = "pass" if code == 0 else "fail"
        ctx.state.steps.append(step_to_dict(step, code, outcome))
        results.append(StepResult(id=step.id, exit_code=code, outcome=outcome, matched=True))
    classified = classify(suspects, results)
    ctx.state.suspects = [_suspect_dict(s) for s in classified]
    culprit_id = next(
        (
            f"ablation-{index}"
            for index, s in enumerate(classified, start=1)
            if s.verdict == "culprit"
        ),
        None,
    )
    return next((rec for rec in ctx.state.steps if rec["id"] == culprit_id), None)


async def _verify(ctx: _Ctx, culprit: dict[str, Any] | None) -> None:
    """Re-run the failing test on Bob with the culprit applied."""
    if culprit is None:
        return
    cmd, env = list(culprit["runner"]["cmd"]), dict(culprit["runner"]["env"])
    got = None
    if await _allowed(ctx, "bob", cmd, env):
        got = await _ask(ctx, "bob", "verify", cmd=cmd, env=env)
    reply = got[1] if got else None
    code = _code(reply)
    ctx.state.fix = {
        "branch": reply.get("branch") if reply else None,
        "verified_on": "bob",
        "outcome": "pass" if code == 0 else "fail",
    }


async def _attest(ctx: _Ctx) -> None:
    for machine in ctx.machines:
        got = await _ask(ctx, machine, "attest", verdict=ctx.state.verdict)
        if got is None:
            continue
        ev, reply = got
        approval = reply.get("approval")
        ctx.state.attestations.append(
            {
                "machine": machine,
                "owner": ev.sender or "unknown",
                "at": datetime.now(UTC).isoformat(timespec="seconds"),
                "approval_message_id": message_id(ev),
                "approval": approval if isinstance(approval, str) else None,
            }
        )


async def _run(ctx: _Ctx) -> dict[str, Any]:
    s = ctx.state
    try:
        await _write_doc(ctx)
        await _advance(ctx, "fingerprinting")
        fingerprints, raw = await _fingerprint(ctx)
        await _advance(ctx, "diffing")
        suspects = diff_fingerprints(
            fingerprints["alice"], fingerprints["bob"], raw["alice"], raw["bob"]
        )
        s.suspects = [_suspect_dict(x) for x in suspects]
        await _advance(ctx, "ablating")
        culprit = await _ablate(ctx, suspects)
        s.culprit = (
            {"variable": culprit["variable"], "evidence_step": culprit["id"]} if culprit else None
        )
        await _advance(ctx, "verifying")
        await _verify(ctx, culprit)
        if s.culprit and s.fix:
            s.verdict = (
                f"culprit: {s.culprit['variable']} (step {s.culprit['evidence_step']}); "
                f"re-run on bob: {s.fix['outcome']}"
            )
        else:
            s.verdict = "no single culprit isolated"
        await _advance(ctx, "attested")
        await _attest(ctx)
    except TurnCapExceeded as exc:
        s.verdict = f"stopped: {exc}"
        s.inconclusive_reason = f"stopped at the turn cap: {exc}"
    s.malformed = ctx.conn.malformed
    ablated = [step for step in s.steps if not step["variable"].endswith(" (no-op)")]
    if not ablated and s.inconclusive_reason is None:
        masked = [x["name"] for x in s.suspects if x["note"] == NOT_ABLATED_MASKED]
        if masked:
            s.inconclusive_reason = f"not ablated (value masked): {', '.join(masked)}"
        elif s.suspects:
            s.inconclusive_reason = "only no-op suspects differ: nothing could be ablated"
        else:
            s.inconclusive_reason = "no suspects: the fingerprints show no difference to ablate"
    if s.baseline is None:
        s.baseline = _not_run("alice", ctx.test_cmd)
    if s.failure is None:
        s.failure = _not_run("bob", ctx.test_cmd)
    s.transition("closed")
    await _write_doc(ctx)
    case = s.to_case_dict()
    problems = validate_receipt({**case, "schema_version": 1})
    if any(p.startswith("receipt.privacy") for p in problems):
        case.pop("privacy")
    return build_receipt(case)


async def serve(
    conn: Conn,
    room_id: str,
    *,
    machines: dict[str, str] = MACHINES,
    probes: dict[str, list[str]] = PROBES,
    test_cmd: list[str] = TEST_CMD,
    step_timeout: float = STEP_TIMEOUT,
    turn_cap: int | None = None,
    simulated: bool = False,
) -> dict[str, Any]:
    """Wait for a human to open a case, run it, and return the receipt dict."""
    inbox: Inbox = asyncio.Queue()
    transcript: list[tuple[str, str]] = []
    pump = asyncio.create_task(_pump(conn, inbox, transcript))
    try:
        while True:
            ev = await _next(inbox)
            title = _trigger_title(ev)
            if title is None:
                continue
            state = CaseState(
                case_id=f"case-{uuid.uuid4().hex[:8]}",
                room_id=room_id,
                title=title,
                opened_by=ev.sender or "unknown",
                turn_cap=turn_cap,
                simulated=simulated,
                transcript=transcript,
            )
            return await _run(_Ctx(conn, state, inbox, machines, probes, test_cmd, step_timeout))
    finally:
        await _stop(pump)


async def run_case(
    conn: Conn,
    state: CaseState,
    *,
    machines: dict[str, str] = MACHINES,
    probes: dict[str, list[str]] = PROBES,
    test_cmd: list[str] = TEST_CMD,
    step_timeout: float = STEP_TIMEOUT,
) -> dict[str, Any]:
    """Run the whole case on an already-opened state. Returns the receipt dict."""
    inbox: Inbox = asyncio.Queue()
    pump = asyncio.create_task(_pump(conn, inbox, state.transcript))
    try:
        return await _run(_Ctx(conn, state, inbox, machines, probes, test_cmd, step_timeout))
    finally:
        await _stop(pump)


async def _main_async() -> int:
    room_id = os.environ["ROOM_ID"]
    machines = {
        "alice": os.environ.get("ALICE_HANDLE", MACHINES["alice"]),
        "bob": os.environ.get("BOB_HANDLE", MACHINES["bob"]),
    }
    raw_cap = os.environ.get("BAILIFF_TURN_CAP")
    try:
        turn_cap = int(raw_cap) if raw_cap else None
    except ValueError:
        print("error: BAILIFF_TURN_CAP must be a whole number")
        return 2
    try:
        async with SwitchConnection(
            os.environ["BAILIFF_BASE_URL"],
            os.environ["BAILIFF_AGENT_ID"],
            os.environ["BAILIFF_API_KEY"],
            os.environ["BAILIFF_CONNECTION_ID"],
            [room_id],
        ) as conn:
            receipt = await serve(
                conn,
                room_id,
                machines=machines,
                step_timeout=float(os.environ.get("STEP_TIMEOUT", STEP_TIMEOUT)),
                turn_cap=turn_cap,
            )
    except TakenOver:
        print("taken over by another connection; stopping without reconnect")
        return 0
    except ReconnectExhausted as exc:
        print(f"giving up: {exc}")
        return 1
    except ValueError as exc:
        print(f"error: {exc}")
        return 1
    path = Path(os.environ.get("RECEIPT_PATH", "receipt.json"))
    save_receipt(receipt, str(path))
    print(f"receipt written to {path}")
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_main_async()))


if __name__ == "__main__":
    main()
