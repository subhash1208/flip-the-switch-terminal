#!/usr/bin/env python3
"""PostToolUse hook: after a source file is edited, remind the agent which
quality gate applies. Deterministic nudge — fires every time.

Reads the postToolUse event JSON from stdin, checks the edited file path, and
returns the relevant gate reminder as additionalContext for the model.
"""

import json
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw or "{}")
    except (json.JSONDecodeError, ValueError):
        return 0

    tool_input = payload.get("tool_input") or payload.get("toolInput") or payload.get("toolArgs") or {}
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except ValueError:
            tool_input = {}
    if not isinstance(tool_input, dict):
        tool_input = {}
    path = str(
        tool_input.get("file_path")
        or tool_input.get("filePath")
        or tool_input.get("path")
        or tool_input.get("file")
        or ""
    ).replace("\\", "/")

    if not path:
        return 0

    messages: list[str] = []

    # Python files → ruff + mypy + pytest
    if re.search(r"\.py$", path):
        messages.append(
            "`just check` (ruff) and `just typecheck` (mypy) must pass before handoff."
        )
    if re.search(r"(^|/)core/switch_core/", path) and not re.search(r"test", path):
        messages.append(
            "Changed Switch core source — `just test` must pass; new behavior needs a test."
        )
    if re.search(r"(^|/)bailiff/", path) and not re.search(r"test", path):
        messages.append(
            "Changed Bailiff source — `python -m pytest tests/ -v` must pass."
        )

    # TypeScript files → oxlint + tsgo + vitest
    if re.search(r"\.(ts|tsx|mts)$", path):
        messages.append(
            "`pnpm -r run typecheck` and `pnpm -r run lint` must pass before handoff."
        )
    if re.search(r"(^|/)console/packages/", path) and not re.search(r"\.test\.", path):
        messages.append(
            "Changed Switch console source — `pnpm -r run test` must pass."
        )

    # Test files
    if re.search(r"(test_|_test\.|\.test\.)", path):
        messages.append("Test file changed — run it now; never hand off an unrun test.")

    # Config files
    if re.search(r"(pyproject\.toml|ruff\.toml|justfile|package\.json|tsconfig)", path):
        messages.append("Build config changed — verify the build still works.")

    if not messages:
        return 0

    print(json.dumps({"additionalContext": f"[quality-gates] {' '.join(messages)}"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
