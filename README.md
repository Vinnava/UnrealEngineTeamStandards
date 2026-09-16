# Unreal Engine Team Standards

The rules every developer on this team follows, on every Unreal project.

The standard is **project-agnostic**: nothing in it depends on a particular game, module or feature.
Where a project has to pin something down - its module name, content root or short prefix - the
standard uses a `<Project>` placeholder, and that project's `CLAUDE.md` fills it in - from
[`tooling/project-template/`](tooling/project-template/).

**Version 1.7** - see the [changelog](CHANGELOG.md). Written against **Unreal Engine 5.x**. Every
claim about engine behaviour was checked against **UE 5.7** source, and the defaults that matter
were re-checked in **5.8**. Where a rule depends on the engine version, it says so.

---

## How this is organised

- **[`rules/`](rules/)** - the standard itself: short, direct rules, one file per area. Read the
  relevant file before you work; give the files to your AI assistant.
- **[`why.md`](why.md)** - the reasoning behind the rules, section by section, including the real
  incidents behind them. It is for people. Read it when a rule looks arbitrary, and before you change
  one.
- **[`tooling/`](tooling/README.md)** - files that enforce the mechanical rules: `.clang-format`,
  `.clang-tidy`, `.editorconfig`, an asset-naming validator, and a consistency checker for this
  repository. Every one of them has been run against this repository, and
  [`.github/workflows/standard.yml`](.github/workflows/standard.yml) runs the two that can gate a
  commit on every push.

**Section numbers are global and stable.** A bare number in prose is always a **section**, never a
file: "(3.12)" means section 3.12 wherever it appears, and this table says which file holds it - in
that case `rules/02-cpp.md`, whose own name carries an unrelated `02`.

| Sections | File | Read it |
|---|---|---|
| - | [rules/00-core.md](rules/00-core.md) | **Always, and first** - pillars, precedence, placeholders |
| 1-2 | [rules/01-layout.md](rules/01-layout.md) | Before you add a file or an asset |
| 3 | [rules/02-cpp.md](rules/02-cpp.md) | Before your first line of code |
| 4 | [rules/03-cpp-naming.md](rules/03-cpp-naming.md) | Before your first line of code |
| 5-6 | [rules/04-comments-logging.md](rules/04-comments-logging.md) | Before your first line of code |
| 7-8 | [rules/05-content-blueprint.md](rules/05-content-blueprint.md) | Before your first asset or Blueprint |
| 9 | [rules/06-architecture.md](rules/06-architecture.md) | Before you design a system |
| 10 | [rules/07-async.md](rules/07-async.md) | Before anything async |
| 11 | [rules/08-networking.md](rules/08-networking.md) | Only if the project replicates |
| 12 | [rules/09-ui.md](rules/09-ui.md) | Before you build UI |
| 13 | [rules/10-performance.md](rules/10-performance.md) | Before you optimise, and before you ship |
| 14-15 | [rules/11-practice.md](rules/11-practice.md) | Once; and when something is wrong |
| 16 | [rules/12-engine-traps.md](rules/12-engine-traps.md) | Before you touch a named system |
| 17-18 | [rules/13-checklists.md](rules/13-checklists.md) | Every commit; when starting a project |
| 19 | [rules/14-audio.md](rules/14-audio.md) | Before you play a sound |
| 20 | [rules/15-accessibility.md](rules/15-accessibility.md) | Before the first screen; before any player-facing text |
| 21 | [rules/16-online.md](rules/16-online.md) | Only if the project talks to a backend |
| 22 | [rules/17-upgrades.md](rules/17-upgrades.md) | Before an engine upgrade |

**Lost, or something is behaving impossibly?** Go straight to the debugging playbook in
[rules/11-practice.md](rules/11-practice.md) (section 15). It is the highest-value page here on an
ordinary day, and the first item solves more mysteries than the other twenty-four combined.

---

## Pillars, precedence and placeholders

These live in **[rules/00-core.md](rules/00-core.md)** - the ranked architecture pillars, the
"which document wins" order, the `<Project>` placeholder convention, and what the `[team-size]`
marker means.

They are in a rule file rather than here because an assistant is given `rules/`, not this README, and
every `CONFLICT` block (14.1) depends on the pillars. Keeping them here would mean handing an
assistant the rules without the thing that decides between them.

## Giving this to an AI assistant

Import only the files a project needs. These are **file** names from the table above; a number in
prose is always a section.

- **Always, in every project, first:** `00-core`. Without it the assistant has the rules and nothing
  to resolve them with - no pillars, no precedence order, no `<Project>` convention.
- **Every project:** `00-core`, `01-layout` to `06-architecture`, plus `11-practice` and
  `13-checklists`.
- **Add as needed:** `07-async` for async work, **`08-networking` only if the project replicates**,
  `09-ui` for UI, `10-performance` for performance work, `12-engine-traps` as a reference before
  touching a named system, `14-audio` for audio, `15-accessibility` for player-facing text and UI,
  **`16-online` only if the project talks to a backend**, `17-upgrades` at upgrade time.

Reference them from the project's `CLAUDE.md` or equivalent. Leave `why.md` out of assistant context
unless you are changing a rule.

## Adopting it

**In tiers** (18). Doing all of it on day one is not the goal, and a standard that cannot be
partially adopted gets wholly ignored.

| Tier | When | What it buys |
|---|---|---|
| **1** (18.1) | Before the first feature | The decisions that are expensive or impossible to reverse: module split, content root, short name, replication, LFS before the first asset |
| **2** (18.2) | Before the first milestone | Production discipline: tooling, CI, budgets, validators, accessibility and audio decisions |
| **3** (18.3) | When review alone stops working | Blueprint lint, reference budgets, perf regression gates, upgrade cadence |

A two-person prototype does Tier 1 and stops - it is not failing the standard by doing so. Adopting
it onto an existing codebase is 18.4: new code meets it in full from day one, nothing is renamed on
sight, and every deliberate deviation is written down as an override.

## Changing this standard

This document is maintained the way the code is. A rule you cannot follow is a defect here, not a
reason to work around it quietly.

- **It has an owner.** The project README names who maintains this standard for that team, and who
  decides when two readings conflict. Without a name, "someone should fix that" is where a defect
  goes to stay.
- **Proposing a change** uses the `CONFLICT` block (14.1): the rule, what it forces today, what the
  change needs, the options, and a recommendation. A change to a rule lands with its `why.md` entry
  in the same commit - a rule with no recorded reasoning is one the next person will delete.
- **Engine claims are re-verified on every upgrade** (22.2), and the version in the header above is
  updated with them. A claim that can no longer be verified is marked unverified rather than left
  implying it was checked.
- **Deprecating a rule** is an entry in the changelog saying what replaced it and why, not a silent
  deletion. Rules removed because the engine fixed the underlying problem say which version fixed it.
- **A project's trap becomes a general one** when a second project hits it: it moves from that
  project's section 16 into [rules/12-engine-traps.md](rules/12-engine-traps.md), with the incident
  in `why.md`.
- **Every change is versioned** in [CHANGELOG.md](CHANGELOG.md), and anything that changes a rule's
  *meaning* says so in those words, so a reader can tell a clarification from a reversal.

---

Nothing here is aspirational. If a rule is wrong, or you cannot follow it, that is a defect in the
standard - fix it here rather than quietly working around it, so the next project starts from what we
learned on this one.
