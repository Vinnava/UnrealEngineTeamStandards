#!/usr/bin/env python3
"""PostToolUse hook: runs check-project on the source file Claude just edited (27.4).

Silent when the file is clean, so a clean edit costs no tokens. An error comes back to Claude as a
blocking reason beside the tool result, the moment it is written; a warning - the checks with known
false positives - comes back as context only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_common  # noqa: E402


def main() -> int:
    event = hook_common.read_event()
    path = hook_common.edited_path(event)
    if path is None or path.suffix not in hook_common.SOURCE_SUFFIXES:
        return 0
    root = hook_common.project_root(path, event)
    if root is None or not (root / "Source").is_dir():
        return 0

    hook_common.remember_edit(event.get("session_id", ""), path)
    errors, warnings = hook_common.check_files(root, [path])
    if errors:
        hook_common.emit({
            "decision": "block",
            "reason": "check-project found errors in the file you just edited - fix them now (27.4):\n"
                      + hook_common.format_findings(errors),
        })
    elif warnings:
        hook_common.emit({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "check-project warnings in the file you just edited - these checks have known "
                                     "false positives, so judge each one:\n" + hook_common.format_findings(warnings),
            }
        })
    return 0


if __name__ == "__main__":
    sys.exit(main())
