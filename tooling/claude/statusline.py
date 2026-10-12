#!/usr/bin/env python3
"""Claude Code status line: model, context used, prompt-cache hits and the standard's version (27.6).

Runs outside the model, so it costs no tokens. Context fill is the number to watch: performance
drops as the window fills, and /clear between unrelated tasks is cheaper than any compaction.
It must never fail - a status line that errors shows nothing - so every field is optional.
"""

import json
import re
import sys
from pathlib import Path

STANDARDS = Path(__file__).resolve().parents[2]


def standard_version() -> str:
    try:
        match = re.search(r"\*\*Version (\d+\.\d+\.\d+)\*\*", (STANDARDS / "README.md").read_text(encoding="utf-8"))
        return match.group(1) if match else "?"
    except OSError:
        return "?"


def render(data: dict) -> str:
    parts = [(data.get("model") or {}).get("display_name") or "Claude"]
    used = (data.get("context_window") or {}).get("used_percentage")
    if used is not None:
        parts.append(f"ctx {float(used):.0f}%")
    cache = data.get("prompt_cache") or {}
    if cache.get("hit_ratio") is not None:
        parts.append(f"cache {float(cache['hit_ratio']) * 100:.0f}% {'warm' if cache.get('warm') else 'cold'}")
    parts.append(f"std {standard_version()}")
    return " | ".join(parts)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    try:
        print(render(data))
    except Exception:  # a status line must always print something
        print("Claude")
    return 0


if __name__ == "__main__":
    sys.exit(main())
