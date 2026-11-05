#!/usr/bin/env python3
"""subagentStop hook: a reviewer must end with VERDICT: GREEN or VERDICT: RED.

Returns a block decision (forces the reviewer to restate its report) only when
the stopping subagent is the reviewer and its response has neither verdict.
Every other subagent passes through untouched.
"""

import json
import sys


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if not isinstance(payload, dict) or payload.get("agentName") != "reviewer":
        return 0
    response = payload.get("response") or ""
    if "VERDICT: GREEN" in response or "VERDICT: RED" in response:
        return 0
    print(json.dumps({
        "decision": "block",
        "reason": "Your report must end with exactly one of VERDICT: GREEN or "
                  "VERDICT: RED, each backed by concrete evidence. Restate it now.",
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
