#!/usr/bin/env python3
"""UserPromptSubmit hook: inject the full-scan instruction only when the prompt asks to
explain the whole project/codebase. Any other prompt prints nothing."""

import json
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

ASK = re.compile(
    r"\b(explain|expand|walk\s*(me\s*)?through|summari[sz]e|present|overview of|break\s*down)\b"
    r".{0,60}\b(project|codebase|code\s*base|repo|repository|architecture|entire|whole)\b",
    re.IGNORECASE | re.DOTALL,
)

INSTRUCTION = (
    "[explain-project] The user asked to explain the whole project. Do NOT answer from "
    "docs/PARITYCOURT.md or spec files alone. First explore the real codebase: list the tree, "
    "then read bailiff/, sample-app/, scripts/, deploy/, tests/, .github/workflows/, docs/ and "
    "any .archify diagrams. Cite path:line. Deliver, in order: (1) High-Level Design, "
    "(2) Workflow end to end, (3) Low-Level Design (modules, data shapes, state machine, "
    "error and security handling). Make it interactive via an archify HTML diagram/explainer "
    "and name the file to open. State what you read and could not verify."
)


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    prompt = str(
        payload.get("prompt") or payload.get("user_prompt") or payload.get("userPrompt") or ""
    )
    if ASK.search(prompt):
        sys.stdout.write(INSTRUCTION + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
