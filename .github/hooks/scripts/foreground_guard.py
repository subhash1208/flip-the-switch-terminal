#!/usr/bin/env python3
"""preToolUse hook: deny subagent calls that request background mode.

Subagents run in the foreground so each result is read before the next step.
Always exits 0: a non-zero exit would deny every tool call.
"""

import json
import sys


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    args = payload.get("toolArgs", payload.get("tool_input"))
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            return 0
    name = str(payload.get("toolName") or payload.get("tool_name") or "").lower()
    if name == "task" and isinstance(args, dict) and args.get("mode") == "background":
        print(json.dumps({
            "permissionDecision": "deny",
            "permissionDecisionReason": 'BLOCKED: background subagents are disabled. '
                                        'Re-issue the task call with mode: "sync".',
        }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
