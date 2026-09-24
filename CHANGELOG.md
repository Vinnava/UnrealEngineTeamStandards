# Changelog

**2.0.1 - 2026-09-25**

- **1.1 says modules are created on demand.** Only `<Project>` is required; the online, editor and
  prototype modules are each created the day the project first needs one. The table read as a set
  every project starts with, so ZRK's `CLAUDE.md` recorded "no `ZRKOnline`" as though it were a gap.
  The project template lists only the modules a project has, and 18.1 no longer asks for the modules
  up front. The rules for what goes in each module are unchanged.

**2.0.0 - 2026-09-24**

**The first release meant for production.** 1.0 to 1.9 were the drafting of the standard; 2.0.0 fixes
the nine problems an engineering-lead review found with adopting it, and is the version the pilot runs
on ([PILOT.md](PILOT.md)). From here, releases follow semantic versioning (README, "Versioning").

**Owner: @Vinnava.**

Governance - the standard had no owner, no release discipline and no evidence from real use:

- **A named owner**, in the README, with [`.github/CODEOWNERS`](.github/CODEOWNERS) requesting their
  review on every pull request and a quarterly duty list. Until now "it has an owner" pointed at each
  project's README, so nobody was named.
- **Semantic versioning, with tags.** A project pins a release as a submodule, not a branch. A release
  whose changelog carries a "Rule change:" bullet must be a major version, and `check-standard.py`
  fails one that is not.
- **[PILOT.md](PILOT.md)**: one project, one milestone, measured by overrides written, gate items
  skipped, falling checker counts and traps added - and a retro that keeps, changes or deletes each
  section on that evidence.
- **[ONBOARDING.md](ONBOARDING.md)**: the fifteen minutes a new starter needs in week one, instead of
  the two-hour whole.

Tooling - the validators had been compiled once and never run; they now are, and three bugs fell out:

- **The validators were run in a headless editor for the first time**, against assets built to pass,
  fail and warn, using the `DataValidation` commandlet CI runs. The first run found three bugs no
  compile could show: an engine `ensure` that had fired on every validation run since **1.0**, from a
  path returning `NotValidated` after accepting an asset; every Blueprint reported twice, once as its
  generated class; and the unmapped-type path returning no verdict. All three are fixed, and the
  engine behaviours behind them are now traps in 16.9.
- **[`tooling/tests/validator-harness/`](tooling/tests/validator-harness/)** makes that run repeatable:
  one command compiles the validators with no PCH and no unity build, builds eleven test assets, and
  checks nineteen outcomes, including that a warning alone exits 0 and an error exits 1. It passes.
- **New `AssetContentValidator`** for the checkable content rules in section 23: a non-power-of-two
  texture that can never stream, a texture over the size budget, a heavy non-Nanite mesh with no LODs.
- **New `ProjectValidatorBase`.** Both validators read the content root from one `GlobalConfig`
  setting, verified in the engine to be honoured by both subclasses.
- **New [`tooling/check-project.py`](tooling/check-project.py)** turns six rows of the 17.4 backlog
  into CI checks on a project's source: `TAtomic`, `LogTemp`, unmarked synchronous loads, emoji and
  `U+FFFD`, the threading-candidate registry, and - as warnings - mutable statics and mixed logging.
  Its `--warn-only` mode is the retrofit path 18.4 asks for. 17.2 marks those items **[tool]**, and
  they have left 17.4.
- **Tests in CI - 31 of them.** Nineteen give every `check-project.py` check a case that must fire and
  one that must not; twelve change a copy of this repository one way at a time and assert
  `check-standard.py` reacts correctly - including the backspace-in-a-regex bug from 1.8, and a release
  that bumps minor while changing a rule's meaning.
- **An always-loaded token budget.** The set every project imports is 21,300 tokens against a
  22,000 budget, and `check-standard.py` fails a change that goes over it.

Rules:

- **New 1.6, Prototype code.** A `<Project>Prototype` module of type `DeveloperTool` - verified to be
  left out of Test and Shipping builds - held only to the safety rules, rewritten rather than moved
  when it graduates.
- **New section 23, [Content pipeline](rules/23-content-pipeline.md)**: textures, meshes and levels,
  limited on purpose to what is verified in engine source or checked by the validator. The art and
  design leads extend it during the pilot.
- **Rule change: an allowed synchronous load outside an editor module now carries a
  `// sync-load-ok: <reason>` marker** (10.3). It was allowed before without one; the marker is what
  lets `check-project.py` tell an exception from a hitch.
- **New traps.** 16.3: an actor's label does not exist in a cooked build (`GetActorLabel` is inside
  `#if WITH_EDITOR`). 16.8: a non-power-of-two texture never streams - still true in 5.7, although the
  refusal moved from the `NeverStream` flag to runtime, so checking the flag no longer finds it. New
  16.9, editor automation: the three engine behaviours the validator run exposed.
