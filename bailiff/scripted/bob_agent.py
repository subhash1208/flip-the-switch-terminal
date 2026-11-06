"""Scripted Bob machine agent (keyless judge path only).
Stands in for Codex on Bob's failing machine.

Same code as Alice's: it answers probes, the failing test, Bob's ablation steps, the fix
verification and attestation, all by running allow-listed commands locally. It is not an LLM and
approves nothing.
See bailiff/scripted/runner.py for the auto-approval note.

Env: BAILIFF_BASE_URL, BOB_AGENT_ID, BOB_API_KEY, BOB_CONNECTION_ID, ROOM_ID, and optionally
BOB_HANDLE (default bob-codex) and MACHINE_WORKDIR.
"""

import asyncio
import os

from bailiff.scripted.runner import run_local, serve_machine
from bailiff.transport import SwitchConnection


async def main() -> None:
    async with SwitchConnection(
        os.environ["BAILIFF_BASE_URL"],
        os.environ["BOB_AGENT_ID"],
        os.environ["BOB_API_KEY"],
        os.environ["BOB_CONNECTION_ID"],
        [os.environ["ROOM_ID"]],
    ) as conn:
        await serve_machine(
            conn, os.environ["ROOM_ID"], "bob", os.environ.get("BOB_HANDLE", "bob-codex"), run_local
        )


if __name__ == "__main__":
    asyncio.run(main())
