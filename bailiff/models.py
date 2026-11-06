from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True)
class Suspect:
    name: str
    alice: str
    bob: str
    verdict: str


@dataclass(frozen=True)
class Runner:
    image: str
    env: dict[str, str]
    cmd: list[str]


@dataclass(frozen=True)
class AblationStep:
    id: str
    machine: str
    variable: str
    from_value: str
    to_value: str
    runner: Runner


@dataclass(frozen=True)
class StepResult:
    id: str
    exit_code: int | None
    outcome: str
    matched: bool


RunnerFn: TypeAlias = Callable[[Runner], tuple[int, str]]
