import time

import pytest

from bailiff.redact import MARKER, mask_secret_lines, redact

LIMIT_S = 3.0  # a quadratic scan on these shapes would take 10 s or more

# Each shape is about 200k characters. A quadratic scan over any of them would take seconds.
SHAPES = {
    "secret-word-run": "token" * 40_000,
    "auth-word-run": "a-auth" * 40_000,
    "password-word-run": "password" * 25_000,
    "secret-space-run": "secret " * 28_572,
    "secret-equals-run": "token=" * 33_334,
    "json-quote-then-secret-run": '"' + "token" * 40_000,
    "non-secret-equals-run": "a=" * 100_000,
    "cookie-colon-run": "cookie:" * 28_572,
    "flag-space-run": "--token " * 22_222,
    "url-userinfo-run": "https://u:" * 20_000,
    "colon-then-spaces": "token:" + " " * 199_994,
    "one-long-key-run": "x" * 200_000,
    "github-pat-run": "github_pat_" * 18_000,
    "slack-token-run": "xoxb-" * 40_000,
    "npm-token-run": "npm_" * 50_000,
    "passphrase-space-run": "passphrase " * 20_000,
    "curl-user-run": "curl -u " * 25_000,
    "nbsp-password-run": "password:\u00a0" * 20_000,
    "fullwidth-colon-run": "password\uff1a" * 20_000,
    "argv-repr-run": "['--password', 'x'], " * 10_000,
}


def test_secret_word_run_is_redacted_in_under_a_second() -> None:
    text = "token" * 40_000 + "=x"
    started = time.perf_counter()
    out, hits = redact(text)
    assert time.perf_counter() - started < LIMIT_S
    assert out == "token" * 40_000 + f"={MARKER}"
    assert hits == 1


@pytest.mark.parametrize("text", list(SHAPES.values()), ids=list(SHAPES))
def test_adversarial_shape_is_redacted_in_linear_time(text: str) -> None:
    started = time.perf_counter()
    redact(text)
    assert time.perf_counter() - started < LIMIT_S


PII_SHAPES = {
    "digit-run": "1" * 200_000,
    "digit-space-run": "1 " * 100_000,
    "hex-pair-run": "ab" * 100_000,
    "dotted-letter-run": "a." * 100_000,
    "colon-run": ":" * 200_000,
    "colon-hex-run": "a:" * 100_000,
    "at-sign-chain": "a@" * 100_000,
    "windows-users-repeat": "C:\\Users\\" * 20_000,
    "posix-home-repeat": "/home/" * 33_334,
    "posix-users-chain": "/Users/a" * 25_000,
    "posix-home-chain": "/home/a/home/a" * 12_500,
    "windows-users-chain": "C:\\Users\\a" * 25_000,
    "identity-key-run": "USER=" * 40_000,
    "dotted-quad-run": "1.1." * 66_667,
    "phone-plus-run": "+1" * 100_000,
    "mac-pair-run": "aa:" * 66_667,
    "uname-kernel-run": "Linux " * 33_334,
    "ipv4-tag-run": "1.2.3.4-rc1 " * 16_667,
    "ipv4-at-run": "root@10.0.0.5 " * 15_385,
    "ipv4-dash-run": "10.0.0.5-" * 22_223,
    "ipv4-plus-run": "1.2.3.4+x" * 22_222,
}


@pytest.mark.parametrize("text", list(PII_SHAPES.values()), ids=list(PII_SHAPES))
def test_adversarial_pii_shape_is_redacted_in_linear_time(text: str) -> None:
    started = time.perf_counter()
    redact(text)
    assert time.perf_counter() - started < LIMIT_S


# Shapes for the regexes that start a scan at many positions. Each is about 200k characters.
MASK_SHAPES = {
    "backslash-n-run": "\\n" * 100_000,
    "ab-backslash-n-run": "ab\\n" * 66_667,
    "quote-a-run": '"a' * 100_000,
    "a-equals-run": "a=" * 100_000,
    "json-escaped-envelope": '{"stdout":"' + "ab\\n" * 40_000 + '"}',
    "json-escaped-token-lines": '{"stdout":"' + "TOKEN=x\\n" * 25_000 + '"}',
    "real-newline-token-lines": "TOKEN=x\n" * 25_000,
    "json-pair-run": '"a": "' * 28_572,
    "single-quote-pair-run": "'a': '" * 28_572,
    "url-segment-run": "https://u:p" * 20_000,
    "url-at-run": "https://u:p@" * 20_000,
    "ssh-git-run": "ssh://git@" * 20_000,
    "version-cue-run": "version 1.2.3.4-" * 14_000,
    "created-at-run": "created_at: 1731000000000123 " * 6_000,
    "linux-backslash-n-run": "Linux \\n" * 33_334,
}


@pytest.mark.parametrize("text", list(MASK_SHAPES.values()), ids=list(MASK_SHAPES))
def test_mask_secret_lines_is_linear_on_adversarial_shapes(text: str) -> None:
    started = time.perf_counter()
    mask_secret_lines(text)
    assert time.perf_counter() - started < LIMIT_S


@pytest.mark.parametrize("text", list(MASK_SHAPES.values()), ids=list(MASK_SHAPES))
def test_redact_of_mask_secret_lines_is_linear_on_adversarial_shapes(text: str) -> None:
    started = time.perf_counter()
    redact(mask_secret_lines(text)[0])
    assert time.perf_counter() - started < LIMIT_S
