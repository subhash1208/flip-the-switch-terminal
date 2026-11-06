"""Regressions from the third independent review: Python-repr pairs, URL and email edge cases,
version-looking IPv4, the timestamp guard, the stderr tail order, capped masking, and the
raw-value fingerprint comparison."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from bailiff.agent import serve
from bailiff.demo import privacy_line
from bailiff.fingerprint import diff_fingerprints, parse_fingerprint, raw_compared
from bailiff.models import Suspect
from bailiff.redact import MARKER, MAX_REDACT_CHARS, mask_bounded, mask_secret_lines, redact
from bailiff.scripted.fake_room import FakeRoom
from bailiff.scripted.runner import Runner, fixture_runner, serve_machine

FIXTURES = Path(__file__).resolve().parents[1] / "bailiff" / "scripted" / "fixtures"
TEST_CMD = ["node", "test.js"]
# Built from parts so no fixture literal looks like a credential to the scanners.
SECRET = "Q9" + "xK7mW" * 12 + "zt"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("{'password': 'a b'}", f"{{'password': '{MARKER}'}}"),
        ("{'token':'x'}", f"{{'token':'{MARKER}'}}"),
        ('{"password": "p\\"tail"}', f'{{"password": "{MARKER}"}}'),
        ('{"password": "p\\"' + SECRET + '"}', f'{{"password": "{MARKER}"}}'),
    ],
)
def test_python_repr_and_escaped_quote_pairs_are_masked(text: str, expected: str) -> None:
    out, hits = redact(text)
    assert out == expected
    assert hits == 1
    assert "xK7mW" not in out
    assert redact(out) == (out, 0)


def test_single_quoted_secret_with_a_space_leaks_nothing() -> None:
    out, _ = redact("{'password': '" + SECRET + " tail'}")
    assert SECRET not in out
    assert "tail" not in out


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("https://:Zq9xK7mW@h/", f"https://:{MARKER}@h/"),
        ("https://bob:pa/ss@h/", f"https://bob:{MARKER}@h/"),
    ],
)
def test_url_credentials_with_empty_user_or_slash_in_password_are_masked(
    text: str, expected: str
) -> None:
    out, hits = redact(text)
    assert out == expected
    assert hits == 1
    assert "Zq9xK7mW" not in out
    assert "pa/ss" not in out


def test_ssh_git_url_keeps_the_git_account_and_the_scp_form_still_survives() -> None:
    assert redact("ssh://git@github.com/org/repo.git") == (
        "ssh://git@github.com/org/repo.git",
        0,
    )
    assert redact("git@github.com:org/repo.git") == ("git@github.com:org/repo.git", 0)


def test_ssh_url_for_a_person_is_still_masked() -> None:
    assert redact("ssh://bob@example.com/repo") == ("ssh://[redacted:email]/repo", 1)


@pytest.mark.parametrize(
    ("text", "expected", "hits"),
    [
        ("1.2.3.4-rc1", "1.2.3.4-rc1", 0),
        ("peer 10.0.0.1", "peer [redacted:ip]", 1),
        ("0.0.0.0 and 127.0.0.1", "0.0.0.0 and 127.0.0.1", 0),
        ("127.0.0.2", "[redacted:ip]", 1),
    ],
)
def test_versions_and_unspecified_or_loopback_addresses_are_not_masked(
    text: str, expected: str, hits: int
) -> None:
    assert redact(text) == (expected, hits)


@pytest.mark.parametrize(
    "text",
    ["created_at: 1731000000000123", "created_at=1731000000000123", "at: 1731000000000123"],
)
def test_timestamp_keys_ending_in_at_are_not_masked_as_ids(text: str) -> None:
    assert redact(text) == (text, 0)


def test_a_bare_sixteen_digit_id_is_still_masked() -> None:
    assert redact("ID 1731000000000123") == ("ID [redacted:id]", 1)


def test_a_backslash_n_run_does_not_hide_a_secret_line() -> None:
    text = "A=1\\nTOKEN=abc def\\nB=2"
    assert mask_secret_lines(text) == ("A=1\\nTOKEN=[redacted]\\nB=2", 1)


def test_a_json_escaped_secret_line_is_masked_to_the_end_of_its_line() -> None:
    assert mask_secret_lines('{"stdout":"ab\\nTOKEN=x y"}') == (
        f'{{"stdout":"ab\\nTOKEN={MARKER}',
        1,
    )


def test_mask_bounded_masks_short_text_like_mask_then_redact() -> None:
    # The whole secret-named line is masked, so the trailing word goes with the value.
    assert mask_bounded("TOKEN=hunter2 tail") == (f"TOKEN={MARKER}", 1)


def test_mask_bounded_caps_before_masking_and_says_how_much_it_dropped() -> None:
    text = "TOKEN=" + "x" * MAX_REDACT_CHARS
    assert mask_bounded(text) == (f"TOKEN={MARKER}[truncated 6 chars]", 1)


def test_privacy_line_counts_placeholders_by_type_from_the_transcript() -> None:
    messages = [("a", f"x [redacted:email] y [redacted:email] {MARKER} [redacted:ip]")]
    assert privacy_line(messages) == (
        "privacy: masked email=2, ip=1, secret=1 (placeholders seen in the room transcript)"
    )


def test_privacy_line_says_so_when_the_transcript_has_no_placeholders() -> None:
    assert privacy_line([("a", "nothing masked here")]) == (
        "privacy: no placeholders seen in the room transcript"
    )


def _probes(node_options: str) -> dict[str, str]:
    return {
        "uname -a": "Darwin m 24.5.0 arm64",
        "node -v": "v22.1.0",
        "printenv TZ": "UTC",
        "printenv NODE_OPTIONS": node_options,
    }


def test_two_machines_that_differ_only_in_a_masked_looking_value_still_yield_a_suspect() -> None:
    alice = _probes("--dns-result-order=1.2.3.4")
    bob = _probes("--dns-result-order=5.6.7.8")
    fp_a = parse_fingerprint("alice", alice)
    fp_b = parse_fingerprint("bob", bob)
    assert fp_a["node_options"] == fp_b["node_options"] == "--dns-result-order=[redacted:ip]"
    (suspect,) = diff_fingerprints(fp_a, fp_b, raw_compared(alice), raw_compared(bob))
    assert suspect == Suspect(
        "node_options",
        "--dns-result-order=[redacted:ip]",
        "--dns-result-order=[redacted:ip]",
        "unknown",
    )
    assert "1.2.3.4" not in suspect.alice


def test_identical_raw_values_still_yield_no_suspect() -> None:
    same = _probes("--dns-result-order=1.2.3.4")
    fp = parse_fingerprint("alice", same)
    assert diff_fingerprints(fp, fp, raw_compared(same), raw_compared(same)) == []


def _machines(room: FakeRoom, bob_run: Runner) -> list[asyncio.Task[None]]:
    return [
        asyncio.create_task(
            serve_machine(
                room.join("alice-claude"),
                room.room_id,
                "alice",
                "alice-claude",
                fixture_runner(FIXTURES / "alice.json"),
            )
        ),
        asyncio.create_task(
            serve_machine(room.join("bob-codex"), room.room_id, "bob", "bob-codex", bob_run)
        ),
    ]


@pytest.mark.asyncio
async def test_stderr_excerpt_whose_tail_starts_inside_a_secret_leaks_nothing() -> None:
    # The secret starts 500 chars in on its own line. The newline and 350 more characters follow
    # it, so the 400-char tail begins 15 characters into the secret.
    stderr = "x" * 500 + "\nMY_SECRET_TOKEN=" + SECRET + "\n" + "done " * 70
    inner = fixture_runner(FIXTURES / "bob.json")

    async def failing(argv: list[str], overlay: dict[str, str]) -> dict[str, Any]:
        if argv == TEST_CMD:
            return {"exit_code": 1, "stdout": "", "stderr": stderr}
        return await inner(argv, overlay)

    room = FakeRoom()
    bailiff = room.join("bailiff")
    machines = _machines(room, failing)
    try:
        room.publish("dana", "!open case export-service 500 on Ubuntu")
        receipt = await asyncio.wait_for(serve(bailiff, room.room_id, step_timeout=5.0), timeout=30)
    finally:
        for task in machines:
            task.cancel()
        await asyncio.gather(*machines, return_exceptions=True)
    excerpt = receipt["failure"]["stderr_excerpt"]
    assert len(excerpt) == 400
    assert SECRET[15:] not in excerpt
    assert "xK7mW" not in excerpt
    assert MARKER in excerpt
