#!/usr/bin/env python3
"""PreToolUse hook: refuses an Edit or Write inside the project's pinned copy of the standard (26.4).

A deviation is an override in the project's CLAUDE.md (00-core); a rule that is wrong is raised
against the standard (14.1). An edit to the copy is neither, and verify-standard.py would fail it
in CI anyway - this stops it before it is made. It covers Claude's file tools, not shell commands.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_common  # noqa: E402


def main() -> int:
    event = hook_common.read_event()
    path = hook_common.edited_path(event)
    if path is None:
        return 0
    standards = hook_common.STANDARDS
    root = hook_common.project_root(None, event)
    # The standard's own repository is where it is maintained, not a pinned copy
    if root is not None and root.resolve() == standards:
        return 0
    try:
        path.resolve().relative_to(standards)
    except ValueError:
        return 0
    hook_common.emit({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "This file is in the project's pinned copy of the team standard, which is never "
                                        "edited (26.4). Record a deviation as an override in CLAUDE.md, or raise a "
                                        "CONFLICT block against the standard (14.1).",
        }
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
