import pytest

from bailiff.redact import redact

FORMS = {
    "posix-users": "/Users/alice",
    "posix-home": "/home/alice",
    "windows-users": "C:\\Users\\alice",
}


@pytest.mark.parametrize("repeats", [1, 2, 6, 50])
@pytest.mark.parametrize("form", list(FORMS.values()), ids=list(FORMS))
def test_chained_home_paths_are_fully_masked_in_one_call(form: str, repeats: int) -> None:
    text = form * repeats
    out, hits = redact(text)
    assert "alice" not in out
    assert hits >= 1
    assert redact(out) == (out, 0)


@pytest.mark.parametrize("form", list(FORMS.values()), ids=list(FORMS))
def test_chained_home_paths_keep_safe_directories(form: str) -> None:
    safe = form.replace("alice", "Public")
    out, _ = redact(safe * 3)
    assert "Public" in out
