# <Project> - rules for Claude

<!--
Copy this to the project root as CLAUDE.md and fill in every <Project>. It is the file Claude reads in
every session, so anything it must obey has to be reachable from here - a rule that lives only in the
project README is a rule Claude never sees. Keep it under 200 lines (27.1).

Block comments like this one are stripped before Claude reads the file, so they cost no tokens.
-->

## The standard

@standards/rules/00-core.md
@standards/rules/14-15-practice.md
@standards/rules/17-gate.md

<!--
Only these three are imported: an import loads in every session. Every other rule file loads when it
applies, through the Claude kit - run `python standards/tooling/claude/install.py` from the project
root, with `--replicates` if the project replicates (27.7). Never add an @import for another rule file.
-->

The team standard is pinned at `standards/` - a release, never a branch (26.4) - and is never edited:
a deviation goes in the override table below. The other rule files load when they apply - the C++
rules with the first source file, the save-data rules with the first save class (27.1). For work they
do not cover, use the skill: `ue-async`, `ue-performance`, `ue-traps`, `ue-content`, `ue-source-control`.

> Standard version: 4.2.0

## This project

- **Short name:** `<Project>` - class infixes, log categories, console commands (4.4, 4.8, 4.11).
- **Content root:** `Content/_<Project>/` (2.1).
- **Modules:** `<Project>`, plus only the modules this project actually has (1.1). List what exists;
  a module the project does not need yet is not recorded as missing.
- **Replication:** *this project replicates* / *this project is single-player* - pick one, in these
  words (11.1). If it replicates, say whether push model and Iris are on (11.8).
- **Engine version:** `5.x`, and whether the project tracks minor releases (22.1).
- **Frame budget:** per target, in ms, with line items and owners (13.2) - on more than one platform,
  the tier table under "Cross-platform rules" (28.4).
- **Editor connection:** *on* or *off* - Claude driving the running editor through Unreal MCP (27.8). If
  on, the account's data-use terms were checked first.
- **Source control:** the system, how binary assets are stored and locked, and how the standard is
  pinned - vendored copy or submodule (26.2, 26.4).
- **Prototype module, once the first prototype starts:** `<Project>Prototype`, type `DeveloperTool` -
  held only to the safety rules (1.6). Code copied out of it is rewritten, not moved.
- **Standard contact:** the person who raises this project's `CONFLICT` blocks with the standard's
  owner (README, "Ownership").
- **CI:** `python standards/tooling/check-project.py .`, `python standards/tooling/verify-standard.py`,
  `python standards/tooling/claude/install.py --check` and the `DataValidation` commandlet, all in the
  every-commit tier (14.5); `check-project.py` with `--warn-only` until the backlog is clear (18.4).

## Cross-platform rules

<!--
For a project on more than one platform or store; delete it on a single-platform project. The rules
are section 28, which loads with platform code and config (27.1); this block holds this project's
values. Replace every TODO before the first build on a new platform.
-->

- **Targets:** TODO platforms now; TODO platforms later, and the milestone that adds them (28.1).
- **Platform code:** behind an interface, in platform-named folders (`Android/`, `IOS/`, `Windows/`);
  console code in `Platforms/<Platform>/`, restricted to people under that platform's terms (28.1).
- **Platform services:** saves `U<Project>SaveSubsystem`; TODO the subsystem for achievements,
  identity, entitlements and haptics. Store and product IDs: TODO the DataAsset (28.2).
- **Folder owners** (2.1, 28.5): technical art - `Art/`, `VFX/`, master materials; programming -
  `Core/`, `Core/Data/`, gameplay Blueprints. TODO the rest, with the person who owns each.
- **Device-profile tiers and budgets** - the lowest tier is the floor (28.4, 28.6):

| Tier | Device profile | Reference device | Frame ms | Memory MB | Draw calls | Triangles | Texture pool MB |
|---|---|---|---|---|---|---|---|
| Android low | `Android_Low` | TODO | TODO | TODO | TODO | TODO | TODO |
| Android mid | `Android_Mid` | TODO | TODO | TODO | TODO | TODO | TODO |
| Android high | `Android_High` | TODO | TODO | TODO | TODO | TODO | TODO |
| iOS | TODO `IOS_*` profiles | TODO | TODO | TODO | TODO | TODO | TODO |
| Windows | `Windows` | TODO | TODO | TODO | TODO | TODO | TODO |

- **Device-profile and scalability CVar changes** - every one logged here (28.6):

| Date | Profile or CVar | Change | Why |
|---|---|---|---|
| | | | |

- **Build and cook** (28.8), from the project root - `<Engine>` is the engine folder:

