import json
from pathlib import Path
from typing import Any

from bailiff.models import AblationStep
from bailiff.redact import mask_secret_lines, redact

_OUTCOMES = ("pass", "fail")
_VERDICTS = ("unknown", "decoy", "culprit")

_TOP_LEVEL: dict[str, type] = {
    "schema_version": int,
    "case_id": str,
    "created_at": str,
    "room_id": str,
    "pinned": dict,
    "baseline": dict,
    "failure": dict,
    "steps": list,
    "suspects": list,
    "culprit": dict,
    "fix": dict,
    "attestations": list,
    "redactions": int,
}
_PINNED: dict[str, type] = {"app_commit": str, "images": dict}
_IMAGES: dict[str, type] = {"alice": str, "bob": str}
_RUN: dict[str, type] = {
    "machine": str,
    "cmd": list,
    "exit_code": int,
    "outcome": str,
    "stderr_excerpt": str,
}
_STEP: dict[str, type] = {
    "id": str,
    "machine": str,
    "variable": str,
    "from": str,
    "to": str,
    "runner": dict,
    "exit_code": int,
    "outcome": str,
    "pinned": bool,
}
_RUNNER: dict[str, type] = {"image": str, "env": dict, "cmd": list}
_CULPRIT: dict[str, type] = {"variable": str, "evidence_step": str}
_FIX: dict[str, type] = {"branch": str, "verified_on": str, "outcome": str}
_SUSPECT: dict[str, type] = {"name": str, "alice": str, "bob": str, "verdict": str}
_ATTESTATION: dict[str, type] = {
    "machine": str,
    "owner": str,
    "at": str,
    "approval_message_id": str,
}


def _is_kind(value: object, kind: type) -> bool:
    if kind is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, kind)


def _check_fields(
    obj: Any,
    where: str,
    spec: dict[str, type],
    problems: list[str],
    nullable: frozenset[str] = frozenset(),
) -> None:
    if not isinstance(obj, dict):
        return
    for key, kind in spec.items():
        if key not in obj:
            problems.append(f"{where}.{key}: missing")
        elif obj[key] is None and key in nullable:
            continue
        elif not _is_kind(obj[key], kind):
            problems.append(f"{where}.{key}: expected {kind.__name__}")


def _check_outcome(obj: Any, where: str, problems: list[str]) -> None:
    if isinstance(obj, dict) and "outcome" in obj and obj["outcome"] not in _OUTCOMES:
        problems.append(f"{where}.outcome: must be 'pass' or 'fail'")


def _check_strings(value: Any, where: str, problems: list[str]) -> None:
    if isinstance(value, list) and not all(isinstance(item, str) for item in value):
        problems.append(f"{where}: every item must be a string")
    if isinstance(value, dict) and not all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    ):
        problems.append(f"{where}: keys and values must be strings")


def _check_items(
    items: Any, where: str, spec: dict[str, type], problems: list[str]
) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    valid: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            problems.append(f"{where}[{index}]: expected an object")
            continue
        _check_fields(item, f"{where}[{index}]", spec, problems)
        valid.append(item)
    return valid


def _check_privacy(privacy: Any, problems: list[str]) -> None:
    if not isinstance(privacy, dict):
        problems.append("receipt.privacy: expected an object")
        return
    counts = privacy.get("placeholders")
    if not isinstance(counts, dict) or not all(
        isinstance(kind, str) and _is_kind(n, int) and n >= 0 for kind, n in counts.items()
    ):
        problems.append("receipt.privacy.placeholders: expected a map of type to count >= 0")
    example = privacy.get("example")
    if not isinstance(example, str) or len(example) > 200:
        problems.append("receipt.privacy.example: expected a string of at most 200 characters")
    elif redact(example)[1] or mask_secret_lines(example)[1]:
        problems.append("receipt.privacy.example: holds text that masking would still change")


