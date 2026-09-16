# Changelog

**1.6 - 2026-09-16**

Tooling fixes. 1.5 shipped four enforcement files; none of them had ever been run against the
repository they enforce, and three were broken. Each fix below was verified by executing the tool,
not by reading it.

- **`.clang-format` produced mixed tabs and spaces**, against 3.10 and `.editorconfig`.
  `BasedOnStyle: LLVM` silently inherits `AlignAfterOpenBracket: Align` and
  `Cpp11BracedListStyle: true`, and both indent with spaces in a tab-indented file. Now
  `UseTab: ForContinuationAndIndentation`, `AlignAfterOpenBracket: DontAlign` and
  `Cpp11BracedListStyle: false`, with `AlignTrailingComments: Leave` so the aligned
  `private:   // Variables` block in 3.1 survives the formatter. Every option carries the reason.
- **The shipped validator did not match the shipped formatter.** It does now, and produces no diff,
  so it doubles as the config's test case.
- **3.10 gains one exception**: a braced initialiser list keeps its brace on the assignment line,
  because clang-format cannot break there and a rule the formatter reverses on the next save is not
  a rule.
- **`AssetNamingValidator` passed `BP_TEMP_ragdoll` and `WBP_TEMP_hudTest`.** The prefix list was
  searched first-match, so `BP_` matched ahead of `BP_TEMP_` and the PascalCase check landed on the
  `T` of `TEMP`. The list is now sorted longest-first, and failure messages still read the type's own
  prefix first.
- **`.clang-tidy` demanded PascalCase for a `const` member**, contradicting 4.1 - `ConstantMemberCase`
  was unset, so a const member fell back to the constant rule. Added.
- **4.1 now says a `constexpr` name is PascalCase wherever it is declared**, which is what separates
  it from a plain `const` local. The tooling already behaved this way; the rule did not say so.
- **`tooling/README.md` documents `--warnings-as-errors`** - clang-tidy exits 0 on violations, so the
  every-commit tier printed them and passed.
- **Added [`.github/workflows/standard.yml`](.github/workflows/standard.yml)**: `check-standard.py`
  and a `clang-format --dry-run --Werror` gate, with clang-format pinned to the version the config
  was verified against. 1.5 named the every-commit tier and then ran nothing.
- **Added `.gitattributes`**, ending the CRLF churn that made seven files report as modified with an
  empty diff.
- **22.2** now names `UE_ENABLE_DEBUG_DRAWING` as the macro to look for in `EngineDefines.h`;
  `ENABLE_DRAW_DEBUG` is its alias and is defined elsewhere.
- No rule changed meaning. 3.10 gained an exception and 4.1 gained a clarification, both recording
  what the tooling already did.

**1.5 - 2026-09-11**

Ten improvements from a review of the standard against itself. The theme is that the document was
easier to admire than to comply with.

- **The pre-commit checklist was 81 boxes and is now twelve** (17.1). Nobody ran 81, so nobody ran
  any. The twelve are the ones no tool catches and that are expensive to undo. The full list stays
  as a review reference (17.2) with **[tool]** markers on everything already enforced
  mechanically, and 17.4 is the backlog that keeps shrinking it.
- **Adoption is now tiered** (18.1-18.3). Tier 1 is the ten decisions that are expensive or
  impossible to reverse; Tier 2 is production discipline; Tier 3 is scale. A two-person prototype
  does Tier 1 and stops. 18.4 is new: how to retrofit onto an existing codebase.
- **New section 19, [Audio](rules/14-audio.md)** - intent from gameplay, mandatory concurrency caps,
  mixing in classes rather than call sites, one owner per loop.
- **New section 20, [Accessibility and localisation](rules/15-accessibility.md)** - subtitles, colour
  as a channel, remapping, text scale, photosensitivity, plurals, expansion budget, pseudo-loc.
  Both are cert items and both constrain layout before the first screen exists.
- **New section 21, [The online module](rules/16-online.md)** - 1.1 created the module and gave it no
  rules. Wire boundary, timeouts and backoff, never trusting a response, secrets, transport, offline
  behaviour, and a fake backend for tests.
- **New section 22, [Engine upgrades](rules/17-upgrades.md)** - the re-verification list naming every
  version-pinned claim in this standard and where to re-check it. Without it, the engine claims rot
  and the document becomes the folklore it was written to replace.
- **The two-line comment rule is a budget, not an absolute** (5.2). It was wrong in one direction: a
  threading invariant sometimes needs four lines, and "put it in a design doc" moves the explanation
  away from the reader who is confused. Going over now has to be earned in the comment's first line.
- **The camelCase deviation now has a real defence** ([why.md](why.md) 4.1), including the honest
  cost and the note that a project may override it wholesale. It is the most expensive rule here and
  had one sentence behind it.
- **Added "Changing this standard"** to the README - owner, proposal via `CONFLICT` block,
  re-verification on upgrade, deprecation, and how a project's trap becomes a general one.
- **Added [`tooling/check-standard.py`](tooling/check-standard.py)**, which fails CI on a broken
  section reference, a broken link, a non-ASCII character, a checklist item that cites no rule, a
  rule file missing from the README index, or a version that disagrees with the changelog.
- No rule changed meaning except 5.2.

**1.4 - 2026-09-11**

- **Rule change: a delegate member is now PascalCase `On*`** - `OnTransitionReady`, where 1.3 said
  `onTransitionReady` (4.7). This resolves a contradiction with the Blueprint Event Dispatcher rule
  (7.4), which is the same object seen from the Blueprint side and was already PascalCase. 4.1 now
  lists the two exceptions to camelCase members - the delegate member and the `BindWidget` member -
  in one place, and [why.md](why.md) records why the tie went this way. **Existing camelCase
  delegate members are renamed in a planned pass, not on sight** (5.4).
- Resolved a second contradiction: `HDRI_` is named as the single accepted alternative to `T_`, so
  it no longer contradicts "one prefix per type" (7.1).
- Added [`tooling/.clang-tidy`](tooling/.clang-tidy), which section 18 asked for and `tooling/` did
  not ship: `readability-identifier-naming` for the 4.1 case rules, with the engine-required forms
  (`OnRep_`, `_Implementation`, `_Validate`), delegate members and `BindWidget` members exempted,
  and what it cannot express listed in the file.
- `AssetNamingValidator` now enforces the 7.2 core-framework role prefixes (`BP_GM_`, `BP_PC_`,
  `BP_CH_` and the rest) by parent class, accepts `T_` or `HDRI_` for textures, and covers
  `TextureCube`, texture arrays, volume textures and cube render targets - previously skipped in
  silence. `BP_TEMP_` and `WBP_TEMP_` pass whatever the parent class, so the role check does not
  push prototypes out of the naming rules (8.2).
- No other rule changed meaning.

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
