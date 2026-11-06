"""Pre-recording check: `python scripts/preflight.py [--skip-network]`.

Prints one `PASS|FAIL|WARN <name>: <detail>` line per check, then a result line. Exits 0 when no
check FAILs, 1 otherwise. Stdlib only. Never prints an environment variable's value or a URL.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parent.parent

Verdict = Literal["PASS", "FAIL", "WARN"]


@dataclass(frozen=True)
class Outcome:
    name: str
    verdict: Verdict
    evidence: str


def run(argv: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            argv,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None


def check_python() -> Outcome:
    version = ".".join(str(part) for part in sys.version_info[:3])
    verdict: Verdict = "PASS" if sys.version_info >= (3, 11) else "FAIL"
    return Outcome("python", verdict, f"{version} (needs 3.11+)")


def check_docker() -> Outcome:
    name = "docker"
    if shutil.which("docker") is None:
        return Outcome(name, "FAIL", "docker not on PATH")
    proc = run(["docker", "info"])
    if proc is None:
        return Outcome(name, "FAIL", "docker info timed out or failed to start")
    if proc.returncode != 0:
        return Outcome(name, "FAIL", f"docker info exit {proc.returncode} (daemon running?)")
    return Outcome(name, "PASS", "docker info exit 0")


def check_env() -> list[Outcome]:
    wanted: tuple[tuple[str, Verdict], ...] = (
        ("BAILIFF_BASE_URL", "WARN"),
        ("SWITCH_REGISTRATION_TOKEN", "FAIL"),
    )
    outcomes: list[Outcome] = []
    for name, missing_verdict in wanted:
        is_set = bool(os.environ.get(name))
        verdict: Verdict = "PASS" if is_set else missing_verdict
        outcomes.append(Outcome(f"env {name}", verdict, "set" if is_set else "missing"))
    return outcomes


def check_bailiff(skip_network: bool) -> Outcome:
    name = "bailiff reachable"
    if skip_network:
        return Outcome(name, "WARN", "skipped by --skip-network")
    base = os.environ.get("BAILIFF_BASE_URL", "")
    if not base:
        return Outcome(name, "WARN", "BAILIFF_BASE_URL unset")
    if not base.startswith(("http://", "https://")):
        return Outcome(name, "FAIL", "BAILIFF_BASE_URL is not an http(s) URL")
    url = base.rstrip("/") + "/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:  # nosec B310
            return Outcome(name, "PASS", f"GET /health -> HTTP {resp.status}")
    except urllib.error.HTTPError as exc:
        return Outcome(name, "PASS", f"GET /health -> HTTP {exc.code}")
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return Outcome(name, "FAIL", f"no HTTP response from /health ({type(exc).__name__})")


def check_judge_cli() -> Outcome:
    name = "judge CLI"
    proc = run([sys.executable, str(REPO_ROOT / "scripts" / "judge.py"), "--help"])
    if proc is None:
        return Outcome(name, "FAIL", "judge.py --help timed out or failed to start")
    if proc.returncode != 0:
        return Outcome(name, "FAIL", f"judge.py --help exit {proc.returncode}")
    return Outcome(name, "PASS", "judge.py --help exit 0")


def check_git() -> Outcome:
    name = "git tracked files"
    proc = run(["git", "status", "--porcelain"])
    if proc is None or proc.returncode != 0:
        return Outcome(name, "WARN", "git status failed")
    changed = [line for line in proc.stdout.splitlines() if line and not line.startswith("??")]
    if changed:
        return Outcome(name, "WARN", f"{len(changed)} tracked file(s) with changes")
    return Outcome(name, "PASS", "no tracked-file changes")


def check_fixtures() -> Outcome:
    name = "live fixtures"
    fixtures = REPO_ROOT / "bailiff" / "scripted" / "fixtures"
    missing = [n for n in ("alice.json", "bob.json") if not (fixtures / n).is_file()]
    if missing:
        return Outcome(name, "FAIL", f"missing: {', '.join(missing)}")
    return Outcome(name, "PASS", "alice.json and bob.json present")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/preflight.py", description="Pre-recording checks for the demo."
    )
    parser.add_argument("--skip-network", action="store_true", help="skip the /health probe")
    args = parser.parse_args(argv)

    outcomes = [
        check_python(),
        check_docker(),
        *check_env(),
        check_bailiff(args.skip_network),
        check_judge_cli(),
        check_git(),
        check_fixtures(),
    ]
    for outcome in outcomes:
        print(f"{outcome.verdict} {outcome.name}: {outcome.evidence}")
    fails = sum(outcome.verdict == "FAIL" for outcome in outcomes)
    warns = sum(outcome.verdict == "WARN" for outcome in outcomes)
    print(f"PREFLIGHT RESULT: {'FAIL' if fails else 'PASS'} ({fails} FAIL, {warns} WARN)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
