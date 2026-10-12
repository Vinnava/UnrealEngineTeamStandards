#!/usr/bin/env python3
"""Prints the lines of an Unreal log that matter, de-duplicated (27.4).

    python standards/tooling/claude/scripts/ue_log.py [--file PATH] [--level warning] [--category LogGameQuest]

Reads the newest log in Saved/Logs unless --file names one. Repeated lines are folded with a count,
so a warning logged every frame costs one line, not thousands. A crash prints the critical-error
block, which holds the callstack.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ue_common  # noqa: E402

# Category: Verbosity: message - verbosity is absent for plain Log lines
LINE = re.compile(r"^(?P<category>[A-Za-z]\w*): (?:(?P<verbosity>Fatal|Error|Warning|Display|Log|Verbose|VeryVerbose): )?(?P<text>.*)$")
LEVELS = {"error": {"Fatal", "Error"}, "warning": {"Fatal", "Error", "Warning"},
          "all": {"Fatal", "Error", "Warning", "Display", "Log", "Verbose", "VeryVerbose"}}
CRASH = re.compile(r"Critical error|Fatal error!|=== Critical error: ===|Unhandled Exception")


def filter_lines(lines: list[str], level: str, category: str | None, pattern: str | None) -> list[str]:
    wanted = LEVELS[level]
    regex = re.compile(pattern) if pattern else None
    kept = []
    for raw in lines:
        line = ue_common.strip_log_prefix(raw)
        match = LINE.match(line)
        if not match:
            continue
        verbosity = match.group("verbosity") or "Log"
        if verbosity not in wanted:
            continue
        if category and match.group("category") != category:
            continue
        if regex and not regex.search(line):
            continue
        kept.append(line)
    return kept


def crash_block(lines: list[str], size: int = 30) -> list[str]:
    for index, raw in enumerate(lines):
        if CRASH.search(raw):
            return [ue_common.strip_log_prefix(line) for line in lines[index:index + size]]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the lines of an Unreal log that matter.")
    parser.add_argument("--file", type=Path, help="the log to read; the newest in Saved/Logs by default")
    parser.add_argument("--project", type=Path)
    parser.add_argument("--level", choices=sorted(LEVELS), default="warning")
    parser.add_argument("--category", help="only this log category, such as LogGameQuest")
    parser.add_argument("--grep", help="only lines matching this regular expression")
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args()

    log = args.file
    if log is None:
        project = ue_common.find_project(args.project)
        logs = sorted((project / "Saved/Logs").glob("*.log"), key=lambda p: p.stat().st_mtime) if project else []
        if not logs:
            print("No log found - pass --file.")
            return 2
        log = logs[-1]
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()

    crash = crash_block(lines)
    if crash:
        print("CRASH - critical error block:")
        for line in crash:
            print(f"  {line}")
    shown, hidden = ue_common.compact(filter_lines(lines, args.level, args.category, args.grep), args.limit)
    print(f"{log.name}: {len(lines)} lines, {len(shown) + hidden} distinct at level {args.level}"
          + (f" in {args.category}" if args.category else ""))
    for line in shown:
        print(line)
    if hidden:
        print(f"... {hidden} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
