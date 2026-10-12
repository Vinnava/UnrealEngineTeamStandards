#!/usr/bin/env python3
"""Stop hook: keeps Claude working while a source file it edited this session has check-project errors.

The edit hook reports an error the moment it is written; this is the backstop for one that was
reported and left. It blocks once. If Claude is already continuing because of this hook and the
errors remain - a false positive, or a fix that needs you - it lets the turn end and tells you,
rather than looping (27.4).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_common  # noqa: E402


def main() -> int:
    event = hook_common.read_event()
    edited = hook_common.edits_this_session(event.get("session_id", ""))
    if not edited:
        return 0
    root = hook_common.project_root(edited[0], event)
    if root is None:
        return 0
    errors, _ = hook_common.check_files(root, edited)
    if not errors:
        return 0
    if event.get("stop_hook_active"):
        hook_common.emit({"systemMessage": f"check-project still reports {len(errors)} error(s) in files edited this "
                                           f"session - see the list above, or run check-project.py."})
        return 0
    hook_common.emit({
        "decision": "block",
        "reason": "Before finishing, fix the check-project errors in files you edited this session (17.1, 27.4). "
                  "If one is a false positive, say so instead of changing the code:\n"
                  + hook_common.format_findings(errors),
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
