import argparse
import contextlib
import subprocess
import sys
import uuid
from collections.abc import Sequence

from bailiff.allowlist import is_allowed, is_allowed_overlay
from bailiff.models import Runner, RunnerFn, StepResult
from bailiff.receipt import load_receipt, validate_receipt

DOCKER_TIMEOUT_S = 120


def docker_runner(runner: Runner) -> tuple[int, str]:
    if runner.image.startswith("-"):
        raise ValueError(f"refusing image {runner.image!r}: it would be parsed as a docker flag")
    if not is_allowed(runner.cmd) or not is_allowed_overlay(runner.env):
        return 126, "refused: the command or its env is not on the allow-list"
    name = f"paritycourt-replay-{uuid.uuid4().hex}"
    argv = ["docker", "run", "--rm", "--name", name]
    for key, value in runner.env.items():
        argv += ["-e", f"{key}={value}"]
    argv += [runner.image, *runner.cmd]
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=DOCKER_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired:
        with contextlib.suppress(OSError, subprocess.SubprocessError):
            subprocess.run(
                ["docker", "rm", "-f", name],
                capture_output=True,
                timeout=DOCKER_TIMEOUT_S,
                check=False,
            )
        return 124, f"timed out after {DOCKER_TIMEOUT_S}s"
    return proc.returncode, proc.stderr


def replay(path: str, runner_fn: RunnerFn) -> list[StepResult]:
    receipt = load_receipt(path)
    problems = validate_receipt(receipt)
    if problems:
        raise ValueError("invalid receipt: " + "; ".join(problems))
    results: list[StepResult] = []
    for step in receipt["steps"]:
        runner = Runner(
            image=step["runner"]["image"],
            env=dict(step["runner"]["env"]),
            cmd=list(step["runner"]["cmd"]),
        )
        exit_code, _stderr = runner_fn(runner)
        outcome = "pass" if exit_code == 0 else "fail"
        matched = outcome == step["outcome"] and exit_code == step["exit_code"]
        results.append(
            StepResult(id=step["id"], exit_code=exit_code, outcome=outcome, matched=matched)
        )
    return results


def main(argv: Sequence[str] | None = None, runner_fn: RunnerFn | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m bailiff.replay",
        description="Re-run every step of a ParityCourt receipt and compare outcomes.",
    )
    parser.add_argument("receipt", help="path to receipt.json")
    parser.add_argument("--docker", action="store_true", help="re-run each step in docker run")
    args = parser.parse_args(argv)
    if runner_fn is None:
        if not args.docker:
            print(
                "error: no runner selected; pass --docker to re-run steps in containers",
                file=sys.stderr,
            )
            return 2
        runner_fn = docker_runner
    try:
        results = replay(args.receipt, runner_fn)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for result in results:
        label = "ok" if result.matched else "MISMATCH"
        print(f"{result.id}: {label} (exit {result.exit_code}, outcome {result.outcome})")
    matched = sum(result.matched for result in results)
    print(f"{matched}/{len(results)} steps matched")
    return 0 if matched == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
