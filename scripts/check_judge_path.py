"""Live check of the ParityCourt judge path. Needs Docker.

Exit 0: every case matched. Exit 1: at least one FAIL. Exit 2: docker not on PATH.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = REPO_ROOT / "deploy" / "docker-compose.yml"
BUILD_TIMEOUT_S = 900
RUN_TIMEOUT_S = 180
NODE22_BIN = "/opt/node22/bin/node"
BOB_NODE_OPTIONS = "--openssl-legacy-provider"
TOSORTED_ERROR = "toSorted is not a function"


def compose(*args: str) -> list[str]:
    return ["docker", "compose", "-f", str(COMPOSE_FILE), *args]


# (label, argv, expect_zero_exit, stderr marker required when exit is non-zero or None)
CASES: list[tuple[str, list[str], bool, str | None]] = [
    ("alice: node 22 passes", compose("run", "--rm", "-T", "alice"), True, None),
    ("bob: node 18 fails", compose("run", "--rm", "-T", "bob"), False, TOSORTED_ERROR),
    (
        "bob: node 22 binary passes",
        compose("run", "--rm", "-T", "--entrypoint", NODE22_BIN, "bob", "test.js"),
        True,
        None,
    ),
    (
        "alice: TZ=UTC passes",
        compose("run", "--rm", "-T", "-e", "TZ=UTC", "alice"),
        True,
        None,
    ),
    (
        "alice: bob's NODE_OPTIONS passes",
        compose("run", "--rm", "-T", "-e", f"NODE_OPTIONS={BOB_NODE_OPTIONS}", "alice"),
        True,
        None,
    ),
]


def execute(argv: list[str], timeout: int) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None


def main() -> int:
    if shutil.which("docker") is None:
        print("SKIP: docker not found")
        return 2

    build = execute(compose("build"), BUILD_TIMEOUT_S)
    if build is None or build.returncode != 0:
        print("FAIL: docker compose build did not succeed")
        return 1

    rows: list[tuple[str, str, str, str]] = []
    for label, argv, expect_zero, marker in CASES:
        expected = "exit 0" if expect_zero else "exit != 0"
        if marker is not None:
            expected += f", stderr has '{marker}'"
        proc = execute(argv, RUN_TIMEOUT_S)
        if proc is None:
            rows.append((label, expected, "timeout", "FAIL"))
            continue
        exit_ok = (proc.returncode == 0) == expect_zero
        marker_ok = marker is None or marker in proc.stderr
        result = "PASS" if exit_ok and marker_ok else "FAIL"
        rows.append((label, expected, f"exit {proc.returncode}", result))

    width = max(len(label) for label, *_ in rows)
    print(f"{'CASE':<{width}}  {'EXPECTED':<40}  {'GOT':<10}  RESULT")
    for label, expected, got, result in rows:
        print(f"{label:<{width}}  {expected:<40}  {got:<10}  {result}")

    return 1 if any(result == "FAIL" for *_, result in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
