"""One-command check for judges: `python scripts/judge.py [--no-docker]`.

Needs Python 3.11+ and the runtime deps (`pip install -e .` from the repo root). Runs eight checks
in order, prints a PASS/FAIL/SKIP table, and exits 1 if any check FAILs. Checks 3-6 use the
in-process fake room (SIMULATED, no Switch server). Check 7 runs the real sample app under Node.
Check 8 runs the live Docker judge path when docker is on PATH. Makes no network calls.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "bailiff" / "scripted" / "fixtures"
SAMPLE_DIR = REPO_ROOT / "sample-app" / "export-service"

Verdict = Literal["PASS", "FAIL", "SKIP"]


@dataclass(frozen=True)
class Outcome:
    name: str
    verdict: Verdict
    evidence: str


def run(argv: list[str], cwd: Path, timeout: int) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None


def check_python() -> Outcome:
    version = ".".join(str(part) for part in sys.version_info[:3])
    verdict: Verdict = "PASS" if sys.version_info >= (3, 11) else "FAIL"
    return Outcome("python version", verdict, f"Python {version} (needs 3.11+)")


def check_import() -> Outcome:
    name = "import bailiff"
    try:
        module = importlib.import_module("bailiff")
    except ImportError as exc:
        return Outcome(name, "FAIL", f"{exc}; run: python -m pip install -e .")
    return Outcome(name, "PASS", f"imported from {module.__file__}")


def check_demo(receipt_path: Path) -> tuple[Outcome, str]:
    name = "demo runs offline"
    argv = [sys.executable, "-m", "bailiff.demo", "--offline", "--receipt", str(receipt_path)]
    proc = run(argv, REPO_ROOT, 120)
    if proc is None:
        return Outcome(name, "FAIL", "timed out after 120s"), ""
    if proc.returncode != 0:
        last = (proc.stderr.strip().splitlines() or ["no stderr"])[-1]
        return Outcome(name, "FAIL", f"exit {proc.returncode}: {last}"), proc.stdout
    replay = next(
        (line for line in proc.stdout.splitlines() if line.startswith("replay:")),
        "replay line missing",
    )
    return Outcome(name, "PASS", f"exit 0; {replay}"), proc.stdout


def check_receipt(receipt_path: Path) -> Outcome:
    name = "receipt valid, culprit node"
    if not receipt_path.exists():
        return Outcome(name, "FAIL", "demo wrote no receipt")
    from bailiff.receipt import load_receipt, validate_receipt

    try:
        receipt = load_receipt(str(receipt_path))
    except ValueError as exc:
        return Outcome(name, "FAIL", f"receipt is not valid JSON: {exc}")
    problems = validate_receipt(receipt)
    if problems:
        return Outcome(name, "FAIL", f"{len(problems)} schema problem(s), first: {problems[0]}")
    culprit = receipt.get("culprit") or {}
    variable = culprit.get("variable")
    if variable != "node":
        return Outcome(name, "FAIL", f"culprit variable is {variable!r}, expected 'node'")
    return Outcome(
        name,
        "PASS",
        f"schema valid; culprit variable {variable}, evidence step {culprit.get('evidence_step')}",
    )


def fixture_pii() -> dict[str, str]:
    """Synthetic PII and secrets from the fixtures, keyed by label. Values are never printed."""
    found: dict[str, str] = {}
    for path in sorted(FIXTURES.glob("*.json")):
        commands: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))["commands"]
        env: dict[str, str] = {}
        for line in commands["env"]["stdout"].splitlines():
            key, _, value = line.partition("=")
            env[key] = value
        values = {
            "EMAIL": env.get("EMAIL", ""),
            "HOME": env.get("HOME", ""),
            "HOSTNAME": env.get("HOSTNAME", ""),
            "DATABASE_PASSWORD": env.get("DATABASE_PASSWORD", ""),
            "SSH_CLIENT address": (env.get("SSH_CLIENT", "").split() or [""])[0],
            "uname node name": (commands["uname -a"]["stdout"].split() + ["", ""])[1],
        }
        for key, value in values.items():
            if value:
                found[f"{path.stem} {key}"] = value
    return found


def check_privacy(receipt_path: Path, demo_stdout: str) -> Outcome:
    name = "privacy: no fixture PII"
    if not receipt_path.exists():
        return Outcome(name, "FAIL", "no receipt to inspect")
    try:
        pii = fixture_pii()
    except (KeyError, IndexError, ValueError) as exc:
        return Outcome(name, "FAIL", f"fixtures unreadable: {exc!r}")
    haystacks = {"receipt": receipt_path.read_text(encoding="utf-8"), "demo stdout": demo_stdout}
    leaks = sorted(
        f"{label} in {where}"
        for label, value in pii.items()
        for where, text in haystacks.items()
        if value in text
    )
    if leaks:
        return Outcome(name, "FAIL", f"leaked: {', '.join(leaks)}")
    unmarked = [where for where, text in haystacks.items() if "[redacted" not in text]
    if unmarked:
        return Outcome(name, "FAIL", f"no [redacted marker in {', '.join(unmarked)}")
    return Outcome(
        name,
        "PASS",
        f"0 of {len(pii)} fixture values found; [redacted marker in receipt and stdout",
    )


def check_replay(receipt_path: Path) -> Outcome:
    name = "replay matches every step"
    try:
        from bailiff.demo import _fixture_replayer
        from bailiff.replay import replay
    except ImportError as exc:
        return Outcome(name, "SKIP", f"fixture runner not importable: {exc}")
    if not receipt_path.exists():
        return Outcome(name, "FAIL", "no receipt to replay")
    try:
        results = replay(str(receipt_path), _fixture_replayer(FIXTURES / "bob.json"))
    except (ValueError, OSError) as exc:
        return Outcome(name, "FAIL", f"replay refused the receipt: {exc}")
    matched = sum(result.matched for result in results)
    verdict: Verdict = "PASS" if results and matched == len(results) else "FAIL"
    return Outcome(
        name, verdict, f"{matched}/{len(results)} steps matched (fixture replay of bob.json)"
    )


def check_node() -> Outcome:
    name = "sample test.js vs node version"
    node = shutil.which("node")
    if node is None:
        return Outcome(name, "SKIP", "node not found on PATH")
    version_proc = run([node, "-v"], SAMPLE_DIR, 30)
    if version_proc is None or version_proc.returncode != 0:
        return Outcome(name, "FAIL", "node -v did not run")
    match = re.match(r"v(\d+)\.", version_proc.stdout.strip())
    if match is None:
        return Outcome(name, "FAIL", f"unrecognised node version {version_proc.stdout.strip()!r}")
    major = int(match.group(1))
    proc = run([node, "test.js"], SAMPLE_DIR, 60)
    if proc is None:
        return Outcome(name, "FAIL", f"node v{major}: test.js timed out after 60s")
    if major >= 20:
        expected = "exit 0"
        ok = proc.returncode == 0
    else:
        expected = "exit != 0 with 'toSorted is not a function'"
        ok = proc.returncode != 0 and "toSorted is not a function" in proc.stderr
    verdict: Verdict = "PASS" if ok else "FAIL"
    return Outcome(name, verdict, f"node v{major}: exit {proc.returncode}; expected {expected}")


def check_docker(skip: bool) -> Outcome:
    name = "live Docker judge path"
    if skip:
        return Outcome(name, "SKIP", "--no-docker given")
    if shutil.which("docker") is None:
        return Outcome(name, "SKIP", "docker not found")
    judge_path = REPO_ROOT / "scripts" / "check_judge_path.py"
    proc = run([sys.executable, str(judge_path)], REPO_ROOT, 1800)
    if proc is None:
        return Outcome(name, "FAIL", "check_judge_path.py timed out after 1800s")
    if proc.returncode == 2:
        return Outcome(name, "SKIP", "docker not found")
    rows = [line for line in proc.stdout.splitlines() if line.rstrip().endswith((" PASS", " FAIL"))]
    passed = sum(1 for line in rows if line.rstrip().endswith(" PASS"))
    verdict: Verdict = "PASS" if proc.returncode == 0 else "FAIL"
    return Outcome(name, verdict, f"{passed}/{len(rows)} live cases PASS (exit {proc.returncode})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/judge.py", description="Run the ParityCourt judge checks."
    )
    parser.add_argument("--no-docker", action="store_true", help="skip check 8 (live Docker)")
    args = parser.parse_args(argv)
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    outcomes: list[Outcome] = []

    def record(outcome: Outcome) -> None:
        outcomes.append(outcome)
        print(f"{len(outcomes):>2}  {outcome.name:<30} {outcome.verdict:<4}  {outcome.evidence}")

    print(f"{'#':>2}  {'CHECK':<30} {'RESULT':<4}  EVIDENCE")
    record(check_python())
    record(check_import())
    with tempfile.TemporaryDirectory(prefix="judge-") as tmp:
        receipt_path = Path(tmp) / "receipt.json"
        demo, demo_stdout = check_demo(receipt_path)
        record(demo)
        record(check_receipt(receipt_path))
        record(check_privacy(receipt_path, demo_stdout))
        record(check_replay(receipt_path))
    record(check_node())
    record(check_docker(skip=args.no_docker))

    failed = any(outcome.verdict == "FAIL" for outcome in outcomes)
    print(
        "NOTE: checks 3-6 are SIMULATED (in-process fake Switch room, canned fixtures, no Switch "
        "server). Check 7 runs real Node. Check 8 runs real Docker when present."
    )
    print(
        "Live Switch-room evidence: (to be added) in docs/evidence/ or the demo video. "
        "See JUDGES.md."
    )
    print(f"JUDGE RESULT: {'FAIL' if failed else 'PASS'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
