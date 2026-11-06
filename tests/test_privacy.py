"""The privacy record: placeholder counts and one example, read from the transcript."""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from bailiff.privacy import EXAMPLE_CHARS, masked_example, placeholder_counts, privacy_record
from bailiff.receipt import build_receipt, validate_receipt
from bailiff.redact import MARKER
from bailiff.state import CaseState

CLEAN = [("dana", "nothing masked here")]
MASKED = [
    ("dana", "!open case export-service"),
    ("alice-claude", "RES env: EMAIL=[redacted:email] and DATABASE_PASSWORD=[redacted]"),
    ("bob-codex", "peer [redacted:ip] and [redacted:ip] seen"),
]
BASE: dict[str, Any] = {
    "schema_version": 1,
    "case_id": "case-p1",
    "created_at": "2026-11-06T12:00:00+05:30",
    "room_id": "room-p1",
    "pinned": {"app_commit": "abc1234", "images": {"alice": "a", "bob": "b"}},
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
        "stderr_excerpt": "",
    },
    "steps": [],
    "suspects": [],
    "culprit": None,
    "fix": None,
    "attestations": [],
    "redactions": 0,
    "inconclusive": True,
    "inconclusive_reason": "no suspects: the fingerprints show no difference to ablate",
}


def test_counts_by_type_and_a_bare_marker_as_secret() -> None:
    assert placeholder_counts(MASKED) == {"email": 1, "ip": 2, "secret": 1}


def test_no_placeholder_means_no_record() -> None:
    assert placeholder_counts(CLEAN) == {}
    assert privacy_record(CLEAN) is None
    assert privacy_record([]) is None


def test_the_example_is_a_window_of_at_most_100_characters_from_a_masked_line() -> None:
    example = masked_example(MASKED)
    assert example is not None
    assert "[redacted:email]" in example
    assert len(example) <= EXAMPLE_CHARS
    assert example in MASKED[1][1]


def test_the_example_falls_back_to_a_bare_marker_when_no_typed_placeholder_exists() -> None:
    assert masked_example([("a", f"TOKEN={MARKER}")]) == f"TOKEN={MARKER}"


def test_the_record_holds_the_counts_and_the_example() -> None:
    assert privacy_record(MASKED) == {
        "placeholders": {"email": 1, "ip": 2, "secret": 1},
        "example": masked_example(MASKED),
    }


def test_case_dict_carries_privacy_only_when_a_placeholder_was_seen() -> None:
    state = CaseState(case_id="c1", room_id="r1", title="t", opened_by="dana")
    state.transcript = list(CLEAN)
    assert "privacy" not in state.to_case_dict()
    state.transcript = list(MASKED)
    assert state.to_case_dict()["privacy"] == privacy_record(MASKED)


def test_a_base_receipt_without_privacy_is_valid() -> None:
    assert validate_receipt(BASE) == []


@pytest.mark.parametrize(
    ("privacy", "problem"),
    [
        ("not an object", "receipt.privacy: expected an object"),
        ({"placeholders": ["ip"], "example": "x"}, "receipt.privacy.placeholders"),
        ({"placeholders": {"ip": -1}, "example": "x"}, "receipt.privacy.placeholders"),
        ({"placeholders": {"ip": True}, "example": "x"}, "receipt.privacy.placeholders"),
        ({"placeholders": {"ip": 1}}, "receipt.privacy.example: expected a string"),
        ({"placeholders": {"ip": 1}, "example": "x" * 201}, "at most 200 characters"),
        (
            {"placeholders": {"ip": 1}, "example": "peer 10.0.0.5 seen"},
            "holds text that masking would still change",
        ),
    ],
)
def test_a_bad_privacy_block_is_reported_and_build_refuses_it(
    privacy: object, problem: str
) -> None:
    problems = validate_receipt({**BASE, "privacy": privacy})
    assert any(problem in text for text in problems), problems
    with pytest.raises(ValueError, match="invalid receipt"):
        build_receipt({**BASE, "privacy": privacy})


def test_a_well_formed_privacy_block_is_accepted() -> None:
    good = {"placeholders": {"ip": 2}, "example": "peer [redacted:ip] seen"}
    assert validate_receipt({**BASE, "privacy": good}) == []


def test_a_version_quad_kept_by_its_v_is_the_example_when_the_window_holds_the_v() -> None:
    line = "v1.2.3.4" + " " * 22 + "[redacted:host]"
    record = privacy_record([("a", line)])
    assert record is not None
    assert record["example"] == line
    assert validate_receipt({**BASE, "privacy": record}) == []


@pytest.mark.parametrize(
    "line",
    [
        # The window starts at `1.2.3.4`: without its `v` the address is masked, so it is skipped.
        "v1.2.3.4" + " " * 23 + "[redacted:host]",
        # The window starts after `==`, so the quad is a bare address again.
        "==1.2.3.4" + " " * 23 + "[redacted:ip]",
        # The window starts inside a 16-digit timestamp, so its `created_at:` key is gone.
        "created_at: 1731000000000123" + " " * 14 + "[redacted:ip]",
    ],
    ids=["v-cut", "equals-cut", "timestamp-key-cut"],
)
def test_a_window_whose_cut_would_unmask_text_is_skipped(line: str) -> None:
    assert masked_example([("a", line)]) is None
    assert privacy_record([("a", line)]) is None


def test_a_type_name_longer_than_32_characters_is_not_a_placeholder() -> None:
    hostile = "[redacted:" + "a" * 60_000 + "]"
    assert placeholder_counts([("mallory", hostile)]) == {}
    assert privacy_record([("mallory", hostile)]) is None


def test_a_type_name_of_exactly_32_characters_is_counted() -> None:
    kind = "a" * 32
    assert placeholder_counts([("bob", f"[redacted:{kind}]")]) == {kind: 1}


FRAGMENTS = st.sampled_from(
    [
        "v",
        "==",
        "1.2.3.4",
        "10.0.0.5",
        " ",
        "\t",
        "[redacted:host]",
        "[redacted:ip]",
        "[redacted]",
        "[redacted:x]",
        "created_at: ",
        "1731000000000123",
        "@",
        "-",
        "token=",
        "x",
        "=",
    ]
)
LINES = st.one_of(st.lists(FRAGMENTS, max_size=40).map("".join), st.text(max_size=200))
TRANSCRIPTS = st.lists(st.tuples(st.just("bob"), LINES), max_size=4)


@settings(deadline=None, max_examples=300)
@given(TRANSCRIPTS)
def test_the_privacy_record_is_none_or_validates_for_any_transcript(
    messages: list[tuple[str, str]],
) -> None:
    record = privacy_record(messages)
    if record is not None:
        assert len(record["example"]) <= EXAMPLE_CHARS
        assert validate_receipt({**BASE, "privacy": record}) == []
