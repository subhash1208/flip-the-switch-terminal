"""Scripted Alice machine agent (keyless judge path only).
Stands in for Claude Code on Alice's machine.

It is not an LLM and approves nothing itself. It runs allow-listed commands locally in
MACHINE_WORKDIR
and posts the results. See bailiff/scripted/runner.py for the auto-approval note.

Env: BAILIFF_BASE_URL, ALICE_AGENT_ID, ALICE_API_KEY, ALICE_CONNECTION_ID, ROOM_ID, and optionally
ALICE_HANDLE (default alice-claude) and MACHINE_WORKDIR.
"""

import asyncio
import os

from bailiff.scripted.runner import run_local, serve_machine
from bailiff.transport import SwitchConnection


async def main() -> None:
    async with SwitchConnection(
        os.environ["BAILIFF_BASE_URL"],
        os.environ["ALICE_AGENT_ID"],
        os.environ["ALICE_API_KEY"],
        os.environ["ALICE_CONNECTION_ID"],
        [os.environ["ROOM_ID"]],
    ) as conn:
        await serve_machine(
            conn,
            os.environ["ROOM_ID"],
            "alice",
            os.environ.get("ALICE_HANDLE", "alice-claude"),
            run_local,
        )


if __name__ == "__main__":
    asyncio.run(main())
