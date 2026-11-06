"""IPv4 versus version: the cues that may unmask a quad, and the uname host rule.

Privacy wins over version display. A quad is a version only with a `v` attached, `==` directly
before, or a pre-release or build tag after. `version 1.2.3.4` is masked by design.
"""

from __future__ import annotations

import pytest

from bailiff.redact import redact

MUST_MASK = [
    ("root@10.0.0.5", "root@[redacted:ip]"),
    ("ssh user@192.168.1.20", "ssh user@[redacted:ip]"),
    ("scp a bob@10.1.2.3:/tmp", "scp a bob@[redacted:ip]:/tmp"),
    ("- 10.0.0.5", "- [redacted:ip]"),
    ("10.0.0.1-10.0.0.9", "[redacted:ip]-[redacted:ip]"),
    ("range 10.0.0.1-10.0.0.9", "range [redacted:ip]-[redacted:ip]"),
    ("host-1.2.3.4", "host-[redacted:ip]"),
    ("10.0.0.5-eth0", "[redacted:ip]-eth0"),
    ("10.0.0.5-devbox", "[redacted:ip]-devbox"),
    ("k8s node 10.0.0.5 NotReady", "k8s node [redacted:ip] NotReady"),
    ("Node 172.16.4.4 down", "Node [redacted:ip] down"),
    ("version 10.0.0.5", "version [redacted:ip]"),
    ("version 1.2.3.4", "version [redacted:ip]"),
]

MUST_SURVIVE = [
    "v22.11.0",
    "v1.2.3.4",
    "pkg==1.2.3.4",
    "1.2.3.4-rc1",
    "1.2.3.4-alpha.2",
    "1.2.3.4+build5",
    "1.2.3.4.5",
    "1.2.3",
    "10.0.19045.4894",
]

UNAME_VERSION = "Linux version 5.15.0-91-generic (buildd@lcy02) #1 SMP"


@pytest.mark.parametrize(("text", "expected"), MUST_MASK, ids=[t for t, _ in MUST_MASK])
def test_an_address_behind_a_non_version_cue_is_masked(text: str, expected: str) -> None:
    out, hits = redact(text)
    assert out == expected
    assert hits == out.count("[redacted:ip]")
    assert "10." not in out


@pytest.mark.parametrize("text", MUST_SURVIVE)
def test_a_real_version_form_survives(text: str) -> None:
    assert redact(text) == (text, 0)


def test_the_kernel_line_from_proc_version_names_no_host() -> None:
    assert redact(UNAME_VERSION) == (UNAME_VERSION, 0)


def test_a_real_hostname_in_uname_is_still_masked_after_the_version_skip() -> None:
    assert redact("Linux bob-staging 6.8.0-45-generic #45-Ubuntu SMP") == (
        "Linux [redacted:host] 6.8.0-45-generic #45-Ubuntu SMP",
        1,
    )