def validate_receipt(d: dict[str, Any]) -> list[str]:
    if not isinstance(d, dict):
        return ["receipt: expected a JSON object"]
    problems: list[str] = []
    _check_fields(d, "receipt", _TOP_LEVEL, problems, nullable=frozenset({"culprit", "fix"}))
    if "schema_version" in d and d["schema_version"] != 1:
        problems.append("receipt.schema_version: must be 1")

    pinned = d.get("pinned")
    _check_fields(pinned, "receipt.pinned", _PINNED, problems)
    if isinstance(pinned, dict):
        _check_fields(pinned.get("images"), "receipt.pinned.images", _IMAGES, problems)

    for key in ("baseline", "failure"):
        run = d.get(key)
        _check_fields(run, f"receipt.{key}", _RUN, problems, nullable=frozenset({"exit_code"}))
        _check_outcome(run, f"receipt.{key}", problems)
        if isinstance(run, dict):
            _check_strings(run.get("cmd"), f"receipt.{key}.cmd", problems)

    step_ids: list[str] = []
    inconclusive = d.get("inconclusive") is True
    steps = d.get("steps")
    if isinstance(steps, list):
        if not steps and not inconclusive:
            problems.append("receipt.steps: must contain at least one step")
        for index, step in enumerate(steps):
            where = f"receipt.steps[{index}]"
            if not isinstance(step, dict):
                problems.append(f"{where}: expected an object")
                continue
            _check_fields(step, where, _STEP, problems, nullable=frozenset({"exit_code"}))
            _check_outcome(step, where, problems)
            runner = step.get("runner")
            _check_fields(runner, f"{where}.runner", _RUNNER, problems)
            if isinstance(runner, dict):
                _check_strings(runner.get("cmd"), f"{where}.runner.cmd", problems)
                _check_strings(runner.get("env"), f"{where}.runner.env", problems)
            step_id = step.get("id")
            if isinstance(step_id, str):
                if step_id in step_ids:
                    problems.append(f"{where}.id: duplicate step id {step_id!r}")
                step_ids.append(step_id)

    for suspect in _check_items(d.get("suspects"), "receipt.suspects", _SUSPECT, problems):
        verdict = suspect.get("verdict")
        if isinstance(verdict, str) and verdict not in _VERDICTS:
            problems.append(f"receipt.suspects {suspect.get('name')!r}: invalid verdict")

    culprit = d.get("culprit")
    _check_fields(culprit, "receipt.culprit", _CULPRIT, problems)
    if isinstance(culprit, dict):
        evidence = culprit.get("evidence_step")
        if isinstance(evidence, str) and evidence not in step_ids:
            problems.append(f"receipt.culprit.evidence_step: no step with id {evidence!r}")

    fix = d.get("fix")
    _check_fields(fix, "receipt.fix", _FIX, problems, nullable=frozenset({"branch"}))
    _check_outcome(fix, "receipt.fix", problems)

    attestations = d.get("attestations")
    _check_items(attestations, "receipt.attestations", _ATTESTATION, problems)
    if isinstance(attestations, list):
        for index, attestation in enumerate(attestations):
            approval = attestation.get("approval") if isinstance(attestation, dict) else None
            if approval is not None and not isinstance(approval, str):
                problems.append(f"receipt.attestations[{index}].approval: expected str or null")

    for key in ("simulated", "inconclusive"):
        if key in d and not isinstance(d[key], bool):
            problems.append(f"receipt.{key}: expected bool")
    if inconclusive and not isinstance(d.get("inconclusive_reason"), str):
        problems.append("receipt.inconclusive_reason: required when inconclusive is true")

    if "privacy" in d:
        _check_privacy(d["privacy"], problems)

    redactions = d.get("redactions")
    if isinstance(redactions, int) and redactions < 0:
        problems.append("receipt.redactions: must be >= 0")
    return problems


def build_receipt(case: dict[str, Any]) -> dict[str, Any]:
    receipt = {**case, "schema_version": 1}
    problems = validate_receipt(receipt)
    if problems:
        raise ValueError("invalid receipt: " + "; ".join(problems))
    return receipt


def step_to_dict(
    step: AblationStep, exit_code: int | None, outcome: str, pinned: bool = True
) -> dict[str, Any]:
    return {
        "id": step.id,
        "machine": step.machine,
        "variable": step.variable,
        "from": step.from_value,
        "to": step.to_value,
        "runner": {
            "image": step.runner.image,
            "env": dict(step.runner.env),
            "cmd": list(step.runner.cmd),
        },
        "exit_code": exit_code,
        "outcome": outcome,
        "pinned": pinned,
    }


def save_receipt(d: dict[str, Any], path: str) -> None:
    Path(path).write_text(json.dumps(d, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_receipt(path: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    return data
