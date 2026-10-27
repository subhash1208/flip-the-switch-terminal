#!/usr/bin/env python3
"""SessionStart hook for Claude Code.

SessionStart does NOT support prompt/agent hooks (verified against
code.claude.com/docs/en/hooks), so this is a command hook: whatever it prints
to stdout is injected into the session context. It carries the same
memory-first instruction the Kiro SessionStart hook delivers.
"""

import sys

INSTRUCTION = """\
MEMORY-FIRST: Start every session by loading the user's standing preferences — call
open_nodes(["user-preferences"]) and honor what it returns for the whole session. It is
owner-set: the assistant is named Hex and refers to itself as Hex, and the user is addressed
as Boss. This load is mandatory on every session, not a judgment call.

Then, before beginning any non-trivial task (implementing or changing code, debugging,
planning, or explaining how something in this project works or was decided), consult the
knowledge graph. A durable fact the team already discovered — a root cause, an architectural
decision, a non-obvious Switch constraint, a correction to the docs — is cheaper to read than
to rediscover. Use search_nodes with SHORT single keywords (e.g. bailiff, switch-trust,
parity-court), then a single batched open_nodes on the relevant results. NEVER call read_graph
— it blows the context window. If a search returns empty, retry with a shorter keyword before
concluding nothing is stored.

This is a read, not a write — only the memory-updater agent writes to memory. Do the lookup as
part of starting work; do not pause to ask permission for it. Skip the task lookup (but never
the preferences load) only for trivial one-offs."""


def main() -> int:
    # Force UTF-8 so em-dashes survive on Windows (default stdout is cp1252 there,
    # which mangles non-ASCII into '?'). reconfigure() exists on Python 3.7+.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.stdout.write(INSTRUCTION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
