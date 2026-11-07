# ParityCourt

**"Works on my machine" is now evidence: each machine's own agent testifies, and each machine's owner approves its probes and attests to that machine's side.**

Hackathon: [Flip the Switch](https://www.wemakedevs.org/hackathons/switch) (Nov 4–7, 2026), Track 01 — Best Business Workflow. Team Terminal.

Demo video: [VIDEO_URL]

---

## How Switch is used

ParityCourt is three Switch agents working on one bug case in one Switch room. Each real machine has its own agent. A neutral arbiter runs the case.

| Agent | Runs on | What it does | Who may approve its probes |
|---|---|---|---|
| `@alice-claude` (role `baseline-counsel`) | Claude Code on Alice's Mac, run by Switch Console (real in the `--alice-agent` live run; the judge path uses the scripted Alice container) | Fingerprints its machine, proposes allow-listed probes, writes the fix | Alice only |
| `@bob-codex` (handle only; role `forensic-prosecutor`) | Scripted Bob Node 18 container on the judge path, and scripted in the live run. Real Claude Code Bob: in progress. | Fingerprints the failing machine, runs the one ablation, re-runs the failing test | Bob only |
| `@bailiff` (role `court-arbiter`) | Custom Python agent in [`bailiff/`](bailiff/) | Opens the case, keeps the case file, diffs fingerprints, redacts env dumps, writes `receipt.json` | Nobody. It holds no approval power. |

**Room setup**

- One room per case. The room's documents are the case file.
- The Bailiff creates the case-file document itself, because only the agent that creates a room document may edit it.
- Each agent has its own connection ID. Reusing an ID is a takeover: the displaced connection receives `taken_over`, which is final.
- The Bailiff subscribes with `filter=all`. A connection with `filter=addressed` never receives `command` events.
- A newly registered agent answers only its owner and the owner's other agents until its addressing policy is changed.

**Transport**

- Inbound: WebSocket `GET /agents/{agent_id}/connection/ws?connection_id=<uuid>&rooms=<id>`. Answer every `ping` with `{"type":"pong","cursor":N}` before processing events. Six seconds of silence evicts the connection (`heartbeat_lapsed`); reopen and resume from your cursor.
- Outbound: HTTP calls to Switch.
- Custom agents: register each one once with `POST /agents`. Not `POST /agents/register-known`: that endpoint covers only the agent types Switch Console runs.

**Owner-only approval** is enforced by Switch's addressing gate, not by message text. The gate covers approval answers as well as commands, so an `[Allow]` press is checked against the clicker's Switch identity. Verified by reading Switch core code (`session_activity/service.py:483-485` and `:599-603`). Live test: `(to be verified)`. Keep the default addressing policy; never set `anyone`, except the optional real-Alice demo, which registers `alice-claude` as Anyone (see Live run with a real Alice); that weakens the owner-only gate for `alice-claude`, so keep Bob and the Bailiff on the default.

*Delete Switch, and these agents can't see each other's machines. There is no shared room for the case file and no owner-scoped gate on each machine's probes.*

---

## The 60-second story

This is what one case run is designed to show. The offline demo simulates steps 3 and 4 with canned output. In a live Switch room, steps 3 and 4 are `(to be verified)`.

1. **Fingerprint both machines.** Each agent runs its allow-listed probes (`uname -a`, `node -v`, `env`, `git config core.ignorecase`). Its owner approves each one.
2. **Redacted env diff.** Secret-looking values are masked before they reach room history. The Bailiff posts the clean diff to the case file.
3. **One ablation isolates the cause.** The env diff sets aside the decoys (`TZ`, `NODE_OPTIONS`). Bob's failing test runs under Node 22 instead of Node 18 and passes, which points at the Node major version. `(to be verified)`
4. **Fix verified on the failing machine.** The fix counts only if the failing test passes on Bob's machine, not on Alice's. `(to be verified)`
5. **Receipt and replay.** `receipt.json` lists every step. `replay` re-runs them and prints the outcomes.
6. **Owner attestation.** The machine owner attests to that machine's side.

---

## Quick start (no accounts, no keys)

**Prerequisites**

- Python 3.11+ (`requires-python` in [`pyproject.toml`](pyproject.toml)). CI runs 3.11 and 3.12. The offline demo was run on Python 3.13 on Windows.
- [`just`](https://github.com/casey/just). On Windows, `just` needs `sh` on PATH, for example from Git for Windows. Without `just`, use the plain `python` commands; they always work.
- Docker (only needed for the container replay and the judge-path check)

```
python -m pip install -e .           # the one prerequisite
python scripts/judge.py              # the one command: 8 checks, ends in JUDGE RESULT
```

`python scripts/judge.py` prints a PASS/FAIL/SKIP table for eight checks. Check 8 runs the live Docker judge path when Docker is on PATH and SKIPs otherwise. `--no-docker` skips it on purpose. The exit code is 1 if any check FAILs.

Alternatives:

```
python -m bailiff.demo --offline     # the offline demo; same as `just demo`
python -m pip install -e ".[dev]"    # adds pytest, ruff, mypy and hypothesis for the Quality commands
```

**Offline demo: SIMULATED.** `just demo` runs the real Bailiff flow against an in-memory room ([`bailiff/scripted/fake_room.py`](bailiff/scripted/fake_room.py)). Alice and Bob are scripted agents that replay canned output from `bailiff/scripted/fixtures/`, so the machine outputs are canned fixtures. No Switch server, no Docker, no LLM key. It prints the room messages, writes `receipt.json` to the current directory, and exits 0. Abridged output follows (room messages and the masked example are left out; `...` marks elided lines):

```
SIMULATED: in-process fake room, no Switch server
...
privacy: masked email=2, host=4, ip=2, secret=2, user=4 (placeholders seen in the room transcript)
...
replay: 4/4 steps matched (fixture replay, not Docker)
```

`python -m bailiff.demo --live` is merged to main. It needs `BAILIFF_BASE_URL` and `SWITCH_REGISTRATION_TOKEN`, registers `pc-live-bailiff` and `pc-live-bob`, plus a scripted Alice unless `--alice-agent NAME` names a Console-registered Claude Code agent. The room is `internal_only` unless `--chat-user NAME` is given, which binds it to the bundled Mattermost. It runs the case over real WebSockets against Switch 0.31.0. Bob and the fixture replay stay scripted. Transcript of the scripted run: [`docs/evidence/transcript.txt`](docs/evidence/transcript.txt).

**Replay in containers (needs Docker)**

```
just replay        # after the offline demo: re-runs receipt.json steps with docker run
just judge-check   # runs the judge-path check (needs Docker)
just demo-docker   # docker compose build, then the judge-path check (needs Docker)
```

`just judge-check` runs [`scripts/check_judge_path.py`](scripts/check_judge_path.py), and `just demo-docker` runs `docker compose build` first. The check expects five results: Alice on Node 22 passes; Bob on Node 18 fails with `toSorted is not a function`; Bob's Node 22 binary passes; Alice with `TZ=UTC` passes; Alice with Bob's `NODE_OPTIONS` passes. Exit 0 means every case matched, 1 means a FAIL, 2 means Docker is not on PATH. Docker run: container check 5/5.

**Run it on a real Switch room (live mode merged; a real Claude Code Alice verified in one live run (not in the repo transcript); Bob scripted)**

The live entry point is the Bailiff agent process, `python -m bailiff.agent`.

1. Self-host Switch 0.31.0, the version the live run used, with Docker Compose, following the [self-host guide](https://docs.switchagents.ai/switch-rooms/deploy/self-host). Set `SECRET_KEYS` (`<id>:<secret>` pairs, each secret at least 32 characters) and `AGENT_REGISTRATION_TOKEN`. Keep both out of git.
2. Register `alice-claude`, `bob-codex` and `bailiff` with `POST /agents`, using a registration key from your own account. The docs say agents registered with the bootstrap key belong to a separate account. The response returns each agent's API key once. Store keys in environment variables, never in the repo.
3. Keep the default addressing policy for Bob and the Bailiff. It admits the agent's owner and the owner's agents. Never set `anyone` for them. The only exception is the optional real-Alice demo, which registers `alice-claude` as Anyone (see Live run with a real Alice); that weakens the owner-only gate for `alice-claude`.
4. Start the Bailiff with `python -m bailiff.agent`. It reads `BAILIFF_BASE_URL`, `BAILIFF_AGENT_ID`, `BAILIFF_API_KEY`, `BAILIFF_CONNECTION_ID` (a UUID, reused on every reconnect), `ROOM_ID` and `RECEIPT_PATH`. Optional: `ALICE_HANDLE`, `BOB_HANDLE`, `STEP_TIMEOUT`.
5. In the room, open a case: `!open case <title>` or `@bailiff open case <title>`.

## Live run with a real Alice

Alice is a Claude Code agent that Switch Console runs on the Mac. With `--alice-agent`, the Bailiff names it when it creates the room, waits for its `room_join`, and allows 300 seconds per step. The flags are defined in [`bailiff/demo.py`](bailiff/demo.py).

Register `alice-claude` in Switch Console with these settings:

- Provider Claude Code, run location This computer, directory `sample-app/export-service`.
- Who can talk to your agent: Anyone. This is the verified demo setting and the one exception to step 3 above. Switch's owner-only gate for this agent is not re-tested here.
- Auto mode on, Bypass off.
- Instructions: run only the exact allow-listed argv the Bailiff sends. Reply with one `@pc-live-bailiff BAILIFF-RES {json}` message containing request_id, machine `"alice"`, kind, exit_code, stdout and stderr. Reply in strict JSON only.

Then run:

```
python -m bailiff.demo --live --alice-agent alice-claude --chat-user user
```

`--chat-user` makes the room visible in Switch Console's room Chat tab. Alice's messages show in Mattermost under the owner account `admin`, because no Mattermost bot exists for her. Bob's approvals read `APPROVAL: auto-approved (scripted agent, no human)`. In the recorded runs Alice's attestation read `UNVERIFIED` or `DECLINED`. The Bailiff does not validate the string, so a receipt line is not proof that a human approved ([`bailiff/agent.py:398-406`](bailiff/agent.py)).

---

## Privacy

Nothing personal or secret should reach the room that the LLM agents read. Masking runs on probe output, posted messages, the case-file document and `receipt.json`. Fingerprint comparison runs on raw values in memory only; they are never stored or posted.

The masking code is [`bailiff/redact.py`](bailiff/redact.py). It is regex plus checksum, deterministic, linear-time, idempotent, and it never raises. Each message is capped at 64 KB; anything beyond the cap becomes a `[truncated N chars]` marker.

- **Secrets** become `[redacted]`: key=value pairs with secret-named keys, tokens, `Bearer` values, AWS and GitHub keys, JWTs, URL credentials, auth headers, `--password x` flags, and JSON and Python-repr pairs.
- **Personal data** becomes a typed placeholder:

| Placeholder | Matches |
|---|---|
| `[redacted:email]` | email addresses |
| `[redacted:ip]` | IPv4 and IPv6 addresses |
| `[redacted:mac]` | MAC addresses |
| `[redacted:card]` | card numbers that pass the Luhn check |
| `[redacted:ssn]` | social security numbers |
| `[redacted:phone]` | phone numbers in E.164 form (leading `+`) only |
| `[redacted:id]` | long numeric IDs |
| `[redacted:user]` | usernames in Windows, macOS and Linux home paths, and `USER`, `LOGNAME`, `USERNAME` |
| `[redacted:host]` | hostnames in `uname -a` output, and `HOSTNAME`, `COMPUTERNAME` |

The receipt has an optional `privacy` block with placeholder counts and one masked example. Demo output reports the same counts.

**Limits of masking** (regex and checksum only):

- No name or street-address detection. Free-text names, non-Latin scripts and base64-embedded PII are not masked.
- Bare national phone numbers are not masked; only `+` E.164 is.
- `user@host:path` SSH remotes and dash-style hostnames such as `ip-10-0-1-5` are not masked.
- Mid-sentence `KEY=value tail words` keeps the tail. Whole-line masking applies to env-style lines in probe stdout.
- Not masked: PEM bodies on later lines, YAML block scalars, unquoted numeric JSON secrets, `docker login -p X`, and `mysql -pX`.
- A quoted value that contains an unescaped same quote can leave a fragment.
- Version-like dotted quads are masked as IPs, except `v1.2.3.4`, `pkg==1.2.3.4`, and `-rc`, `-alpha`, `-beta` or `+build` forms.
- `auth: 4 passed`-style prose is masked, because `auth` is a secret word.

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
| `privacy` | Optional: placeholder counts and one masked example (see Privacy) |

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
scripts/judge.py               one-command check (python scripts/judge.py)
scripts/check_judge_path.py    judge-path check (needs Docker)
tests/                         pytest suite for bailiff/
docs/PARITYCOURT.md            full design, flow, risks, judge path
justfile, pyproject.toml       commands and project metadata
```

---

## Quality

- **603 tests pass** with `python -m pytest -q` (`just test`). Branch coverage is 95%; the CI gate is 90 percent.
- **Property tests.** Hypothesis tests cover the redactor and the PII masking ([`tests/test_redact_properties.py`](tests/test_redact_properties.py), [`tests/test_pii_properties.py`](tests/test_pii_properties.py)).
- **Strict types and lint.** `mypy --strict` over `bailiff/` (`just typecheck`) and `ruff` over `bailiff`, `tests` and `scripts` (`just check`) are clean.
- **CI: 8 jobs, all green.** [`.github/workflows/ci.yml`](.github/workflows/ci.yml) covers lint, types and tests on Python 3.11 and 3.12 with the coverage gate; bandit, pip-audit and gitleaks; a Node job (Node 22 must pass, Node 18 must fail with `toSorted is not a function`); the Docker judge path; actionlint; and an aggregate `ci-ok` job. Dependabot and pre-commit are configured. The repo is private, so there is no badge yet.
<!-- CI badge: add after the repo is public -->
- **Planned:** mutation tests on the pure modules.

---

## Scaling and limits

- **Isolation.** Each case runs in its own Switch room (one room per case). Scale by adding rooms or running more Bailiff processes.
- **Cost.** One ablation per differing variable, so the cost per case is linear in the number of variables that differ.
- **Replay** is stateless and keyless: `receipt.json` re-runs in Docker with no Switch server and no keys.
- **No model call in the Bailiff**, so it adds no API cost and no rate limit.
- **Adding a machine** means one more Switch agent plus its fingerprint.
- **Limits:**
  - One-variable ablation misses bugs that need two variables changed together. Pairwise ablation would catch them, at quadratic cost.
  - The design compares two machines per case. For N machines, cluster by fingerprint and compare one representative per cluster. Not built.
  - Probes are a hand-maintained allow-list.
  - Owner approval caps throughput by design: every probe waits for its machine's owner.
  - Masking is regex and checksum, with the gaps listed under [Privacy](#privacy).
  - Concurrent cases in one Bailiff process have not been load-tested. The design is room-per-case.

## Honest limits

| Piece | Status |
|---|---|
| Receipt format, validation and `replay` | Code in `bailiff/receipt.py` and `bailiff/replay.py`; pytest coverage in `tests/` |
| Offline demo | Simulated: in-memory room, scripted agents, canned output |
| Judge path | Two Node containers: Alice runs Node 22; Bob's image has Node 22 and Node 18 stages ([`deploy/`](deploy/)). Not a Mac or an Ubuntu box. `python scripts/judge.py` with Docker: 8/8 checks; container check 5/5. |
| Switch-room mode | Live mode merged to main; ran against Switch 0.31.0 with scripted Bob, and scripted Alice in the [transcript](docs/evidence/transcript.txt). One verified live run (not in the repo transcript) had a real Claude Code Alice via `--alice-agent`. Real Claude Code Bob: in progress. |
| CI | 8 jobs, all green ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) |
| Owner-only approval | Verified by reading Switch code; live test `(to be verified)` |
| Case-only import on a real Mac | Replayed and recorded per the design doc; recording location `(to be verified)` |

- **Approval identity is the participant's name, not a signed identity.** An attestation records who said yes. It is not a cryptographic signature.
- **Probes are allow-listed.** Agents run only approved commands and never read `.env` files.
- **Scripted agents stand in for Claude Code** on the keyless path and for Bob in the live run. A real Claude Code Alice ran in one live run with `--alice-agent`. Real Claude Code Bob is in progress and not claimed done.
- **Alice appears as `admin` in Mattermost**, because no Mattermost bot exists for her.
- **The room is bound to Mattermost only with `--chat-user`.** Without it the room is `internal_only`.
- **A real Alice needs Auto mode on.** Observed in one live run (2026-11-07), not guaranteed: with Auto mode off, Alice's turn blocked. Switch's log said "No Mattermost bot for agent 'alice-claude', so its activity cannot be posted in channel", and posting `!interrupt @alice-claude` in the room made her respond again.
- **A real Alice's attestation is unsigned.** In the recorded runs it read `UNVERIFIED` or `DECLINED`. The Bailiff does not validate the string, so a receipt line is not proof that a human approved ([`bailiff/agent.py:398-406`](bailiff/agent.py)).
- **The judge path reproduces a Node-version bug**, not the case bug. The `toSorted` failure on Node 18 was reproduced on real Node 18.20.8 vs Node 22.23.4 on the author's machine (via npx). Inside the Docker containers the check matched 5/5.
- **The case-only import is the real-world analogue.** `SqlAuthGuard` vs `sqlAuthGuard` fails on a case-sensitive filesystem (ext4) and resolves on a case-insensitive one (APFS). The judge containers do not reproduce it. A privileged case-insensitive mount to reproduce it is untested.
- **Switch has no loop breaker or dual sign-off.** The turn cap is Bailiff code and is optional.
- **Privacy masking is regex and checksum only.** Its limits are listed under [Privacy](#privacy). Whether Switch's own guardrail masks real agent replies is unverified. Masking is not a substitute for a security review.
- **Custom Python agents cannot raise Switch approval cards (unverified).** The scripted agents' owner gate is a targeted message to the owner plus an addressed reply, enforced by Switch's addressing. Real approval cards would appear only for real Claude Code agents. A real Alice ran in one live run with Auto mode on (see the bullets above). Unverified end to end.
- **Masked suspects are not ablated.** A suspect whose value contains a placeholder gets verdict `unknown` (`not ablated: value masked`).
- **No ablation, no verdict.** If nothing could be ablated, the receipt is INCONCLUSIVE.
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
