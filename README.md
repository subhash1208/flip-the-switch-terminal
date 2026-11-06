# ParityCourt

**"Works on my machine" is now evidence: each machine's own agent testifies, and each owner signs for their own machine.**

Hackathon: [Flip the Switch](https://www.wemakedevs.org/hackathons/switch) (Nov 4–7, 2026), Track 01 Best Business Workflow. Team Terminal.

---

## How Switch is used

ParityCourt is three Switch agents working one bug case in one Switch room. Each real machine has its own agent. A neutral arbiter runs the case.

| Agent | Runs on | What it does | Who may approve its probes |
|---|---|---|---|
| `@alice-claude` (role `baseline-counsel`) | Claude Code on Alice's machine (macOS host, or the Alice container on the judge path) | Fingerprints its machine, proposes allow-listed probes, writes the fix | Alice only |
| `@bob-codex` (role `forensic-prosecutor`) | Codex on the failing machine (Ubuntu 24.04 over SSH in the recorded run; the Bob container on the judge path) | Fingerprints the failing machine, runs the one ablation, re-runs the failing test | Bob only |
| `@bailiff` (role `court-arbiter`) | Custom Python agent in [`bailiff/`](bailiff/) | Opens the case, keeps the case file, diffs fingerprints, redacts env dumps, writes `receipt.json` | Nobody. It holds no approval power. |

**Room setup**

- One room per case. The room's documents are the case file.
- The Bailiff creates the case-file document itself, because only the agent that creates a room document may edit it.
- Each agent has its own connection id. Reusing an id is a takeover: the displaced connection receives `taken_over`, which is final.
- The Bailiff subscribes with `filter=all`. A connection with `filter=addressed` never receives `command` events.
- A newly registered agent answers only its owner and the owner's other agents until its addressing policy is changed.

**Transport**

- Inbound: WebSocket `GET /agents/{agent_id}/connection/ws?connection_id=<uuid>&rooms=<id>`. Answer every `ping` with `{"type":"pong","cursor":N}` before processing events. Six seconds of silence evicts the connection (`heartbeat_lapsed`); reopen and resume from your cursor.
- Outbound: HTTP calls to Switch.
- Custom agents: register each one once with `POST /agents`. Not `POST /agents/register-known`: that endpoint covers only the agent types Switch Console runs.

**Owner-only approval** is enforced by Switch's addressing gate, not by message text. The gate covers approval answers as well as commands, so a `[Allow]` press is checked against the clicker's Switch identity. Verified by reading Switch core code (`session_activity/service.py:483-485` and `:599-603`). Live test: `(to be verified)`. Keep the default addressing policy; never set `anyone`.

*Delete Switch and these agents can't see each other's machines. There is no shared room for the case file and no owner-scoped gate on each machine's probes.*

---

## The 60-second story

What one case run is designed to show. The offline demo simulates steps 3 and 4 with canned output. On a live Switch room they are `(to be verified)`.

1. **Fingerprint both machines.** Each agent runs its allow-listed probes (`uname -a`, `node -v`, `env`, `git config core.ignorecase`). Its owner approves each one.
2. **Redacted env diff.** Secret-looking values are masked before they reach room history. The Bailiff posts the clean diff to the case file.
3. **One ablation isolates the cause.** The env diff sets aside the decoys (`TZ`, `NODE_OPTIONS`). Bob's failing test runs under Node 22 instead of Node 18 and passes, which points at the Node major version. `(to be verified)`
4. **Fix verified on the failing machine.** The fix counts only if the failing test passes on Bob's machine, not on Alice's. `(to be verified)`
5. **Receipt and replay.** `receipt.json` lists every step. `replay` re-runs them and prints the outcomes.
6. **Owner attestation.** Each owner attests to their own side, on their own machine.

---

## Quick start (no accounts, no keys)

**Prerequisites**

- Python 3.11+ (`requires-python` in [`pyproject.toml`](pyproject.toml))
- [`just`](https://github.com/casey/just). On Windows, `just` needs `sh` on PATH, for example from Git for Windows. Without `just`, use the plain `python` commands; they always work.
- Docker, only for the container replay and the judge-path check

```
python -m pip install -e ".[dev]"    # (to be verified)
just demo                            # same as: python -m bailiff.demo --offline
```

**Offline demo: SIMULATED.** `just demo` runs the real Bailiff flow against an in-memory room ([`bailiff/scripted/fake_room.py`](bailiff/scripted/fake_room.py)). Alice and Bob are scripted agents that replay canned output from `bailiff/scripted/fixtures/`, so the machine outputs are canned fixtures. No Switch server, no Docker, no LLM key. It prints the room messages, writes `receipt.json` to the current directory, and exits 0. Key lines, abridged:

```
SIMULATED offline demo (scripted agents, in-memory room)
suspects: tz, node, node_options, os
culprit:  node (ablation-2)
fix:      re-run on bob passes
redactions: 2
replay: 4/4 steps matched
```

`python -m bailiff.demo --live` is not built yet: it prints a TODO and exits 2.

**Replay in containers (needs Docker)**

```
just replay        # after the offline demo: re-runs receipt.json steps with docker run
just judge-check   # runs the judge-path check (needs Docker)
just demo-docker   # docker compose build, then the judge-path check (needs Docker; not yet run)
```

`just judge-check` runs [`scripts/check_judge_path.py`](scripts/check_judge_path.py), and `just demo-docker` runs `docker compose build` first. The check expects five results: Alice on Node 22 passes; Bob on Node 18 fails with `toSorted is not a function`; Bob's Node 22 binary passes; Alice with `TZ=UTC` passes; Alice with Bob's `NODE_OPTIONS` passes. Exit 0 means every case matched, 1 means a FAIL, 2 means Docker is not on PATH. Not yet run: `(to be verified)`

**Run it on a real Switch room (live mode in progress)**

The live entry point is the Bailiff agent process, `python -m bailiff.agent`.

1. Self-host Switch with Docker Compose, following the [self-host guide](https://docs.switchagents.ai/switch-rooms/deploy/self-host). Pin the Switch version it names (`SWITCH_VERSION` is not confirmed in the docs: `(to be verified)`). Set `SECRET_KEYS` (`<id>:<secret>` pairs, each secret at least 32 characters) and `AGENT_REGISTRATION_TOKEN`. Keep both out of git.
2. Register `alice-claude`, `bob-codex` and `bailiff` with `POST /agents`, using a registration key from your own account. The docs say agents registered with the bootstrap key belong to a separate account. The response returns each agent's API key once. Store keys in environment variables, never in the repo.
3. Keep every agent on the default addressing policy, which admits its owner and the owner's agents. Never set `anyone`.
4. Start the Bailiff with `python -m bailiff.agent`. It reads `BAILIFF_BASE_URL`, `BAILIFF_AGENT_ID`, `BAILIFF_API_KEY`, `BAILIFF_CONNECTION_ID` (a UUID, reused on every reconnect), `ROOM_ID` and `RECEIPT_PATH`. Optional: `ALICE_HANDLE`, `BOB_HANDLE`, `STEP_TIMEOUT`.
5. In the room, open a case: `!open case <title>` or `@bailiff open case <title>`.

---

## receipt.json

The Bailiff writes `receipt.json` to `RECEIPT_PATH`. The offline demo writes it to `--receipt` (default `receipt.json`, or `RECEIPT_PATH` if set). Each run generates the file; it is not source and is not part of the repo. Fields come from [`bailiff/receipt.py`](bailiff/receipt.py):

| Field | Contents |
|---|---|
| `schema_version` | Always `1` |
| `case_id`, `created_at`, `room_id` | Case identity and room |
| `pinned` | `app_commit` and the `images` used for `alice` and `bob` |
| `baseline` | Alice's run: `machine`, `cmd`, `exit_code`, `outcome`, `stderr_excerpt` |
| `failure` | Bob's run, same shape as `baseline` |
| `steps` | Each ablation step: `id`, `machine`, `variable`, `from`, `to`, `runner` (`image`, `env`, `cmd`), `exit_code`, `outcome`, `pinned` |
| `suspects` | `name`, `alice`, `bob`, `verdict` (`unknown`, `decoy` or `culprit`) |
| `culprit` | `variable` and `evidence_step` (must name an existing step) |
| `fix` | `branch`, `verified_on`, `outcome` |
| `attestations` | Per owner: `machine`, `owner`, `at`, `approval_message_id` |
| `redactions` | Count of redacted values |

```
python -m bailiff.replay receipt.json --docker
```

Replay validates the receipt, re-runs each step with `docker run` using the recorded image, env and command, and prints one line per step (`<id>: ok` or `MISMATCH`, with exit code and outcome). It then prints `N/N steps matched` and exits 0 only if every step matches. Without `--docker` it exits 2.

---

## Repository layout

```
bailiff/                       the Bailiff agent, receipt and replay tooling
  agent.py                     entry point (python -m bailiff.agent) and case flow
  transport.py, events.py      Switch WebSocket/HTTP connection and wire events
  state.py                     case state and turn cap
  ablation.py, fingerprint.py  plan and classify the ablation; parse and diff fingerprints
  allowlist.py, redact.py      allow-listed probes; secret redaction
  receipt.py, replay.py        receipt schema; python -m bailiff.replay
  demo.py                      python -m bailiff.demo --offline
  scripted/                    simulated agents, in-memory room, fixtures
sample-app/export-service/     Node app with auth middleware
  test.js                      the failing test
  src/                         export.js, sqlAuthGuard.js
  case-demo/                   SqlAuthGuard.js and consumer.js (case-only import)
  docs-case-bug/               notes on the case bug
deploy/                        Dockerfile.alice, Dockerfile.bob, docker-compose.yml
scripts/check_judge_path.py    judge-path check (needs Docker)
tests/                         pytest suite for bailiff/
docs/PARITYCOURT.md            full design, flow, risks, judge path
justfile, pyproject.toml       commands and project metadata
```

---

## Tests

- `just test` runs `python -m pytest -q` over `tests/`. The last full run passed. The count changes, so see the output of `just test`.
- `just check` runs ruff (lint and format check) over `bailiff`, `tests` and `scripts`. `just typecheck` runs mypy in strict mode over `bailiff/`.

---

## Honest limits

| Piece | Status |
|---|---|
| Receipt format, validation and `replay` | Code in `bailiff/receipt.py` and `bailiff/replay.py`; pytest coverage in `tests/` |
| Offline demo | Simulated: in-memory room, scripted agents, canned output |
| Judge path | Two Node containers: Alice runs Node 22; Bob's image has Node 22 and Node 18 stages ([`deploy/`](deploy/)). Not a Mac or an Ubuntu box. Containers not yet built or run `(to be verified)`. |
| Switch-room mode | `(live mode in progress)` |
| Owner-only approval | Verified by reading Switch code; live test `(to be verified)` |
| Case-only import on a real Mac | Replayed and recorded per the design doc; recording location `(to be verified)` |

- **Approval identity is the participant's name, not a signed identity.** An attestation records who said yes. It is not a cryptographic signature.
- **Probes are allow-listed.** Agents run only approved commands and never read `.env` files.
- **Scripted agents stand in for Claude Code and Codex** on the keyless path. The recorded run uses the real agents `(to be verified against the recording)`.
- **The judge path reproduces a Node-version bug**, not the case bug. The `toSorted` failure on Node 18 was reproduced on real Node 18.20.8 vs Node 22.23.4 on the author's machine (via npx). Inside the Docker containers it is `(to be verified)` by running `just demo-docker`.
- **The case-only import is the real-world analogue.** `SqlAuthGuard` vs `sqlAuthGuard` fails on a case-sensitive filesystem (ext4) and resolves on a case-insensitive one (APFS). The judge containers do not reproduce it. A privileged case-insensitive mount to reproduce it is untested.
- **Switch has no loop breaker or dual sign-off.** The turn cap is Bailiff code and is optional.
- **Secret redaction is best effort.** It combines Switch's guardrail with a regex. It is not a guarantee against every secret format.
- **Verification covers one test.** A passing re-run of the failing test is not proof the fix is correct beyond that test.

---

## Built by voice

Prompts, agent instructions and documentation for this project were dictated with Wispr Flow, for the Code with Wispr side track.

---

## Links

- Hackathon: https://www.wemakedevs.org/hackathons/switch
- Switch docs: https://docs.switchagents.ai
- Switch repo: https://github.com/sandbox-quantum/switch
- Full design, flow, risks and judge path: [docs/PARITYCOURT.md](docs/PARITYCOURT.md)
