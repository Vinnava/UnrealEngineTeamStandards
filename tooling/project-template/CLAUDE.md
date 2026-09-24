# <Project> - rules for an AI assistant

Copy this to the project root as `CLAUDE.md` and fill in every `<Project>`. This is the file the
assistant actually reads, so anything it must obey has to be reachable from here - a rule that lives
only in the project README is a rule the assistant never sees.

---

## The standard

@standards/rules/00-core.md
@standards/rules/01-02-layout.md
@standards/rules/03-cpp.md
@standards/rules/04-cpp-naming.md
@standards/rules/05-06-comments-logging.md
@standards/rules/07-08-content-blueprint.md
@standards/rules/09-architecture.md
@standards/rules/14-15-practice.md
@standards/rules/17-gate.md

Add the optional files this project needs - `10-async`, `11-networking` if it replicates, `12-ui`,
`13-performance`, `16-engine-traps`, `19-audio`, `20-accessibility`, `21-online` if it talks to a
backend, `22-upgrades` at upgrade time. Delete the ones it does not.

**Every file is named for the sections it holds**, so `11-networking.md` is section 11 and
`05-06-comments-logging.md` is sections 5 and 6. A number means the same thing everywhere.

`17-review.md` and `18-adopting.md` are deliberately **not** imported: the first is read when
reviewing, the second once when the project starts. `17-gate.md` is the twelve-item commit gate and
is the one worth carrying on every request.

`00-core.md` is not optional. It carries the ranked pillars every `CONFLICT` block is decided by, the
precedence order, and the `<Project>` convention.

The paths assume the standard is a git submodule at `standards/`, **checked out at a release tag** -
never a branch, so the project upgrades when it decides to (README, "Versioning"). Adjust them if it
lives elsewhere.

**Record which version** (the README header) so a reader can tell whether a rule has moved on:

> Standard version: 2.0.1

## This project

- **Short name:** `<Project>` - class infixes, log categories, console commands (4.4, 4.8, 4.11).
- **Content root:** `Content/_<Project>/` (2.1).
- **Modules:** `<Project>`, plus only the modules this project actually has (1.1). List what exists;
  a module the project does not need yet is not recorded as missing.
- **Replication:** *this project replicates* / *this project is single-player* - pick one, in these
  words (11.1). If it replicates, say whether push model and Iris are on (11.8).
- **Engine version:** `5.x`, and whether the project tracks minor releases (22.1).
- **Prototype module, once the first prototype starts:** `<Project>Prototype`, type `DeveloperTool` -
  held only to the safety rules (1.6). Code copied out of it is rewritten, not moved.
- **Standard contact:** the person who raises this project's `CONFLICT` blocks with the standard's
  owner (README, "Ownership").
- **CI:** `python standards/tooling/check-project.py .` and the `DataValidation` commandlet, both in
  the every-commit tier (14.5); `--warn-only` until the backlog is clear (18.4).

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

## How to work here

- Plan first. Raise any conflict with a rule in a `CONFLICT` block before writing code (14.1).
- One file at a time for unfamiliar systems; the whole change at once when the plan is agreed (14.2).
- Run the 17.1 gate - twelve items - before every commit. 17.2 is for review, not per commit.
