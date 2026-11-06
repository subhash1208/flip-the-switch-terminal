"""CaseState: transition order, turn cap, room-document shape, and the receipt case dict."""

from __future__ import annotations

import json

import pytest

from bailiff.state import CaseState, InvalidTransition, TurnCapExceeded

RECEIPT_KEYS = {
    "case_id",
    "created_at",
    "room_id",
    "pinned",
    "baseline",
    "failure",
    "steps",
    "suspects",
    "culprit",
    "fix",
    "attestations",
    "redactions",
}


def _state(**kwargs: object) -> CaseState:
    return CaseState(
        case_id="case-1", room_id="r1", title="export-service 500", opened_by="dana", **kwargs
    )  # type: ignore[arg-type]


def test_transitions_follow_the_order_and_closed_is_reachable_from_any_open_state() -> None:
    s = _state()
    with pytest.raises(InvalidTransition):
        s.transition("diffing")
    s.transition("fingerprinting")
    s.transition("diffing")
    s.transition("closed")
    assert s.state == "closed"
    with pytest.raises(InvalidTransition):
        s.transition("opened")


def test_room_document_has_exactly_one_fenced_json_block_even_when_output_contains_backticks() -> (
    None
):
    s = _state()
    s.machines["alice"] = {
        "agent_handle": "alice-claude",
        "fingerprint": {"probes": {"env": "x ``` y"}},
    }
    doc = s.to_room_document()
    fences = [line for line in doc.splitlines() if line.startswith("```")]
    assert fences == ["```json", "```"]
    block = doc.split("```json\n", 1)[1].split("\n```", 1)[0]
    body = json.loads(block)
    assert set(body) == {
        "case_id",
        "state",
        "opened_by",
        "machines",
        "probes",
        "suspects",
        "steps",
        "verdict",
    }
    assert body["machines"]["alice"]["fingerprint"]["probes"]["env"] == "x ``` y"


def test_turn_cap_is_off_by_default_and_enforced_when_set() -> None:
    free = _state()
    for _ in range(100):
        free.turn()
    capped = _state(turn_cap=2)
    capped.turn()
    capped.turn()
    with pytest.raises(TurnCapExceeded):
        capped.turn()


def test_case_dict_has_the_receipt_keys_and_counts_both_redaction_sources() -> None:
    s = _state()
    s.redactions = 2
    s.doc_redactions = 1
    d = s.to_case_dict()
    assert set(d) == RECEIPT_KEYS
    assert d["redactions"] == 3
    assert d["culprit"] is None
