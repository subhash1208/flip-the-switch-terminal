from dataclasses import replace

from bailiff.models import AblationStep, Runner, StepResult, Suspect

_NODE22_CMD = ["/opt/node22/bin/node", "test.js"]
_ABLATED = frozenset({"node", "tz", "node_options"})
NOT_ABLATED_MASKED = "not ablated: value masked"


def _masked(suspect: Suspect) -> bool:
    """A masked display value holds a placeholder, which is not a value to put in a command."""
    return "[redacted" in suspect.alice or "[redacted" in suspect.bob


def _step_for(suspect: Suspect, base: Runner) -> tuple[str, Runner]:
    if suspect.name == "node":
        return "node", Runner(base.image, dict(base.env), list(_NODE22_CMD))
    if suspect.name == "tz":
        return "tz", Runner(base.image, {**base.env, "TZ": suspect.alice}, list(base.cmd))
    if suspect.name == "node_options":
        env = {**base.env, "NODE_OPTIONS": suspect.alice}
        return "node_options", Runner(base.image, env, list(base.cmd))
    return f"{suspect.name} (no-op)", Runner(base.image, dict(base.env), list(base.cmd))


def plan_ablation(
    suspects: list[Suspect], failing_machine: str = "bob", base: Runner | None = None
) -> list[AblationStep]:
    root = Runner("node:18-bookworm-slim", {}, ["node", "test.js"]) if base is None else base
    steps: list[AblationStep] = []
    for index, suspect in enumerate(suspects, start=1):
        if _masked(suspect):
            continue
        variable, runner = _step_for(suspect, root)
        steps.append(
            AblationStep(
                id=f"ablation-{index}",
                machine=failing_machine,
                variable=variable,
                from_value=suspect.bob,
                to_value=suspect.alice,
                runner=runner,
            )
        )
    return steps


def classify(suspects: list[Suspect], results: list[StepResult]) -> list[Suspect]:
    outcomes = {result.id: result.outcome for result in results}
    culprit_found = False
    classified: list[Suspect] = []
    for index, suspect in enumerate(suspects, start=1):
        outcome = outcomes.get(f"ablation-{index}")
        verdict, note = suspect.verdict, suspect.note
        if _masked(suspect):
            verdict, note = "unknown", NOT_ABLATED_MASKED
        elif suspect.name not in _ABLATED:
            verdict = "unknown"
        elif outcome == "pass" and not culprit_found:
            verdict = "culprit"
            culprit_found = True
        elif outcome == "fail":
            verdict = "decoy"
        classified.append(replace(suspect, verdict=verdict, note=note))
    return classified
