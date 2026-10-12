---
name: ue-save-version
description: Walks the save-format change procedure (24.2, 24.4) - decide whether a version bump is needed, append it, migrate, keep legacy data readable, load the fixtures. Use whenever anything a save file holds changes.
---

Something a save file holds is changing. Follow section 24 in order; it is included below.

1. **Decide whether it needs a version** with the 24.2 table and its test. Say which row applies.
2. If it does: **append one entry** above the marker, keep the old data readable, write one migration
   function and call it from `ApplyMigrations` in enum order (24.4).
3. **Check the never list** (24.5) against your change before you finish.
4. **Load every fixture** (24.6) and show the result.

{{INCLUDE rules/24-save-data.md}}
