---
name: ue-gate
description: Runs the twelve-item pre-commit gate (17.1) on the current change and reports each item with evidence. Use before a commit, and before saying a task is done.
---

Run the 17.1 gate on the current change. The gate is in the always-loaded `17-gate` rules; go through
all twelve items, in order.

For each item, answer one of:

- **pass** - with the evidence: the command and the lines it printed, the file:line that shows it, or
  the build or PIE result
- **n/a** - with the reason, such as "the project does not replicate"
- **fail** - with what is wrong and the fix

Two items need the person, not you: say what they must do.

- **Played in PIE** - you cannot play it; list what to try in PIE to exercise the change.
- **Read every line an assistant wrote** - name the files and the riskiest parts to read first.

Get the evidence by running checks, not by recalling them:

- `{{PYTHON}} {{STANDARDS}}/tooling/claude/scripts/ue_build.py` - the editor-closed build, when a header,
  delegate, constructor default or new class changed (15, item 1)
- `{{PYTHON}} {{STANDARDS}}/tooling/check-project.py . --files <changed files>`
- `{{PYTHON}} {{STANDARDS}}/tooling/claude/scripts/ue_validate.py` - when assets changed

End with one line: ready to commit, or the items still failing.
