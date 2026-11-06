"""Local demo of the full ParityCourt case.

    python -m bailiff.demo --offline [--receipt PATH]
    BAILIFF_BASE_URL=... SWITCH_REGISTRATION_TOKEN=... \
        python -m bailiff.demo --live [--alice-agent NAME]

--offline runs the real Bailiff flow against an in-memory room. Alice (macOS-like, Node 22) and Bob
(Linux-like, Node 18) are scripted agents whose command output is canned in
bailiff/scripted/fixtures/. No Docker, no Switch, no LLM key.

--live runs the same case on a real Switch server (see bailiff/live.py), saves the evidence under
docs/evidence/, and replays it against Bob's fixture.

Either way the receipt is replayed; the exit code is 0 only if every step matches. Exit 2 means
missing config or no mode chosen.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

import httpx
import websockets

from bailiff.ablation import NOT_ABLATED_MASKED
from bailiff.agent import serve
from bailiff.live import BAILIFF, FIXTURES, LIVE, LiveError, run_live
from bailiff.models import Runner, RunnerFn
from bailiff.privacy import masked_example, placeholder_counts
from bailiff.receipt import save_receipt
from bailiff.replay import replay
from bailiff.scripted.fake_room import FakeRoom
from bailiff.scripted.runner import fixture_runner, serve_machine
from bailiff.transport import OpError, ReconnectExhausted, SwitchRefused

EVIDENCE = Path(__file__).resolve().parent.parent / "docs" / "evidence"
TRIGGER = "!open case export-service 500 AuthVerifierError on Ubuntu, passes on the Mac"


async def run_offline(fixtures: Path = FIXTURES) -> tuple[dict[str, Any], FakeRoom]:
    room = FakeRoom()
    bailiff = room.join("bailiff")
    machines = [
        asyncio.create_task(
            serve_machine(
                room.join("alice-claude"),
                room.room_id,
                "alice",
                "alice-claude",
                fixture_runner(fixtures / "alice.json"),
            )
        ),
        asyncio.create_task(
            serve_machine(
                room.join("bob-codex"),
                room.room_id,
                "bob",
                "bob-codex",
                fixture_runner(fixtures / "bob.json"),
            )
        ),
    ]
    try:
        room.publish("dana", TRIGGER)
        receipt = await asyncio.wait_for(
            serve(bailiff, room.room_id, step_timeout=5.0, simulated=True), timeout=60
        )
    finally:
        for task in machines:
            task.cancel()
        await asyncio.gather(*machines, return_exceptions=True)
    return receipt, room


def _fixture_replayer(path: Path) -> RunnerFn:
    """Replay each step on the fixture's canned output: the same answers the live run got."""
    run = fixture_runner(path)

    def replay_step(runner: Runner) -> tuple[int, str]:
        async def once() -> dict[str, Any]:
            return await run(list(runner.cmd), dict(runner.env))

        reply = asyncio.run(once())
        return int(reply["exit_code"]), str(reply["stderr"])

    return replay_step


def privacy_line(messages: list[tuple[str, str]]) -> str:
    """Say what the room transcript holds of the masking, by placeholder type."""
    counts = placeholder_counts(messages)
    if not counts:
        return "privacy: no placeholders seen in the room transcript"
    parts = ", ".join(f"{kind}={n}" for kind, n in counts.items())
    return f"privacy: masked {parts} (placeholders seen in the room transcript)"


