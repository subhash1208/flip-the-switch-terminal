from dataclasses import replace

from bailiff.models import AblationStep, Runner, StepResult, Suspect

_NODE22_CMD = ["/opt/node22/bin/node", "test.js"]
_ABLATED = frozenset({"node", "tz", "node_options"})


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
        verdict = suspect.verdict
        if suspect.name not in _ABLATED:
            verdict = "unknown"
        elif outcome == "pass" and not culprit_found:
            verdict = "culprit"
            culprit_found = True
        elif outcome == "fail":
            verdict = "decoy"
        classified.append(replace(suspect, verdict=verdict))
    return classified
