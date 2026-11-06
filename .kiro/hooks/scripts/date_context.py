#!/usr/bin/env python3
"""UserPromptSubmit hook: inject current date/time into agent context.

Models have a training cutoff and will otherwise assume a stale "today",
which poisons web searches and date-relative reasoning.
"""

import sys
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

now = datetime.now(timezone.utc)
iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
weekday = now.strftime("%A")

sys.stdout.write(
    f"Current date/time: {weekday}, {iso}. "
    "Use this for any date-relative reasoning. When searching the web for "
    "library or framework information, restrict results to the last 12-18 "
    "months relative to this date rather than assuming your training cutoff.\n"
)
sys.exit(0)
