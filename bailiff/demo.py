"""Local demo of the full ParityCourt case.

    python -m bailiff.demo --offline [--receipt PATH]

Runs the real Bailiff flow against an in-memory room. Alice (macOS-like, Node 22) and Bob
(Linux-like, Node 18) are scripted agents whose command output is canned in
bailiff/scripted/fixtures/. No Docker, no Switch, no LLM key. The receipt is then replayed against
Bob's fixture; the exit code is 0 only if every step matches. `--live` (Switch-room mode) is not
built yet and exits 2.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from bailiff.agent import serve
from bailiff.models import Runner, RunnerFn
from bailiff.receipt import save_receipt
from bailiff.replay import replay
from bailiff.scripted.fake_room import FakeRoom
from bailiff.scripted.runner import fixture_runner, serve_machine

FIXTURES = Path(__file__).parent / "scripted" / "fixtures"
TRIGGER = "!open case export-service 500 AuthVerifierError on Ubuntu, passes on the Mac"


async def run_offline() -> tuple[dict[str, Any], FakeRoom]:
    room = FakeRoom()
    bailiff = room.join("bailiff")
    machines = [
        asyncio.create_task(
            serve_machine(
                room.join("alice-claude"),
                room.room_id,
                "alice",
                "alice-claude",
                fixture_runner(FIXTURES / "alice.json"),
            )
        ),
        asyncio.create_task(
            serve_machine(
                room.join("bob-codex"),
                room.room_id,
                "bob",
                "bob-codex",
                fixture_runner(FIXTURES / "bob.json"),
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bailiff.demo")
    parser.add_argument("--offline", action="store_true", help="run against the in-memory room")
    parser.add_argument("--live", action="store_true", help="run against a Switch room (TODO)")
    default_receipt = os.environ.get("RECEIPT_PATH", "receipt.json")
    parser.add_argument("--receipt", type=Path, default=Path(default_receipt))
    args = parser.parse_args(argv)
    # TODO(live): register the Bailiff and both machine agents with Switch (POST /agents), then run.
    if args.live or not args.offline:
        print("TODO: live Switch-room mode is the next step (register agents, then run)")
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
    for suspect in receipt["suspects"]:
        print(f"  suspect {suspect['name']}: alice={suspect['alice']} bob={suspect['bob']}")
        print(f"    verdict: {suspect['verdict']}")
    for step in receipt["steps"]:
        print(f"  step {step['id']} ({step['variable']}) on {step['machine']}: {step['outcome']}")
    print(f"culprit: {json.dumps(receipt['culprit'])}")
    print(f"fix re-run on bob: {json.dumps(receipt['fix'])}")
    print(f"redactions: {receipt['redactions']}")
    print(f"receipt written to {args.receipt}")
    results = replay(str(args.receipt), _fixture_replayer(FIXTURES / "bob.json"))
    matched = sum(result.matched for result in results)
    print(f"replay: {matched}/{len(results)} steps matched (fixture replay, not Docker)")
    return 0 if matched == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
