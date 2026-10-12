---
name: ue-upgrade-engine
description: Runs the engine upgrade procedure (22.3) and the re-verification list (22.2). Use only when the person starts an engine upgrade.
disable-model-invocation: true
---

An engine upgrade is starting. It happens on a branch, never inside a milestone (22.1). Follow the
procedure below in order and report after each step.

- Re-verify every 22.2 claim with the **ue-engine-source** agent, one claim per request, and keep its
  quotes. A claim that changed is fixed in the standard by its owner, not in the project's copy.
- The standard's harnesses are part of step 7: run them on the new engine
  (`{{STANDARDS}}/tooling/README.md`, "Proving the validators work" and "Proving the save versioning works").

{{INCLUDE rules/22-upgrades.md}}
