#!/usr/bin/env python3
"""Stop hook: emit the standing evidence + no-pause rules when the agent
finishes a turn. Exits 0 so the agent stops normally, but with the rules
in view.
"""

import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

RULES = """\
[standing-rules]

PART A — EVIDENCE:
Every quality gate you claim passed MUST have its verbatim command output
in the transcript. No test may be skipped, deleted, or loosened to make a
gate pass. For any piped command, report PIPESTATUS[0] (the real exit code
of the left-hand side), not the pipeline exit.

Switch repo Python gates: `just check`, `just typecheck`, `just test`.
Switch repo TypeScript gates: `pnpm -r run format:check`, `pnpm -r run lint`,
`pnpm -r run typecheck`, `pnpm -r run test`.
This repo: `python -m pytest tests/ -v`.

PART B — NO PAUSE:
Carry already-requested work as far as possible without stopping to ask
permission for it. Pause ONLY for: missing credentials; destructive actions;
git push; genuinely ambiguous requirements; or a review cap reached at
round 5.

REVIEWER:
If you are acting as a reviewer subagent, you MUST end with exactly one of
VERDICT: GREEN or VERDICT: RED, each backed by concrete evidence.
"""

sys.stdout.write(RULES)
sys.exit(0)
