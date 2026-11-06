# Cancel a Pending Message — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let people cancel a message queued for an agent before the agent starts on it, via `!cancel @agent <turn-id>`, with the turn-id shown on every queued activity card.

**Architecture:** A new `turn.cancel` command type flows from chat (`!cancel`) through the Python bridge to the TypeScript session host, which removes the turn from its in-memory queue and publishes a `turn.upsert` with a new `'cancelled'` terminal status. The activity card for queued turns is extended to display a short turn-id and a ready-to-use cancel command. No provider interaction — the provider never sees a cancelled turn.

**Tech Stack:** TypeScript (session host, session-v1 contract), Python (core bridge, renderers, contract mirror)

**Spec:** https://github.com/sandbox-quantum/switch/issues/800
Maintainer-approved UX: `!cancel @agent <turn-id>`, turn-id on queued activity card, deleting a queued message to cancel it is out of scope for this PR.

## Global Constraints

- The Switch repo is at `D:\Projects\switch`. All file paths below are relative to that root.
- TypeScript contract and Python contract must stay in sync — same command types, same status values.
- Follow existing patterns exactly: new command mirrors `turn.interrupt`, new chat command mirrors `!interrupt`.
- Exit codes unchanged — the issue spec requires this.
- No new dependencies.
- PR must include unit tests and a short demo video.

## Review Focus