def run_live_demo(evidence: Path = EVIDENCE, alice_agent: str | None = None) -> int:
    base = os.environ.get("BAILIFF_BASE_URL")
    token = os.environ.get("SWITCH_REGISTRATION_TOKEN")
    if not base or not token:
        print("error: --live needs BAILIFF_BASE_URL and SWITCH_REGISTRATION_TOKEN set")
        return 2
    print(f"LIVE: running against a real Switch server at {base} (not simulated)")
    if alice_agent:
        print(f"LIVE: Alice is @{alice_agent}, a real agent (not scripted)")
    try:
        receipt = asyncio.run(run_live(base, token, evidence, alice_agent=alice_agent))
    except (
        LiveError,
        OpError,
        SwitchRefused,
        ReconnectExhausted,
        TimeoutError,
        ValueError,
        OSError,
        httpx.HTTPError,
        websockets.WebSocketException,
    ) as exc:
        print(f"error: {exc}")
        return 1
    print(f"case {receipt['case_id']}: {len(receipt['suspects'])} suspects")
    print(f"culprit: {json.dumps(receipt['culprit'])}")
    print(f"fix re-run on bob: {json.dumps(receipt['fix'])}")
    path = evidence / "receipt.json"
    print(f"receipt written to {path}; transcript at {evidence / 'transcript.txt'}")
    try:
        results = replay(str(path), _fixture_replayer(FIXTURES / "bob.json"))
    except ValueError as exc:
        print(f"error: {exc}")
        return 1
    matched = sum(result.matched for result in results)
    print(f"replay: {matched}/{len(results)} steps matched (fixture replay, not Docker)")
    return 0 if matched == len(results) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bailiff.demo")
    parser.add_argument("--offline", action="store_true", help="run against the in-memory room")
    parser.add_argument("--live", action="store_true", help="run against a real Switch server")
    parser.add_argument(
        "--alice-agent", metavar="NAME", help="with --live: a Console agent plays Alice"
    )
    default_receipt = os.environ.get("RECEIPT_PATH", "receipt.json")
    parser.add_argument("--receipt", type=Path, default=Path(default_receipt))
    args = parser.parse_args(argv)
    if args.live:
        if args.alice_agent in {BAILIFF, *LIVE.values()}:
            print(f"error: --alice-agent {args.alice_agent} is a scripted pc-live name")
            return 2
        return run_live_demo(alice_agent=args.alice_agent)
    if args.alice_agent:
        print("error: --alice-agent needs --live")
        return 2
    if not args.offline:
        print("error: choose a mode: --offline or --live")
        return 2
    receipt, room = asyncio.run(run_offline())
    for sender, text in room.messages:
        print(f"[{sender}] {(text.splitlines() or [''])[0][:110]}")
    save_receipt(receipt, str(args.receipt))
    print("SIMULATED: in-process fake room, no Switch server")
    print(f"case {receipt['case_id']}: {len(receipt['suspects'])} suspects")
    not_ablated = [
        step["variable"].removesuffix(" (no-op)")
        for step in receipt["steps"]
        if step["variable"].endswith(" (no-op)")
    ]
    print(f"not ablated (no-op, verdict unknown): {', '.join(not_ablated) or 'none'}")
    masked = [s["name"] for s in receipt["suspects"] if s["note"] == NOT_ABLATED_MASKED]
    if masked:
        print(f"not ablated (value masked): {', '.join(masked)}")
    for suspect in receipt["suspects"]:
        print(f"  suspect {suspect['name']}: alice={suspect['alice']} bob={suspect['bob']}")
        print(f"    verdict: {suspect['verdict']}")
    for step in receipt["steps"]:
        print(f"  step {step['id']} ({step['variable']}) on {step['machine']}: {step['outcome']}")
    print(f"culprit: {json.dumps(receipt['culprit'])}")
    print(f"fix re-run on bob: {json.dumps(receipt['fix'])}")
    print(f"redactions: {receipt['redactions']}")
    print(privacy_line(room.messages))
    example = masked_example(room.messages)
    if example is not None:
        print(f"masked example: {example}")
    print(f"receipt written to {args.receipt}")
    results = replay(str(args.receipt), _fixture_replayer(FIXTURES / "bob.json"))
    matched = sum(result.matched for result in results)
    print(f"replay: {matched}/{len(results)} steps matched (fixture replay, not Docker)")
    return 0 if matched == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
