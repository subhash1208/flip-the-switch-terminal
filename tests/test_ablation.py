from bailiff.ablation import NOT_ABLATED_MASKED, classify, plan_ablation
from bailiff.models import Runner, StepResult, Suspect

BASE = Runner("node:18-bookworm-slim", {}, ["node", "test.js"])
SUSPECTS = [
    Suspect("tz", "Asia/Kolkata", "UTC", "unknown"),
    Suspect("node", "v22.11.0", "v18.20.4", "unknown"),
    Suspect("node_options", "", "--openssl-legacy-provider", "unknown"),
    Suspect("fs_case", "case-insensitive", "case-sensitive", "unknown"),
]


def test_plan_has_one_step_per_suspect_in_input_order() -> None:
    steps = plan_ablation(SUSPECTS, base=BASE)
    assert [s.id for s in steps] == ["ablation-1", "ablation-2", "ablation-3", "ablation-4"]
    assert [s.from_value for s in steps] == [
        "UTC",
        "v18.20.4",
        "--openssl-legacy-provider",
        "case-sensitive",
    ]
    assert [s.to_value for s in steps] == [
        "Asia/Kolkata",
        "v22.11.0",
        "",
        "case-insensitive",
    ]
    assert all(s.machine == "bob" for s in steps)


def test_each_step_changes_exactly_one_variable() -> None:
    tz, node, node_options, fs_case = plan_ablation(SUSPECTS, base=BASE)
    assert (tz.variable, tz.runner.env, tz.runner.cmd) == (
        "tz",
        {"TZ": "Asia/Kolkata"},
        BASE.cmd,
    )
    assert (node.variable, node.runner.env, node.runner.cmd) == (
        "node",
        {},
        ["/opt/node22/bin/node", "test.js"],
    )
    assert (node_options.variable, node_options.runner.env) == (
        "node_options",
        {"NODE_OPTIONS": ""},
    )
    assert fs_case.variable == "fs_case (no-op)"
    assert fs_case.runner == BASE


def test_classify_picks_first_pass_as_culprit_and_failures_as_decoys() -> None:
    results = [
        StepResult("ablation-1", 1, "fail", True),
        StepResult("ablation-2", 0, "pass", True),
        StepResult("ablation-3", 0, "pass", True),
        StepResult("ablation-4", 1, "fail", True),
    ]
    verdicts = [s.verdict for s in classify(SUSPECTS, results)]
    assert verdicts == ["decoy", "culprit", "unknown", "unknown"]


def test_classify_leaves_suspects_without_results_unknown() -> None:
    verdicts = [s.verdict for s in classify(SUSPECTS, [StepResult("ablation-1", 1, "fail", True)])]
    assert verdicts == ["decoy", "unknown", "unknown", "unknown"]


def test_a_no_op_suspect_is_never_the_culprit_even_when_its_step_passes() -> None:
    results = [
        StepResult("ablation-1", 1, "fail", True),
        StepResult("ablation-2", 1, "fail", True),
        StepResult("ablation-3", 1, "fail", True),
        StepResult("ablation-4", 0, "pass", True),
    ]
    verdicts = [s.verdict for s in classify(SUSPECTS, results)]
    assert verdicts == ["decoy", "decoy", "decoy", "unknown"]


MASKED_NODE_OPTIONS = Suspect(
    "node_options", "--inspect=[redacted:ip]:9229", "--inspect=[redacted:ip]:9229", "unknown"
)


def test_a_masked_suspect_gets_no_step_so_no_placeholder_reaches_an_env() -> None:
    assert plan_ablation([MASKED_NODE_OPTIONS], base=BASE) == []


def test_a_masked_from_value_alone_is_enough_to_skip_the_step() -> None:
    suspect = Suspect("tz", "Asia/Kolkata", "[redacted:host]", "unknown")
    assert plan_ablation([suspect], base=BASE) == []
    (verdict,) = classify([suspect], [])
    assert (verdict.verdict, verdict.note) == ("unknown", NOT_ABLATED_MASKED)


def test_a_masked_suspect_is_unknown_and_a_node_major_difference_is_still_the_culprit() -> None:
    suspects = [MASKED_NODE_OPTIONS, Suspect("node", "v22.11.0", "v18.20.4", "unknown")]
    steps = plan_ablation(suspects, base=BASE)
    assert [(step.id, step.variable) for step in steps] == [("ablation-2", "node")]
    verdicts = classify(suspects, [StepResult("ablation-2", 0, "pass", True)])
    assert [(s.name, s.verdict, s.note) for s in verdicts] == [
        ("node_options", "unknown", NOT_ABLATED_MASKED),
        ("node", "culprit", ""),
    ]
