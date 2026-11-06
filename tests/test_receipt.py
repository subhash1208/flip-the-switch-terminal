import json
from pathlib import Path
from typing import Any

from bailiff.ablation import plan_ablation
from bailiff.models import Runner, Suspect
from bailiff.receipt import (
    build_receipt,
    load_receipt,
    save_receipt,
    step_to_dict,
    validate_receipt,
)


def _case() -> dict[str, Any]:
    node = Suspect("node", "v22.11.0", "v18.20.4", "culprit")
    step = plan_ablation([node], base=Runner("node:18-bookworm-slim", {}, ["node", "test.js"]))[0]
    return {
        "case_id": "101",
        "created_at": "2026-11-06T12:00:00+05:30",
        "room_id": "room-101",
        "pinned": {
            "app_commit": "abc1234",
            "images": {"alice": "node:22-bookworm-slim", "bob": "node:18-bookworm-slim"},
        },
        "baseline": {
            "machine": "alice",
            "cmd": ["node", "test.js"],
            "exit_code": 0,
            "outcome": "pass",
            "stderr_excerpt": "",
        },
        "failure": {
            "machine": "bob",
            "cmd": ["node", "test.js"],
            "exit_code": 1,
            "outcome": "fail",
            "stderr_excerpt": "TypeError: toSorted is not a function",
        },
        "steps": [step_to_dict(step, 0, "pass")],
        "suspects": [
            {"name": "node", "alice": "v22.11.0", "bob": "v18.20.4", "verdict": "culprit"}
        ],
        "culprit": {"variable": "node", "evidence_step": "ablation-1"},
        "fix": {"branch": "fix/case-101-import", "verified_on": "bob", "outcome": "pass"},
        "attestations": [
            {
                "machine": "alice",
                "owner": "alice",
                "at": "2026-11-06T12:05:00+05:30",
                "approval_message_id": "msg-1",
            }
        ],
        "redactions": 0,
    }


def test_null_culprit_fix_and_exit_codes_are_accepted_when_nothing_was_isolated() -> None:
    case = _case()
    case["culprit"] = None
    case["fix"] = None
    case["steps"][0]["exit_code"] = None
    case["steps"][0]["outcome"] = "fail"
    case["failure"]["exit_code"] = None
    assert validate_receipt({**case, "schema_version": 1}) == []


def test_exit_code_must_still_be_an_int_or_null() -> None:
    case = _case()
    case["steps"][0]["exit_code"] = "0"
    problems = validate_receipt({**case, "schema_version": 1})
    assert "receipt.steps[0].exit_code: expected int" in problems


def test_valid_case_builds_with_schema_version_1() -> None:
    receipt = build_receipt(_case())
    assert receipt["schema_version"] == 1
    assert validate_receipt(receipt) == []


def test_missing_field_is_reported_and_build_refuses() -> None:
    case = _case()
    del case["fix"]
    assert "receipt.fix: missing" in validate_receipt({**case, "schema_version": 1})
    try:
        build_receipt(case)
    except ValueError as exc:
        assert "receipt.fix: missing" in str(exc)
    else:
        raise AssertionError("build_receipt accepted a receipt with no fix")


def test_culprit_must_reference_an_existing_step() -> None:
    case = _case()
    case["culprit"] = {"variable": "node", "evidence_step": "ablation-9"}
    problems = validate_receipt({**case, "schema_version": 1})
    assert problems == ["receipt.culprit.evidence_step: no step with id 'ablation-9'"]


def test_duplicate_step_ids_are_rejected() -> None:
    case = _case()
    case["steps"] = [case["steps"][0], case["steps"][0]]
    problems = validate_receipt({**case, "schema_version": 1})
    assert "receipt.steps[1].id: duplicate step id 'ablation-1'" in problems


def test_outcome_must_be_pass_or_fail_and_malformed_values_do_not_raise() -> None:
    case = _case()
    case["steps"][0]["outcome"] = "maybe"
    case["baseline"]["outcome"] = ["pass"]
    problems = validate_receipt({**case, "schema_version": 1})
    assert "receipt.steps[0].outcome: must be 'pass' or 'fail'" in problems
    assert "receipt.baseline.outcome: must be 'pass' or 'fail'" in problems


def test_receipt_without_steps_is_rejected() -> None:
    case = _case()
    case["steps"] = []
    problems = validate_receipt({**case, "schema_version": 1})
    assert "receipt.steps: must contain at least one step" in problems


def test_save_and_load_roundtrip_writes_sorted_keys(tmp_path: Path) -> None:
    receipt = build_receipt(_case())
    path = tmp_path / "receipt.json"
    save_receipt(receipt, str(path))
    assert load_receipt(str(path)) == receipt
    assert json.loads(path.read_text(encoding="utf-8")) == receipt
    assert path.read_text(encoding="utf-8").startswith('{\n  "attestations": ')


def test_inconclusive_receipt_may_have_no_steps() -> None:
    case = _case()
    case["steps"] = []
    case["culprit"] = None
    case["fix"] = None
    case["inconclusive"] = True
    case["inconclusive_reason"] = "no suspects: the fingerprints show no difference to ablate"
    assert validate_receipt({**case, "schema_version": 1}) == []


def test_inconclusive_true_requires_a_reason_and_booleans_must_be_booleans() -> None:
    case = _case()
    case["inconclusive"] = True
    case["simulated"] = 1
    problems = validate_receipt({**case, "schema_version": 1})
    assert "receipt.inconclusive_reason: required when inconclusive is true" in problems
    assert "receipt.simulated: expected bool" in problems


def test_attestation_approval_is_optional_and_must_be_text_or_null() -> None:
    case = _case()
    assert validate_receipt({**case, "schema_version": 1}) == []
    case["attestations"][0]["approval"] = None
    assert validate_receipt({**case, "schema_version": 1}) == []
    case["attestations"][0]["approval"] = 1
    problems = validate_receipt({**case, "schema_version": 1})
    assert "receipt.attestations[0].approval: expected str or null" in problems
