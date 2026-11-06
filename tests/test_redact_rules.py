import re

import pytest

from bailiff.redact import MARKER, MAX_REDACT_CHARS, redact, redact_bounded

RULE_CASES = [
    ("Authorization: Basic dXNlcjpwYXNz", "Authorization: [redacted]"),
    ("Authorization: Bearer abc.def-123", "Authorization: [redacted]"),
    ("Proxy-Authorization: Basic dXNl", "Proxy-Authorization: [redacted]"),
    ("Cookie: sid=abc123", "Cookie: [redacted]"),
    ("Set-Cookie: sid=abc123; Path=/", "Set-Cookie: [redacted]"),
    ("x-api-key: abc123", "x-api-key: [redacted]"),
    ("x-auth-token: abc123", "x-auth-token: [redacted]"),
    ("password: hunter2", "password: [redacted]"),
    ("client_secret: 'abc def'", "client_secret: [redacted]"),
    ("secret: c2VjcmV0+/==", "secret: [redacted]"),
    ("--password hunter2 --verbose", "--password [redacted] --verbose"),
    ('--api-key "a b" next', "--api-key [redacted] next"),
]


@pytest.mark.parametrize(("text", "expected"), RULE_CASES)
def test_header_colon_and_flag_secrets_are_masked(text: str, expected: str) -> None:
    out, hits = redact(text)
    assert out == expected
    assert hits == 1
    assert redact(out) == (out, 0)


def test_a_header_value_stops_at_the_line_end() -> None:
    assert redact("Cookie: a=b\nTOKEN=x") == ("Cookie: [redacted]\nTOKEN=[redacted]", 2)


@pytest.mark.parametrize(
    "text",
    [
        "password is hunter2",
        "--verbose yes",
        "Content-Type: text/plain",
        "HOME=/opt/app&LANG=en",
    ],
)
def test_prose_and_non_secret_names_are_left_alone(text: str) -> None:
    assert redact(text) == (text, 0)


@pytest.mark.parametrize(
    "key", ["PRIVATE_KEY", "MY_CREDENTIAL", "GH_AUTH", "API-KEY", "passwd", "MY_SECRET"]
)
def test_every_secret_word_masks_its_key(key: str) -> None:
    assert redact(f"{key}=abc") == (f"{key}={MARKER}", 1)


def test_redact_bounded_passes_short_text_through() -> None:
    assert redact_bounded("TOKEN=abc") == ("TOKEN=[redacted]", 1)


def test_redact_bounded_drops_the_tail_and_says_how_much() -> None:
    text = "a " * (MAX_REDACT_CHARS // 2) + "TOKEN=hunter2"
    out, hits = redact_bounded(text)
    match = re.search(r"\[truncated (\d+) chars\]$", out)
    assert match is not None
    assert "TOKEN" not in out and "hunter2" not in out
    assert hits == 0
    assert int(match.group(1)) == len(text) - (len(out) - len(match.group(0)))


def test_redact_bounded_counts_the_dropped_characters_of_an_unbroken_run() -> None:
    text = "a" * (MAX_REDACT_CHARS + 10)
    assert redact_bounded(text) == ("a" * MAX_REDACT_CHARS + "[truncated 10 chars]", 0)


def test_redact_bounded_never_splits_a_token_at_the_cut() -> None:
    text = "x " * (MAX_REDACT_CHARS // 2 - 1) + "sk_live_" + "Z" * 20
    out, _ = redact_bounded(text)
    assert "sk" not in out
    assert out.endswith("chars]")
