#!/usr/bin/env python3
"""postToolUse hook for memory-updater: report malformed lines in the knowledge graph.

Read-only. It never rewrites the file, so a bad parse cannot damage the graph.
Always exits 0 so a hook fault never blocks the agent.
"""

import json
import os
import sys

PATH = os.environ.get("MEMORY_FILE_PATH", "switch-hackathon-knowledge-graph.jsonl")


def main() -> int:
    if not os.path.exists(PATH):
        return 0
    bad: list[int] = []
    try:
        with open(PATH, encoding="utf-8") as f:
            for number, line in enumerate(f, 1):
                text = line.strip()
                if not text:
                    continue
                try:
                    json.loads(text)
                except ValueError:
                    bad.append(number)
    except OSError:
        return 0
    if bad:
        print(json.dumps({
            "additionalContext": f"[memory-check] {len(bad)} malformed line(s) in {PATH}: "
                                 f"lines {bad[:10]}. Repair before the next write.",
        }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