- **22.2 gains six rows** for the version-pinned claims above.
- **18** adds the submodule pinned to a tag, the prototype module, both validators and the project
  checker to the adoption tiers.

**1.9 - 2026-09-24**

A separate multithreading standard folded in. About 60 per cent of it was already here and was not
repeated. What was new is below, rewritten to this standard's conventions - its `MT-` rule IDs and its
own strength levels were dropped rather than imported, because a second numbering scheme is what 1.8
removed. Every engine claim was re-checked against UE 5.7 source on the way in, and two of them were
sharpened.

- **Found a bug in this standard: 10.1's example applied its result unconditionally.** It was correct
  only when nothing else could write the data while the task ran, and did not say so. 10.1 now says
  so, and points to the fix.
- **New 10.7, Stale results.** A generation counter on each owned data set, recorded at gather and
  compared at apply, so a late result cannot silently overwrite a newer player action. Every write path
  increments it - which 9.4's single write path makes enforceable.
- **New 10.8, Shared state.** A ladder: `TQueue` or `FPipe`, then `std::atomic`, then `UE::FMutex`.
  The imported doc said `FCriticalSection`; 5.7 has `UE::FMutex`, a one-byte non-recursive mutex, and
  `FCriticalSection` is a recursive platform mutex (`HAL/CriticalSection.h`). New code uses `UE::FMutex`.
  **Never `TAtomic`** - deprecated, but only in a comment (`Atomic.h`), so the compiler never warns.
- **New 10.9, Thread on evidence.** Four criteria, all required, before any system moves off the game
  thread; before and after captures in the pull request.
- **New 10.10, Threading candidates** (`[team-size]`). A registry in the project `CLAUDE.md`; only
  registered systems get callback-shaped APIs and the `Async` suffix, and over-applying them is a
  review defect.
- **10.4: a task continuation does not run on the game thread by default.** The imported doc said a
  continuation could return results to the game thread, which is true only when it is launched with
  `UE::Tasks::EExtendedTaskPriority::GameThreadNormalPri` (`Tasks/TaskPrivate.h`). A default
  continuation applies on a worker.
- **10.4: pure compute functions from the start, a gather snapshot holds IDs never pointers, and async
  logs name their phase** (`[Dispatch]`, `[Worker]`, `[Apply]`).
- **10.1: thread affinity is stated in the header comment** where it is not the default.
- **9.4: every write goes through the owner's API, and gameplay data lives in a `USTRUCT` the owner
  holds.**
- **3.7: no mutable `static` or global state.** Beyond the threading argument, mutable statics survive
  between PIE sessions today - the editor process outlives every Play.
- **4.3: a function that can complete later ends in `Async`**; a synchronous one never does.
- **22.2 gains three rows** for the version-pinned claims above, and **17.4 gains three greps**.
- **`tooling/check-standard.py` now fails when the project template's version disagrees with the
  README.** 1.8 shipped the template still saying 1.7.

**1.8 - 2026-09-17**

**Every rule file is now named for the sections it holds.** A number means one thing everywhere.

Until now the files carried their own sequence, unrelated to the sections inside them, and the two
collisions landed on the most cross-referenced sections in the standard: `16-online.md` held section
21 while "section 16" is the engine traps, and `17-upgrades.md` held section 22 while section 17 is
the commit checklist. 1.7 tried to fix this with a README sentence saying a bare number always means
a section. That was the wrong fix - the reader who needs the sentence has already misread the number.

| Was | Now | Holds |
|---|---|---|
| `01-layout.md` | `01-02-layout.md` | 1-2 |
| `02-cpp.md` | `03-cpp.md` | 3 |
| `03-cpp-naming.md` | `04-cpp-naming.md` | 4 |
| `04-comments-logging.md` | `05-06-comments-logging.md` | 5-6 |
| `05-content-blueprint.md` | `07-08-content-blueprint.md` | 7-8 |
| `06-architecture.md` | `09-architecture.md` | 9 |
| `07-async.md` | `10-async.md` | 10 |
| `08-networking.md` | `11-networking.md` | 11 |
| `09-ui.md` | `12-ui.md` | 12 |
| `10-performance.md` | `13-performance.md` | 13 |
| `11-practice.md` | `14-15-practice.md` | 14-15 |
| `12-engine-traps.md` | `16-engine-traps.md` | 16 |
| `13-checklists.md` | `17-gate.md`, `17-review.md`, `18-adopting.md` | 17.1; 17.2-17.4; 18 |
| `14-audio.md` | `19-audio.md` | 19 |
| `15-accessibility.md` | `20-accessibility.md` | 20 |
| `16-online.md` | `21-online.md` | 21 |
| `17-upgrades.md` | `22-upgrades.md` | 22 |

No section number changed, and no rule changed meaning. All 60 internal references were rewritten,
and the files were moved with `git mv`, so history follows them.

- **`check_file_numbering` in `tooling/check-standard.py` now fails the build** when a file's name and
  its sections disagree, so this cannot come back. Mutation-tested both ways: a heading moved into the
  wrong file, and a file renamed away from its sections.
