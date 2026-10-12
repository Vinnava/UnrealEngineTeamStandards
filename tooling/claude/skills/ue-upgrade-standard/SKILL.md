---
name: ue-upgrade-standard
description: Upgrades the project's pinned copy of the team standard to a new release (26.4) and refreshes the Claude kit (27.7). Use only when the person asks to upgrade the standard.
argument-hint: "[new version]"
disable-model-invocation: true
---

Upgrade the pinned standard to `$ARGUMENTS`.

1. **Read the changelog first** - every release between the pinned version and the new one. List each
   `Rule change:` bullet and what in this project it affects. Stop and show the list before changing
   anything.
2. **Replace the whole `{{STANDARDS}}/` folder** with the new release (26.4) - never merge file by file.
   The person copies it in on their source-control system; do not edit files inside it.
3. **Verify the copy:** `{{PYTHON}} {{STANDARDS}}/tooling/verify-standard.py`
4. **Refresh the kit:** `{{PYTHON}} {{STANDARDS}}/tooling/claude/install.py` - it regenerates `.claude/`
   and removes files an older kit made. Pass `--replicates` if the project replicates.
5. **Update `CLAUDE.md`:** the `Standard version:` line, and any override a rule change made obsolete.
6. **Run the project's checks:** `check-project.py`, the build and the validators, and report what the
   new rules flag. New code meets them in full; existing code is fixed in planned passes (18.4).
