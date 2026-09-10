# Changelog

**1.3 - 2026-09-10**

- Split the single standard file into [README.md](README.md) (index, precedence, pillars),
  thirteen rule files under [rules/](rules/), and [why.md](why.md) for the reasoning. Section numbers
  are unchanged; no rule was added, removed or changed in meaning.

**1.2 - 2026-09-10**

- Added material from the *Unreal Architect Track* and *Unreal Performance Track* (UE 5.8), checked
  against engine source where it went in as fact: compile-time gating and plugins (1.4, 1.5); the CDO,
  Details-panel design, pointer choice, Core Redirects, the actor lifecycle and tick (3.2-3.12); native
  gameplay tags (4.10); the Blueprint boundary tests (8.1, 8.3); the pattern catalogue, ownership map,
  subsystem design, input, save versioning, GAS and AI (9.10-9.15); gather-compute-apply and the
  animation thread rule (10.4, 10.6); replication, prediction and server rules (11.3-11.9); UI
  architecture (12.6); performance method, memory, hitches, instrumentation, content, server and
  regression gates (13.2-13.9); CI (14.5); collision traps (16); the reviewer's scan (17).
- Replaced "project overrides" with an explicit order for which document wins.
- Added `tooling/`: `.clang-format`, `.editorconfig` and an asset-naming validator.
- Re-checked the replication, push-model and Iris defaults in 5.8: unchanged from 5.7.

**1.1 - 2026-09-10**

- Checked engine claims against UE 5.7 source. Corrected three: `UE_LOGFMT` tokens match by position,
  not name (6.5); reflected struct fields are not zeroed outside engine allocation (4.6); an
  unregistered replicated property is auto-registered by default, and the missing-registration
  ensure is off by default (11.3).
- Resolved contradictions: comment and logging cleanup both apply to new and modified code only
  (5.4, 6.5); header-initialisation exceptions (3.2); one widget bind-name form (7.4); delegate member
  naming (4.7); underscores in function names (11.6); what replaces a switch (9.2).
- Replaced Hot Reload guidance with Live Coding and editor-closed builds (section 15, item 1).
- Added: ranked architecture pillars; the `CONFLICT` block (14.1); object lifetime and GC (3.8);
  assertions (3.9); formatting (3.10); project settings, interfaces, responsibility chains and input
  adapters (9.6-9.9); push model and Iris (11.8); player-facing text (12.5); cooking (13.3); source
  control (14.3); automated tests (14.4); missing asset prefixes (7.1); `GetNameSafe`, enum and
  `UE_CLOGFMT` logging rules (6.1); Tick approval, clamps and units (3.3, 3.7); collision and input
  traps (16); enforcement tooling and canonical examples (18).
- Added the version, placeholder and project-override rules at the top.

**1.0 - 2026-08-27** - First team standard.
