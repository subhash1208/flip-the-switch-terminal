#!/usr/bin/env python3
"""postToolUse hook for memory-updater: keep the knowledge graph readable and backed up.

Runs after every memory write. It reports malformed lines, refreshes a backup of the
graph while the graph is healthy, and restores the backup when a write left the graph
empty. Always exits 0 so a hook fault never blocks the agent.

`python validate_memory.py --self-test` exercises the backup logic in a temp dir.
"""

import json
import os
import sys
import tempfile


def scan(path: str) -> tuple[int, list[int]]:
    """Return (entity line count, malformed line numbers). Missing or unreadable counts as empty."""
    entities = 0
    bad: list[int] = []
    try:
        with open(path, encoding="utf-8") as f:
            for number, line in enumerate(f, 1):
                text = line.strip()
                if not text:
                    continue
                try:
                    obj = json.loads(text)
                except ValueError:
                    bad.append(number)
                    continue
                if isinstance(obj, dict) and obj.get("type") == "entity":
                    entities += 1
    except (OSError, ValueError):
        return 0, []
    return entities, bad


def _copy_atomic(src: str, dst: str) -> None:
    """Copy src over dst through a temp file, so a reader never sees a partial file."""
    folder = os.path.dirname(os.path.abspath(dst))
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".memory-tmp-")
    try:
        with os.fdopen(fd, "wb") as out, open(src, "rb") as inp:
            out.write(inp.read())
        os.replace(tmp, dst)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def sync_backup(graph: str, backup: str) -> str:
    """Refresh the backup from a healthy graph, or restore it over an empty one.

    Returns the warning for the agent when a restore happened, else "".
    """
    entities, bad = scan(graph)
    backup_entities, _ = scan(backup)
    if entities == 0:
        if backup_entities == 0:
            return ""
        _copy_atomic(backup, graph)
        return (
            "MEMORY GRAPH WAS EMPTY AFTER A WRITE - restored from backup "
            f"({backup_entities} entities). Re-verify your last write."
        )
    if not bad and entities * 2 >= backup_entities:
        _copy_atomic(graph, backup)
    return ""


def self_test() -> int:
    entity = (
        '{"type": "entity", "name": "%s", "entityType": "Repo", "observations": []}\n'
    )

    def lines(count: int) -> str:
        return "".join(entity % f"e{i}" for i in range(count))

    def write(path: str, text: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    results: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as tmp:
        graph = os.path.join(tmp, "graph", "switch-hackathon-knowledge-graph.jsonl")
        backup = os.path.join(tmp, "backup", "switch-hackathon-knowledge-graph.jsonl")

        write(backup, lines(2))
        write(graph, lines(3))
        msg = sync_backup(graph, backup)
        results.append(
            (
                "(a) healthy graph refreshes a stale backup",
                scan(backup)[0] == 3 and msg == "",
            )
        )

        write(graph, "")
        msg = sync_backup(graph, backup)
        results.append(
            (
                "(b) empty graph restores the backup",
                scan(graph)[0] == 3
                and msg
                == "MEMORY GRAPH WAS EMPTY AFTER A WRITE - restored from backup "
                "(3 entities). Re-verify your last write.",
            )
        )

        os.remove(backup)
        write(graph, "")
        msg = sync_backup(graph, backup)
        results.append(
            (
                "(c) empty graph with no backup is left alone",
                os.path.getsize(graph) == 0
                and not os.path.exists(backup)
                and msg == "",
            )
        )

        write(backup, lines(3))
        write(graph, lines(1))
        msg = sync_backup(graph, backup)
        results.append(
            (
                "(d) shrunk graph below 50% does not overwrite backup",
                scan(backup)[0] == 3 and msg == "",
            )
        )

        os.remove(graph)
        msg = sync_backup(graph, backup)
        results.append(
            (
                "(e) missing graph counts as empty and is restored",
                scan(graph)[0] == 3 and "restored from backup (3 entities)" in msg,
            )
        )

    failures = 0
    for name, ok in results:
        failures += 0 if ok else 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    total = len(results)
    print(f"\n{total - failures}/{total} self-test cases passed.")
    return 1 if failures else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (OSError, ValueError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    cwd = payload.get("cwd")
    base = (
        cwd
        if isinstance(cwd, str) and cwd
        else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    )
    graph = os.path.join(
        base,
        os.environ.get("MEMORY_FILE_PATH") or "switch-hackathon-knowledge-graph.jsonl",
    )
    backup = os.path.join(
        os.path.expanduser("~"), ".copilot", "memory-backup", os.path.basename(graph)
    )

    messages: list[str] = []
    try:
        warning = sync_backup(graph, backup)
    except OSError as exc:
        print(
            f"[memory-backup] could not refresh or restore the backup: {exc}",
            file=sys.stderr,
        )
        warning = ""
    if warning:
        messages.append(warning)
    _, bad = scan(graph)
    if bad:
        messages.append(
            f"[memory-check] {len(bad)} malformed line(s) in {graph}: "
            f"lines {bad[:10]}. Repair before the next write."
        )
    if messages:
        print(json.dumps({"additionalContext": " ".join(messages)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