```
<Engine>\Engine\Build\BatchFiles\RunUAT.bat BuildCookRun -project=<full path>\<Project>.uproject -platform=Win64 -clientconfig=Development -build -cook -stage -pak -iostore -archive -archivedirectory=<output>
<Engine>\Engine\Build\BatchFiles\RunUAT.bat BuildCookRun -project=<full path>\<Project>.uproject -platform=Android -cookflavor=ASTC -clientconfig=Development -build -cook -stage -pak -iostore -archive -archivedirectory=<output>
```

  A store release adds `-createreleaseversion=<version>`; a patch adds
  `-basedonreleaseversion=<version> -generatepatch` (28.9).
- **Version:** `ProjectVersion` in `DefaultGame.ini`, plus the CI build number (28.9).
- **Chunks:** TODO which chunk IDs ship in the base app, and which download later (28.9).
- **Cloud saves:** TODO services; conflict policy TODO - for example, the newer timestamp wins, with
  a prompt when progress differs; save size budget TODO KB (24.8).

## Project overrides

**Every deliberate deviation from the standard goes here**, with its section number and the reason.
An unwritten deviation is a defect, not an override (00-core, "Which document wins"). The project
README links to this list rather than keeping a second copy.

| Section | The standard says | This project does | Why |
|---|---|---|---|
| | | | |

Nothing in the table yet means nothing is being deviated from, not that nobody wrote it down.

## Canonical examples

For each recurring pattern, the real class in this codebase that implements it well (18.5). This
beats describing a pattern, and it gives the assistant something to match.

| Pattern | Follow this |
|---|---|
| Countdown on a timer (3.7) | |
| Subsystem with instrumentation (13.6) | |
| Tag-keyed data table instead of a switch (9.2) | |
| Async load with a fallback (10.3) | |

## Project traps

This project's section 16 - engine or codebase behaviour that fooled someone here once. A trap a
second project hits moves into the standard (README, "Changing this standard").

## Threading candidates

Systems registered under 10.10 - the only ones that get callback-shaped APIs, an `Async` suffix and a
split gather/compute/apply before they are threaded. Every other system stays synchronous. Delete this
section on a project too small to run profiling milestones (10.10 is `[team-size]`).

| System | Owner | Criteria met (10.10) | Registered | Last reviewed |
|---|---|---|---|---|
| | | | | |

Each system listed here carries `THREADING-CANDIDATE` in its class comment.

## What Claude must NOT do

Each one breaks a platform, a store, a future target or a player's save in a way the editor does
not show.

- **Never add platform-specific code to a shared gameplay class** - it goes behind an interface (28.1).
- **Never load an asset synchronously in gameplay code** - soft references and async loads (10.3).
- **Never bind an action for only one input device** - every device the project ships on (28.3).
- **Never use `FString` for player-facing text** - `FText` from `LOCTEXT` or a string table (12.5).
- **Never make a per-platform copy of an asset, or a per-platform branch** (28.1, 28.5).
- **Never change a device profile or scalability CVar without logging it** in its table (28.6).
- **Never store a pointer, an asset path or an array index in save data** - a stable ID (24.8).
- **Never change what a saved field means without bumping the save version and adding a migration**
  (24.4) - but never bump for a change tagged serialisation already handles (24.2).
- **Never rename or move a shipped asset without a redirect** that keeps the old name loading (28.9).
- **Never hard-reference DLC content** from base game code or assets (28.9).
- **Never hard-code a store ID, product ID or entitlement check in gameplay** - the service layer (28.2).
- **Never ship a build whose save fixtures have not loaded** in the automated test (24.6).
- **Never require a keyboard, mouse or touch** anywhere in the game flow (29.2).
- **Never assume a fixed resolution or aspect ratio** in UI (29.4).
- **Never hard-code a frame-rate cap or vsync behaviour** (29.5).
- **Never add handheld-specific code or profiles** until handhelds are a target (29.1).

## How to work here

- **Size the task first (27.2).** One sentence: do it directly. Medium: plan in plan mode, then build.
  Large: `/ue-plan`, then `/clear`, then `/ue-implement <plan>` in a fresh session.
- Raise any conflict with a rule in a `CONFLICT` block before writing code (14.1, `/ue-conflict`).
- **Check your own work and show the evidence** - the command and what it printed (27.4):
  - build: `python standards/tooling/claude/scripts/ue_build.py`
  - assets: `python standards/tooling/claude/scripts/ue_validate.py`
  - logs: `python standards/tooling/claude/scripts/ue_log.py`
  - engine behaviour: ask the ue-engine-source agent - never assume how the engine behaves
- Run `/ue-gate` - the twelve items of 17.1 - before every commit.
- If an advisor is configured, consult it only while building - a recurring error, or before
  declaring done - not while planning (27.2).

## Compact instructions

When compacting, keep: the task and its plan file, every file changed, each decision and `CONFLICT`
answer, open errors with file:line, and the commands that verify the work.
