# JUDGES.md

ParityCourt is cross-machine bug forensics: the same test fails on one machine and passes on
another. Bailiff isolates the variable that causes the difference and writes a `receipt.json`
that can be replayed. This page shows a judge how to check those claims in about a minute.

## Quick start

```
python -m pip install -e .              # once: installs websockets and httpx (pyproject.toml)
python scripts/judge.py                 # then run the judge
```

## The one command

```
python scripts/judge.py                 # all eight checks; check 8 needs Docker
python scripts/judge.py --no-docker     # checks 1-7 only
```

Exit code 0 means PASS. Exit code 1 means at least one check FAILed. SKIP never fails the run.

## Expected output (as run on the current tree)

Without Docker, `python scripts/judge.py --no-docker`:

```
 #  CHECK                          RESULT  EVIDENCE
 1  python version                 PASS  Python 3.13.14 (needs 3.11+)
 2  import bailiff                 PASS  imported from D:\Projects\flip-the-switch-terminal\bailiff\__init__.py
 3  demo runs offline              PASS  exit 0; replay: 4/4 steps matched (fixture replay, not Docker)
 4  receipt valid, culprit node    PASS  schema valid; culprit variable node, evidence step ablation-2
 5  privacy: no fixture PII        PASS  0 of 12 fixture values found; [redacted marker in receipt and stdout
 6  replay matches every step      PASS  4/4 steps matched (fixture replay of bob.json)
 7  sample test.js vs node version PASS  node v26: exit 0; expected exit 0
 8  live Docker judge path         SKIP  --no-docker given
NOTE: checks 3-6 are SIMULATED (in-process fake Switch room, canned fixtures, no Switch server). Check 7 runs real Node. Check 8 runs real Docker when present.
Live Switch-room evidence: (to be added) in docs/evidence/ or the demo video. See JUDGES.md.
JUDGE RESULT: PASS
```

With Docker, `python scripts/judge.py`, check 8 runs the live containers:

```
 #  CHECK                          RESULT  EVIDENCE
 1  python version                 PASS  Python 3.13.14 (needs 3.11+)
 2  import bailiff                 PASS  imported from D:\Projects\flip-the-switch-terminal\bailiff\__init__.py
 3  demo runs offline              PASS  exit 0; replay: 4/4 steps matched (fixture replay, not Docker)
 4  receipt valid, culprit node    PASS  schema valid; culprit variable node, evidence step ablation-2
 5  privacy: no fixture PII        PASS  0 of 12 fixture values found; [redacted marker in receipt and stdout
 6  replay matches every step      PASS  4/4 steps matched (fixture replay of bob.json)
 7  sample test.js vs node version PASS  node v26: exit 0; expected exit 0
 8  live Docker judge path         PASS  5/5 live cases PASS (exit 0)
NOTE: checks 3-6 are SIMULATED (in-process fake Switch room, canned fixtures, no Switch server). Check 7 runs real Node. Check 8 runs real Docker when present.
Live Switch-room evidence: (to be added) in docs/evidence/ or the demo video. See JUDGES.md.
JUDGE RESULT: PASS
```

Check 5 passes because the receipt's `privacy` block carries typed placeholders (`placeholders`
counts by type and one `example`), and the demo prints a masked example line. Both show
`[redacted:<type>]` markers, and no fixture value appears in either.

Check 7 prints the version of whichever Node is on PATH. The judge expects exit 0 on Node 20 or
newer, and a `toSorted is not a function` failure on Node 18 or older.

## What the checks prove

1. Python is 3.11 or newer.
2. `bailiff` imports from this checkout.
3. `python -m bailiff.demo --offline` runs and exits 0.
4. The receipt passes `validate_receipt`, and its culprit variable is `node`.
5. No synthetic PII from the fixtures appears in the receipt or demo output.
6. Every step in the receipt replays to the outcome it recorded.
7. The sample app's `test.js` behaves as its Node version predicts.
8. Live: `scripts/check_judge_path.py` runs the alice and bob containers under Docker.

## Real versus simulated

- Simulated: checks 3 to 6 run an in-process fake Switch room. Command output comes from the
  canned files in `bailiff/scripted/fixtures/`. No Switch server is involved.
- Real: check 7 runs `node test.js` with the Node on your PATH. Check 8 runs the containers.
- Not yet available: live Switch-room evidence. It is `(to be added)` in `docs/evidence/` or in
  the demo video.

## Prerequisites

- Python 3.11 or newer.
- Runtime dependencies: `python -m pip install -e .` from the repo root (declared in
  `pyproject.toml`). The judge imports `bailiff`, which imports `websockets` and `httpx`. The judge
  does not install them.
- Node, for check 7. Without Node, check 7 is SKIP.
- Docker, for check 8. Without Docker, check 8 is SKIP, or pass `--no-docker`.

## Commands

- `just demo` runs the offline demo and writes `receipt.json` in the repo root.
- `just judge` runs `scripts/judge.py`. `just judge-offline` runs it with `--no-docker`.
- `just ci` runs `check`, `typecheck`, `test`, and `judge-offline` in that order.

## Troubleshooting

- No `just` installed: run `python scripts/judge.py` directly. The recipes are shortcuts only.
- No Docker: run `python scripts/judge.py --no-docker`. Check 8 then reports SKIP, which is not a
  failure.
- Windows: `just` runs recipes through `sh`. Install Git for Windows so `sh` is on PATH, or run
  the Python commands directly.
- Check 2 FAIL with a missing module: run `python -m pip install -e .` from the repo root.
- Check 7 FAIL: run `node -v` and then `node test.js` inside `sample-app/export-service`, and
  read stderr.

## Where to read more

- `README.md` for the project overview.
- `docs/PARITYCOURT.md` for the design and the demo plan.
- `docs/evidence/` for live evidence (to be added).
