import pytest

from bailiff.redact import MARKER, redact

TOKEN_SAMPLES = [
    ("charge with sk_live_51HabcdefGHIJKLMNOP now", "sk_live_51HabcdefGHIJKLMNOP"),
    ("key sk-proj-AbCdEfGhIjKlMnOpQrSt in use", "sk-proj-AbCdEfGhIjKlMnOpQrSt"),
    ("Authorization: Bearer abc.def-123_xyz", "abc.def-123_xyz"),
    ("ghp_" + "a" * 36, "ghp_" + "a" * 36),
    (
        "jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2lnbmF0dXJl",
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2lnbmF0dXJl",
    ),
]

IDEMPOTENT_SAMPLES = [
    "DATABASE_PASSWORD=hunter2\nTZ=UTC",
    "Authorization: Bearer abc.def-123_xyz",
    "clone https://ci-bot:s3cret@git.example.com/repo.git",
    "key sk_live_51HabcdefGHIJKLMNOP and ghp_" + "a" * 36,
    "",
]


def test_masks_key_value_secrets_and_keeps_keys() -> None:
    text = "PATH=/usr/bin\nDATABASE_PASSWORD=hunter2\nAPI_KEY=abc123\nTZ=UTC"
    out, count = redact(text)
    assert out == f"PATH=/usr/bin\nDATABASE_PASSWORD={MARKER}\nAPI_KEY={MARKER}\nTZ=UTC"
    assert count == 2


def test_empty_secret_value_is_still_masked() -> None:
    assert redact("SECRET=") == (f"SECRET={MARKER}", 1)


@pytest.mark.parametrize(("text", "secret"), TOKEN_SAMPLES)
def test_masks_token_formats(text: str, secret: str) -> None:
    out, count = redact(text)
    assert secret not in out
    assert MARKER in out
    assert count == 1


def test_masks_url_password_and_keeps_host() -> None:
    out, count = redact("clone https://ci-bot:s3cret@git.example.com/repo.git now")
    assert out == f"clone https://ci-bot:{MARKER}@git.example.com/repo.git now"
    assert count == 1


@pytest.mark.parametrize("text", IDEMPOTENT_SAMPLES)
def test_redaction_is_idempotent(text: str) -> None:
    once, _ = redact(text)
    twice, second_count = redact(once)
    assert twice == once
    assert second_count == 0


@pytest.mark.parametrize(
    "text",
    ["", "=", "==x==", "\x00\ud800 PASSWORD=\r\n", "Bearer ", "://@:", "a" * 200_000],
)
def test_never_raises_on_odd_input(text: str) -> None:
    out, count = redact(text)
    assert isinstance(out, str)
    assert count >= 0
