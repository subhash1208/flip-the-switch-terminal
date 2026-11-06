"""Case state: one case from opened to closed, rendered as a receipt dict or a room document."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from bailiff.privacy import privacy_record

ORDER = ("opened", "fingerprinting", "diffing", "ablating", "verifying", "attested", "closed")


class InvalidTransition(Exception):
    """A case was asked to move somewhere its order does not allow."""


class TurnCapExceeded(Exception):
    """A case used more agent-to-agent turns than its cap allows."""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass
class CaseState:
    case_id: str
    room_id: str
    title: str
    opened_by: str
    app_commit: str = "unknown"
    images: dict[str, str] = field(
        default_factory=lambda: {"alice": "node:22-bookworm-slim", "bob": "node:18-bookworm-slim"}
    )
    turn_cap: int | None = None
    simulated: bool = False
    inconclusive_reason: str | None = None
    created_at: str = field(default_factory=_now)
    state: str = "opened"
    doc_created: bool = False
    turns: int = 0
    redactions: int = 0
    doc_redactions: int = 0
    malformed: int = 0
    machines: dict[str, dict[str, Any]] = field(default_factory=dict)
    probes: list[dict[str, Any]] = field(default_factory=list)
    baseline: dict[str, Any] | None = None
    failure: dict[str, Any] | None = None
    suspects: list[dict[str, Any]] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    culprit: dict[str, Any] | None = None
    fix: dict[str, Any] | None = None
    attestations: list[dict[str, Any]] = field(default_factory=list)
    verdict: str | None = None
    transcript: list[tuple[str, str]] = field(default_factory=list)

    def transition(self, new: str) -> None:
        """Move one step forward, or to closed from any open state."""
        current, target = ORDER.index(self.state), ORDER.index(new)
        if target == current + 1 or (new == "closed" and current < target):
            self.state = new
            return
        raise InvalidTransition(f"{self.state} -> {new}")

    def turn(self) -> None:
        """Count one agent-to-agent turn; raise if a cap is set and exceeded."""
        self.turns += 1
        if self.turn_cap is not None and self.turns > self.turn_cap:
            raise TurnCapExceeded(f"{self.turns} turns exceeds cap of {self.turn_cap}")

    def to_case_dict(self) -> dict[str, Any]:
        """The case dict that bailiff.receipt.build_receipt consumes."""
        case: dict[str, Any] = {
            "case_id": self.case_id,
            "created_at": self.created_at,
            "room_id": self.room_id,
            "pinned": {"app_commit": self.app_commit, "images": dict(self.images)},
            "baseline": self.baseline,
            "failure": self.failure,
            "steps": list(self.steps),
            "suspects": list(self.suspects),
            "culprit": self.culprit,
            "fix": self.fix,
            "attestations": list(self.attestations),
            "redactions": self.redactions + self.doc_redactions,
        }
        if self.simulated:
            case["simulated"] = True
        record = privacy_record(self.transcript)
        if record is not None:
            case["privacy"] = record
        if self.inconclusive_reason is not None:
            case["inconclusive"] = True
            case["inconclusive_reason"] = self.inconclusive_reason
        return case

    def to_room_document(self) -> str:
        """Markdown case file: one fenced JSON block holds the machine-readable state."""
        body = {
            "case_id": self.case_id,
            "state": self.state,
            "opened_by": self.opened_by,
            "machines": {
                name: {"agent_handle": m["agent_handle"], "fingerprint": m["fingerprint"]}
                for name, m in self.machines.items()
            },
            "probes": self.probes,
            "suspects": self.suspects,
            "steps": self.steps,
            "verdict": self.verdict,
        }
        # Backticks become \u0060 (a valid JSON escape), so no string can close the fence early.
        blob = json.dumps(body, indent=2, sort_keys=True, default=str).replace("`", "\\u0060")
        title = self.title.replace("`", "'")
        return f"# Case {self.case_id}: {title}\n\n```json\n{blob}\n```\n"
