---
name: ue-plan
description: Writes a self-contained implementation plan to .claude/plans/ - files, interfaces, state owners, rule sections, work packages and an end-to-end check. Use for any medium or large task, before code (14.1, 27.2).
argument-hint: "[task]"
---

Plan `$ARGUMENTS` before any code. Investigate first: read the code the task touches and the rule
sections that govern it. Raise every conflict as a `CONFLICT` block (14.1) now, not mid-build.

**Size the task first (27.2).** If the whole change fits in one sentence, say so and skip the plan.

Write the plan to `.claude/plans/<short-task-name>.md` with these sections. It must be self-contained:
the session that builds it starts fresh and has only this file.

1. **Goal** - what is true when this is done, in two or three lines.
2. **Out of scope** - what this change deliberately does not touch.
3. **Rules that apply** - the section numbers, and the one-line point of each that matters here.
4. **Decisions** - each fork settled, with the option chosen and why; every `CONFLICT` and its answer.
5. **Work packages** - for each: a name; the exact files it creates or changes; the interfaces it
   exposes (signatures, delegates, data assets); the owner of each piece of state (9.4); what it depends
   on; and its done-check - a command or a PIE step that passes or fails.
   Packages that touch no common file are **independent** and may be built in parallel (27.3).
6. **End-to-end check** - the build, validators, tests and PIE steps that prove the whole feature.
7. **Workflow** - medium (build it in this session) or large (`/clear`, then a fresh session runs
   `/ue-implement` on this file).

Show the plan and wait for approval before writing code.
