#!/usr/bin/env python3
"""Gentle-mode hook: inject the rules once per session, not on every prompt.

UserPromptSubmit: if gentle mode is on and this session has not had the rules yet,
print gentle.md plus the personal preferences and mark the session.
SessionStart (compact, clear, resume): clear the session's mark, so the rules come
back on the next prompt after the context was rebuilt.
"""
import json
import sys
import time
from pathlib import Path

HOME = Path.home()
FLAG = HOME / ".claude" / ".tldr-gentle"
SEEN = HOME / ".claude" / ".tldr-gentle-seen"
GENTLE = Path(__file__).resolve().parent.parent / "gentle.md"
PREFS = (
    HOME / ".claude" / "memory" / "shared" / "preferences" / "writing.md"
    if (HOME / ".claude" / "memory" / "AGENTS.md").exists()
    else HOME / ".claude" / "tldr" / "preferences.md"
)
MAX_AGE = 14 * 86400


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = {}
    session = "".join(c for c in str(event.get("session_id", "")) if c.isalnum() or c in "-_")
    mark = SEEN / session if session else None

    if event.get("hook_event_name") == "SessionStart":
        if mark:
            mark.unlink(missing_ok=True)
        return

    if not FLAG.exists() or (mark and mark.exists()):
        return

    for path in (GENTLE, PREFS):
        if path.exists():
            sys.stdout.write(path.read_text())
            sys.stdout.write("\n")

    if mark:
        SEEN.mkdir(parents=True, exist_ok=True)
        mark.touch()
        now = time.time()
        for old in SEEN.iterdir():
            if now - old.stat().st_mtime > MAX_AGE:
                old.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
