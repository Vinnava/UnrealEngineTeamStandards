---
name: ue-implement
description: Builds an approved plan from .claude/plans/ - packages to implementers, one build at a time, review, gate. Use in a fresh session for a large task.
argument-hint: "[plan file]"
disable-model-invocation: true
---

Build the approved plan in `$ARGUMENTS` (27.2, 27.3).

1. **Read the plan.** If it is not self-contained - a package with no files, no interfaces or no
   done-check - stop and say what is missing. Do not fill the gaps by guessing.
2. **Order the packages.** A package runs after the packages it depends on. Independent packages touch
   no common file.
3. **Implement.**
   - One package, or packages that share files: implement them yourself, in order.
   - Independent packages: delegate each to a **ue-implementer** agent with the plan path and the
     package name - **at most two at once**, and tell each whether it may build. Only one build of a
     target can run at a time.
4. **Build and validate**, once the packages are in:
   `{{PYTHON}} {{STANDARDS}}/tooling/claude/scripts/ue_build.py`
   `{{PYTHON}} {{STANDARDS}}/tooling/claude/scripts/ue_validate.py` - when assets changed
   Fix what fails. A failure you cannot explain from the summary goes to **ue-runner**.
5. **Review.** Delegate to **ue-reviewer** with the plan path and the checklists that apply. Fix every
   must-fix; judge each should-fix rather than chasing all of them.
6. **Gate.** Run `/ue-gate`, and report what the person still has to do - PIE above all.

Report progress after each step in one or two lines. Show evidence, not assertions.