- **The commit gate is its own file.** `17-gate.md` is 17.1, the twelve items, and is the only part of
  the checklists worth carrying on every request. `17-review.md` (17.2-17.4) is read when reviewing;
  `18-adopting.md` once when a project starts. The always-loaded set drops from **24.4k to 20.4k
  tokens** - 4.1k saved on every request, 17 per cent.
- **Added `.gitignore`** for `__pycache__`, which the checker creates.

**1.7 - 2026-09-17**

A review pass. The contradictions below were all real: a rule stating one thing while the example
beside it did another, which is the failure mode that teaches people to trust the example.

- **New [rules/00-core.md](rules/00-core.md), and it is now first in the import list.** The ranked
  pillars, the precedence order and the `<Project>` convention were in the README, which assistants
  are never given - so an assistant had every rule and nothing to resolve a conflict with, while
  being told to raise `CONFLICT` blocks against pillars it could not see. The README links to it now
  instead of holding it.
- **The override table moved to the project `CLAUDE.md`** (00-core, 8.1, 18.1). Precedence rule 2
  makes a written override beat this standard, and the assistant only sees the file it is given. An
  override living only in a project README is an unwritten deviation from where it sits.
- **Section 16 entries are numbered 16.1 to 16.8.** They were unnumbered, so a cross-reference could
  only point at the whole file while the README promised stable global numbers.
- **Four rules are marked `[team-size]`** - 11.7's weekly server build, 13.6's full instrumentation
  set, 13.9's regression gates, and 14.5's nightly and weekly tiers. Everything unmarked is
  unconditional, which is the property that makes "nothing here is aspirational" true.
- **`tooling/project-template/`** ships the three files section 18 asked for and `tooling/` did not
  have: a project `CLAUDE.md` with the imports and the override table, a `.gitattributes` with LFS
  **and `lockable`** (without which 14.3's `git lfs lock` does not work), and a pull request template.

Contradictions resolved:

- **3.6's example used `if (!currentStep)` while 3.4 requires `IsValid`** - the most-pasted snippet in
  the document taught the opposite of the rule. Now `IsValid`.
- **3.9 called `ensureMsgf` the default and then showed `ensure`.** The example uses `ensureMsgf`.
- **3.7 said debug draws are off in Shipping and Test.** True only outside the editor:
  `UE_ENABLE_DEBUG_DRAWING` is `(!(UE_BUILD_SHIPPING || UE_BUILD_TEST) || WITH_EDITOR)`, so an editor
  build keeps them. The `|| WITH_EDITOR` clause is the part worth knowing, and it is now stated.
- **The countdown had no way to reach the screen.** 3.7 said `GetTimerRemaining` for display; 12.6
  bans property bindings and `NativeTick`. 3.7 now names the display timer that pushes the value.
- **9.2's example was a hard reference inside a DataAsset**, against 13.3. It is `TSoftObjectPtr` now,
  with the reason.
- **10.1 taught `AsyncTask` where 10.4 says to reach for `UE::Tasks::Launch` first.** The example
  launches with `UE::Tasks::Launch` and keeps `AsyncTask(ENamedThreads::GameThread, ...)` for the
  return leg, which is the named-thread case that call is still for.
- **9.5 said "a subsystem timer"** where only a GameInstance subsystem works - a World subsystem's
  timers die with the world, which is the bug the section exists to prevent.
- **8.1 sent "per-actor gameplay logic" to Blueprint** while its own drift diagnostic calls a
  Blueprint branching on a game rule the smell. Now "per-actor composition and response".
- **`PHYS_` is recorded as a deliberate deviation from Epic's `PA_`** (7.1), the second in the
  standard after camelCase members. It was the only prefix differing from UE5 without saying so.

Tooling:

- **The validator no longer passes an unmapped asset type in silence.** An unknown class returned
  `NotValidated`, so every new engine type went unnamed forever; it now emits a warning naming the
  class, so the table grows instead of ageing.
- **`.editorconfig` gained `[*.ini]`** - Unreal rewrites config files constantly, and trailing-space
  trimming churned every one the editor touched.

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
- **New section 19, [Audio](rules/19-audio.md)** - intent from gameplay, mandatory concurrency caps,
  mixing in classes rather than call sites, one owner per loop.
- **New section 20, [Accessibility and localisation](rules/20-accessibility.md)** - subtitles, colour
  as a channel, remapping, text scale, photosensitivity, plurals, expansion budget, pseudo-loc.
  Both are cert items and both constrain layout before the first screen exists.
- **New section 21, [The online module](rules/21-online.md)** - 1.1 created the module and gave it no
  rules. Wire boundary, timeouts and backoff, never trusting a response, secrets, transport, offline
  behaviour, and a fake backend for tests.
- **New section 22, [Engine upgrades](rules/22-upgrades.md)** - the re-verification list naming every
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