1. **Race: cancel arrives as `runNext()` shifts the turn** — if the turn just became `activeTurn`, the cancel must reject with "already running", not silently fail or crash. The host's `accept()` must check both the queue and `activeTurn`.
2. **Turn-id prefix collision** — two queued turns whose IDs share the same 8-char prefix. The cancel must reject ambiguous matches rather than cancelling the wrong turn.
3. **Cancel a turn-id that doesn't exist** — typo, already completed, or belongs to a different agent. Must return a clear error, not throw.
4. **Platform card size limits on Slack** — adding the cancel command text to every queued card. Slack blocks have a 3000-char text limit; the cancel hint must fit.
5. **Session recovery** — on host restart, queued turns are already marked `'interrupted'`. Cancelled turns must not be re-interrupted (they're already terminal).

---

### Task 1: Add `turn.cancel` command and `'cancelled'` status to the session-v1 contract

**Files:**
- Modify: `console/packages/shared/src/session-v1/contract.ts:97-131`
- Modify: `core/switch_core/sessions/contract.py:198-300`

**Interfaces:**
- Consumes: nothing (this is the foundation)
- Produces:
  - TypeScript: `{ type: 'turn.cancel'; turnId: Id }` in `CommandBody` union, `'cancelled'` in `TurnUpsert.status`
  - Python: `TurnCancel` model class, `'cancelled'` in `TurnUpsert.status` literal, `'cancelled'` in `TURN_ENDED` frozenset, `TurnCancel` in `CommandBody` union

- [ ] **Step 1: Add `'cancelled'` to the TypeScript `TurnUpsert.status` union**

In `console/packages/shared/src/session-v1/contract.ts` line ~100, change:
```typescript
status: 'queued' | 'running' | 'completed' | 'interrupted' | 'error';
```
to:
```typescript
status: 'queued' | 'running' | 'completed' | 'interrupted' | 'cancelled' | 'error';
```

- [ ] **Step 2: Add `turn.cancel` to the TypeScript `CommandBody` union**

In `contract.ts` line ~131, after `| { type: 'turn.interrupt'; turnId: Id }`, add:
```typescript
| { type: 'turn.cancel'; turnId: Id }
```

- [ ] **Step 3: Add `TurnCancel` model to the Python contract**

In `core/switch_core/sessions/contract.py`, after the `TurnInterrupt` class (line ~282), add:
```python
class TurnCancel(_Model):
    type: Literal["turn.cancel"]
    turn_id: Id
```

- [ ] **Step 4: Add `'cancelled'` to the Python `TurnUpsert.status` literal**

In `contract.py` line ~201, change:
```python
status: Literal["queued", "running", "completed", "interrupted", "error"]
```
to:
```python
status: Literal["queued", "running", "completed", "interrupted", "cancelled", "error"]
```

- [ ] **Step 5: Add `'cancelled'` to `TURN_ENDED` frozenset**

In `contract.py` line ~205, change:
```python
TURN_ENDED = frozenset({"completed", "interrupted", "error"})
```
to:
```python
TURN_ENDED = frozenset({"completed", "interrupted", "cancelled", "error"})
```

- [ ] **Step 6: Add `TurnCancel` to the Python `CommandBody` union**

In `contract.py` line ~291, add `TurnCancel` to the `Annotated` union:
```python
CommandBody = Annotated[
    MessageSend
    | RequestAnswer
    | TurnInterrupt
    | TurnCancel
    | SessionStop
    | SessionReset
    | SessionCompact
    | SessionModelSet,
    Field(discriminator="type"),
]
```

- [ ] **Step 7: Verify both contracts compile**

Run:
```bash
cd console && npx tsc --noEmit
cd ../core && python -c "from switch_core.sessions.contract import TurnCancel, TURN_ENDED; print('cancelled' in TURN_ENDED)"
```
Expected: no errors, `True`

- [ ] **Step 8: Commit**

```bash
git add console/packages/shared/src/session-v1/contract.ts core/switch_core/sessions/contract.py
git commit -m "feat(contract): add turn.cancel command and cancelled status"
```

---

### Task 2: Handle `turn.cancel` in the session host

**Files:**
- Modify: `console/packages/agent-providers/src/host/session-host.ts:839-861`
- Test: `console/packages/agent-providers/src/host/__tests__/session-host-cancel.test.ts` (create)

**Interfaces:**
- Consumes: `{ type: 'turn.cancel'; turnId: Id }` from Task 1
- Produces: `accept()` handles `turn.cancel` — removes turn from `this.queue`, publishes `turn.upsert` with `status: 'cancelled'`

- [ ] **Step 1: Write failing tests for `turn.cancel` in the session host**

Create `console/packages/agent-providers/src/host/__tests__/session-host-cancel.test.ts`:

```typescript
describe('turn.cancel', () => {
  test('cancels a queued turn and publishes cancelled status', async () => {
    // Queue two messages, cancel the second (still queued)
    // Assert: turn.upsert with status 'cancelled' published for the cancelled turn
    // Assert: the cancelled turn is removed from the queue
    // Assert: the first turn still runs normally
  });

  test('rejects cancel of the currently running turn', async () => {
    // Queue one message, let it start running (activeTurn set)
    // Send turn.cancel with that turnId
    // Assert: error thrown or rejected with "already running, use !interrupt"
  });

  test('rejects cancel of unknown turn-id', async () => {
    // Send turn.cancel with a turnId that is not queued
    // Assert: error thrown or rejected with "turn not found in queue"
  });

  test('cancelled turn is never dispatched to the provider', async () => {
    // Queue two messages, cancel the first before runNext picks it up
    // Assert: adapter.sendTurn called only for the second message
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd console && npx jest --testPathPattern session-host-cancel -v`
Expected: FAIL — `turn.cancel` not handled in accept()

- [ ] **Step 3: Implement `turn.cancel` handler in `accept()`**

In `session-host.ts`, in the `accept()` method, after the `turn.interrupt` branch (line ~842) and before the `session.stop` branch, add:

```typescript
} else if (body.type === 'turn.cancel') {
  const idx = this.queue.findIndex(q => q.commandId === body.turnId);
  if (body.turnId === this.activeTurn) {
    throw new Error('Turn is already running. Use !interrupt instead.');
  }
  if (idx === -1) {
    throw new Error('Turn not found in queue.');
  }
  const [removed] = this.queue.splice(idx, 1);
  await this.inbox.append({ type: 'dispatched', commandId: command.commandId });
  this.dispatched.add(command.commandId);
  await this.publish({
    type: 'turn.upsert',
    turnId: removed.commandId,
    commandId: removed.commandId,
    status: 'cancelled',
  });
}
```

Check `activeTurn` first (the race from Review Focus #1), then find in queue, splice out, publish cancelled.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd console && npx jest --testPathPattern session-host-cancel -v`
Expected: PASS

- [ ] **Step 5: Run the full session-host test suite**

Run: `cd console && npx jest --testPathPattern session-host -v`
Expected: all existing tests still pass

- [ ] **Step 6: Commit**

```bash
git add console/packages/agent-providers/src/host/session-host.ts console/packages/agent-providers/src/host/__tests__/session-host-cancel.test.ts
git commit -m "feat(host): handle turn.cancel — remove queued turn and publish cancelled status"
```

---

### Task 3: Add `!cancel` chat command in the Python bridge

**Files:**
- Modify: `core/switch_core/bridges/agent/commands.py:250-254,1874-1886`
- Test: `core/tests/bridges/agent/test_cancel_command.py` (create)

**Interfaces:**
- Consumes: `turn.cancel` command type from Task 1
- Produces: `!cancel @agent <turn-id>` chat command, parsed and relayed to session host

- [ ] **Step 1: Write failing tests for the `!cancel` command**

Create `core/tests/bridges/agent/test_cancel_command.py`:

```python
class TestCancelCommand:
    async def test_cancel_dispatches_turn_cancel_with_turn_id(self):
        # !cancel @agent abc12345 → dispatches turn.cancel with resolved full turnId
        pass

    async def test_cancel_requires_target_agent(self):
        # !cancel abc12345 (no agent) → error: target required
        pass

    async def test_cancel_requires_turn_id_argument(self):
        # !cancel @agent (no turn-id) → error: turn-id required
        pass

    async def test_cancel_rejects_when_no_live_session(self):
        # !cancel @agent abc12345 when agent has no session → error message
        pass

    async def test_cancel_rejects_ambiguous_turn_id_prefix(self):
        # Two queued turns with IDs sharing the same 8-char prefix → error: ambiguous
        pass
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd core && python -m pytest tests/bridges/agent/test_cancel_command.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `_cmd_cancel` and `_decide_cancel` in `commands.py`**

Unlike `!interrupt` which uses `_CONTROL_BODIES` with `turnId: CURRENT`, `!cancel` needs the turn-id from the command argument. Don't use `_CONTROL_BODIES` — write a dedicated handler:

```python
async def _cmd_cancel(
    client: AgentRecipient, room: RoomRef, event: CommandEvent, _is_direct: bool
) -> None:
    turn_id_prefix = _get_arg(event, "turn-id")
    if not turn_id_prefix:
        await _reply_error(client, room, event, "Usage: `!cancel @agent <turn-id>`")
        return
    body = {"type": "turn.cancel", "turnId": turn_id_prefix}
    frame = room_control_frame(body, event)
    await _dispatch_frame(client, room, event, frame, _CANCEL_TEXTS)


async def _decide_cancel(
    client: AgentRecipient, room: RoomRef, event: CommandEvent
) -> ControlDecision:
    turn_id_prefix = _get_arg(event, "turn-id")
    if not turn_id_prefix:
        return ControlDecision(error="turn-id argument required")
    body = {"type": "turn.cancel", "turnId": turn_id_prefix}
    return await _decide_control_command(client, room, event, "cancel", _CANCEL_TEXTS, body_override=body)
```

Add `_CANCEL_TEXTS` message strings (follow `_INTERRUPT` pattern).

- [ ] **Step 4: Register `!cancel` in the `COMMANDS` list**

After the `!interrupt` entry (line ~1886), add:

```python
Command(
    "cancel",
    "Cancel a queued message before the agent starts on it. "
    "Usage: `!cancel @agent <turn-id>`. "
    "The turn-id is shown on the queued activity card.",
    _cmd_cancel,
    decide=_decide_cancel,
    args_spec=(
        CommandArg("target", "Agent name, alias, or role", required=True),
        CommandArg("turn-id", "Turn ID shown on the queued card", required=True),
    ),
    addressed=_addressed_by_required_first_mention,
    admin_check=_check_control_target,
),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd core && python -m pytest tests/bridges/agent/test_cancel_command.py -v`
Expected: PASS

- [ ] **Step 6: Run the full commands test suite**

Run: `cd core && python -m pytest tests/bridges/agent/ -v`
Expected: all existing tests still pass

- [ ] **Step 7: Commit**

```bash
git add core/switch_core/bridges/agent/commands.py core/tests/bridges/agent/test_cancel_command.py
git commit -m "feat(commands): add !cancel chat command for queued turns"
```

---

### Task 4: Update renderers — show turn-id on queued cards and render cancelled status

**Files:**
- Modify: `core/switch_core/bridges/collaboration/session/renderers/__init__.py:28-34`
- Modify: `core/switch_core/bridges/collaboration/session/renderers/slack.py:1358-1413`
- Modify: `core/switch_core/bridges/collaboration/session/renderers/neutral.py` (turn_summary, turn_status)
- Test: `core/tests/bridges/collaboration/session/renderers/test_cancel_rendering.py` (create)

**Interfaces:**
- Consumes: `'cancelled'` status from Task 1, `TURN_ENDED` now includes `'cancelled'`
- Produces: queued cards show turn-id + ready-to-use `!cancel` command hint, cancelled cards show "Turn cancelled."

- [ ] **Step 1: Write failing tests for renderer changes**

Create `core/tests/bridges/collaboration/session/renderers/test_cancel_rendering.py`:

```python
class TestCancelRendering:
    def test_turn_state_returns_cancelled_text(self):
        # turn with status 'cancelled' → "Turn cancelled."
        pass

    def test_queued_turn_state_includes_short_turn_id(self):
        # turn with status 'queued' and turn_id 'abc12345-...' → text contains 'abc12345'
        pass

    def test_cancelled_is_terminal(self):
        # 'cancelled' in TURN_ENDED → True
        pass

    def test_interrupt_block_returns_none_for_cancelled(self):
        # _interrupt_block with cancelled turn → None (no stop button)
        pass
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd core && python -m pytest tests/bridges/collaboration/session/renderers/test_cancel_rendering.py -v`
Expected: FAIL

- [ ] **Step 3: Add `'cancelled'` to `TURN_STATE` dict**

In `renderers/__init__.py` line ~34, add:
```python
"cancelled": "Turn cancelled.",
```

- [ ] **Step 4: Show short turn-id and cancel hint on queued cards**

In `renderers/__init__.py`, modify the `turn_state()` function: when `turn.status == "queued"`, prepend the short turn-id (first 8 chars of `turn.turn_id`) to the status text:

```python
if turn.status == "queued":
    short_id = turn.turn_id[:8]
    return f"Queued ({short_id}). Cancel: `!cancel @agent {short_id}`"
```

- [ ] **Step 5: Update neutral renderer**

In `renderers/neutral.py`, update `turn_status` and `turn_summary` to handle `'cancelled'` — follow the existing pattern for `'interrupted'`.

- [ ] **Step 6: Ensure `_interrupt_block` handles cancelled turns**

In `slack.py` line ~1362, `_interrupt_block` already returns `None` when `turn.status in TURN_ENDED`. Since Task 1 added `'cancelled'` to `TURN_ENDED`, the stop button will automatically disappear for cancelled turns. Verify this — no code change expected.

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd core && python -m pytest tests/bridges/collaboration/session/renderers/test_cancel_rendering.py -v`
Expected: PASS

- [ ] **Step 8: Run the full renderer test suite**

Run: `cd core && python -m pytest tests/bridges/collaboration/session/renderers/ -v`
Expected: all existing tests still pass

- [ ] **Step 9: Commit**

```bash
git add core/switch_core/bridges/collaboration/session/renderers/__init__.py core/switch_core/bridges/collaboration/session/renderers/slack.py core/switch_core/bridges/collaboration/session/renderers/neutral.py core/tests/bridges/collaboration/session/renderers/test_cancel_rendering.py
git commit -m "feat(renderers): show turn-id on queued cards, render cancelled status"
```

---

### Task 5: Integration verification and demo

**Files:**
- No new files — this is end-to-end verification

**Interfaces:**
- Consumes: all of Tasks 1–4

- [ ] **Step 1: Run the full TypeScript build**

Run: `cd console && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 2: Run the full TypeScript test suite**

Run: `cd console && npx jest --verbose`
Expected: all tests pass, including the new session-host-cancel tests

- [ ] **Step 3: Run the full Python test suite**

Run: `cd core && python -m pytest -v`
Expected: all tests pass, including the new cancel command and renderer tests

- [ ] **Step 4: Manual smoke test**

1. Start Switch Console with an agent in a room (auto-approve OFF)
2. Send two messages to the agent back-to-back (first starts running, second queues)
3. Verify the queued card shows the short turn-id and `!cancel` hint
4. Run `!cancel @agent <turn-id>` with the displayed turn-id
5. Verify: the queued card updates to "Turn cancelled.", the agent never sees the cancelled message, the first turn completes normally

- [ ] **Step 5: Record a short demo video**

Capture the smoke test showing: the queued card with turn-id, the `!cancel` command, the card updating to cancelled, and the agent continuing with the first turn unaffected.

- [ ] **Step 6: Open the PR**

PR title: `feat: cancel a pending message before the agent picks it up`
PR body: link `Closes #800`, describe the 4-part change (contract, host, command, renderers), include the demo video, and list the test summary.
