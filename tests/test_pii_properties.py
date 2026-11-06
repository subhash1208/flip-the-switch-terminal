"""Property tests for the PII rules: no crash, idempotent, no personal value survives."""

from __future__ import annotations

import uuid

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from bailiff.redact import mask_secret_lines, redact

FAST = settings(deadline=None, max_examples=200)


def _luhn_valid(digits: str) -> bool:
    total = 0
    for position, char in enumerate(reversed(digits)):
        value = int(char)
        if position % 2:
            value = value * 2 - 9 if value > 4 else value * 2
        total += value
    return total % 10 == 0


def _with_check_digit(payload: str) -> str:
    return next(payload + digit for digit in "0123456789" if _luhn_valid(payload + digit))


EMAILS = st.builds(
    lambda local, labels, tld: f"{local}@{'.'.join(labels)}.{tld}",
    st.from_regex(r"[a-z][a-z0-9_]{0,15}", fullmatch=True),
    st.lists(st.from_regex(r"[a-z][a-z0-9]{0,8}", fullmatch=True), min_size=1, max_size=2),
    st.from_regex(r"[a-z]{2,6}", fullmatch=True),
)
IPV4S = st.tuples(*(st.integers(0, 255) for _ in range(4))).map(
    lambda octets: ".".join(str(octet) for octet in octets)
)
MACS = st.builds(
    lambda octets, sep: sep.join(f"{octet:02x}" for octet in octets),
    st.lists(st.integers(0, 255), min_size=6, max_size=6),
    st.sampled_from([":", "-"]),
)
CARDS = st.text(alphabet="0123456789", min_size=12, max_size=18).map(_with_check_digit)
SAFE_FRAGMENTS = st.sampled_from(
    [
        "alice@example.com",
        "/Users/alice",
        "C:\\Users\\bob",
        "USER=alice",
        "HOSTNAME=box",
        "Linux box 6.8.0-45",
        "10.0.0.1",
        "aa:bb:cc:dd:ee:ff",
        "2001:db8::1",
        "::",
        "4111 1111 1111 1111",
        "123-45-6789",
        "+14155550123",
        "123456789012345",
        "[redacted:user]",
        "[redacted]",
        "TOKEN=",
        "Bearer ",
        "sk_live_" + "a" * 16,
        " ",
        "\n",
        "=",
        ":",
        "@",
        ".",
        "-",
        "x",
        "9",
    ]
)
TEXT = st.one_of(
    st.text(max_size=300),
    st.lists(SAFE_FRAGMENTS, max_size=40).map("".join),
)


@FAST
@given(TEXT)
def test_redact_never_raises_on_text_full_of_personal_fragments(text: str) -> None:
    out, hits = redact(text)
    assert isinstance(out, str)
    assert hits >= 0


@FAST
@given(TEXT)
def test_redaction_is_idempotent_for_personal_fragments(text: str) -> None:
    once, _ = redact(text)
    assert redact(once) == (once, 0)


@FAST
@given(TEXT)
def test_output_grows_by_at_most_24_characters_per_hit(text: str) -> None:
    out, hits = redact(text)
    assert len(out) <= len(text) + 24 * hits


@FAST
@given(EMAILS)
def test_no_generated_email_survives(email: str) -> None:
    out, hits = redact(f"mail {email} end")
    assert email not in out
    assert hits >= 1


@FAST
@given(IPV4S)
def test_no_valid_ipv4_survives_except_loopback_and_unspecified(ip: str) -> None:
    assume(ip not in ("127.0.0.1", "0.0.0.0"))
    out, _ = redact(f"ip {ip} end")
    assert ip not in out


@FAST
@given(MACS)
def test_no_mac_address_survives(mac: str) -> None:
    out, _ = redact(f"nic {mac} end")
    assert mac.lower() not in out.lower()


@FAST
@given(CARDS)
def test_no_luhn_valid_card_survives(card: str) -> None:
    out, _ = redact(f"card {card} end")
    assert card not in out


@FAST
@given(st.integers(0, 99_999), st.integers(0, 99_999), st.integers(0, 99_999))
def test_three_part_versions_survive(major: int, minor: int, patch: int) -> None:
    text = f"v{major}.{minor}.{patch}"
    assert redact(text) == (text, 0)


@FAST
@given(
    st.integers(0, 99_999),
    st.integers(0, 99_999),
    st.integers(0, 99_999),
    st.integers(1, 99),
)
def test_kernel_release_strings_survive(a: int, b: int, c: int, d: int) -> None:
    text = f"{a}.{b}.{c}-{d}-generic"
    assert redact(text) == (text, 0)


@FAST
@given(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
def test_clock_times_and_iso_timestamps_survive(hour: int, minute: int, second: int) -> None:
    clock = f"{hour:02d}:{minute:02d}:{second:02d}"
    assert redact(clock) == (clock, 0)
    iso = f"2026-11-06T{clock}+05:30"
    assert redact(iso) == (iso, 0)


@FAST
@given(st.text(alphabet="0123456789abcdef", min_size=64, max_size=64))
def test_sha256_hex_digests_survive(digest: str) -> None:
    text = f"sha256 {digest} end"
    assert redact(text) == (text, 0)


@FAST
@given(st.uuids())
def test_uuids_survive(identifier: uuid.UUID) -> None:
    text = f"id {identifier} end"
    assert redact(text) == (text, 0)


@FAST
@given(st.text(max_size=200))
def test_secret_line_masking_never_raises_and_is_idempotent(text: str) -> None:
    once, _ = mask_secret_lines(text)
    assert mask_secret_lines(once) == (once, 0)
