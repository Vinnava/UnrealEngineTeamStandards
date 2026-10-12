# Unreal Engine Team Standards

The rules every developer on this team follows, on every Unreal project.

The standard is **project-agnostic**: nothing in it depends on a particular game, module or feature.
Where a project has to pin something down - its module name, content root or short prefix - the
standard uses a `<Project>` placeholder, and that project's `CLAUDE.md` fills it in - from
[`tooling/project-template/`](tooling/project-template/).

**Version 4.1.0** - see the [changelog](CHANGELOG.md). **Owner: @Vinnava** ("Ownership" below). Written against **Unreal Engine 5.x**. Every
claim about engine behaviour was checked against **UE 5.7** source, and the defaults that matter
were re-checked in **5.8**. Where a rule depends on the engine version, it says so.

---

## How this is organised

**New here? Start with [ONBOARDING.md](ONBOARDING.md)** - the fifteen minutes that matter in week one.

- **[`rules/`](rules/)** - the standard itself: short, direct rules, one file per area. Read the
  relevant file before you work; give the files to your AI assistant.
- **[`why.md`](why.md)** - the reasoning behind the rules, section by section, including the real
  incidents behind them. It is for people. Read it when a rule looks arbitrary, and before you change
  one.
- **[`tooling/`](tooling/README.md)** - what enforces the mechanical rules: `.clang-format`,
  `.clang-tidy`, `.editorconfig`, two asset validators, a project checker, a verifier that proves a
  project's copy of the standard is unedited, the Claude kit (27), a consistency checker for this
  repository, and the project templates. Every one of them has been run for real - the validators
  compiled against UE 5.7 and run in a headless editor on assets built to pass and to fail - and
  [`.github/workflows/standard.yml`](.github/workflows/standard.yml) gates every push.
- **[PILOT.md](PILOT.md)** - how the standard goes from written to proven: one project, one
  milestone, measured.

**Section numbers are global and stable, and every file is named for the sections it holds.** "(3.12)"
means section 3.12, and it is in `rules/03-cpp.md`. A file covering more than one section carries the
span: `rules/05-06-comments-logging.md`. There is no second numbering scheme to keep straight.

| Sections | File | Read it |
|---|---|---|
| - | [rules/00-core.md](rules/00-core.md) | **Always, and first** - pillars, precedence, placeholders |
| 1-2 | [rules/01-02-layout.md](rules/01-02-layout.md) | Before you add a file or an asset |
| 3 | [rules/03-cpp.md](rules/03-cpp.md) | Before your first line of code |
| 4 | [rules/04-cpp-naming.md](rules/04-cpp-naming.md) | Before your first line of code |
| 5-6 | [rules/05-06-comments-logging.md](rules/05-06-comments-logging.md) | Before your first line of code |
| 7-8 | [rules/07-08-content-blueprint.md](rules/07-08-content-blueprint.md) | Before your first asset or Blueprint |
| 9 | [rules/09-architecture.md](rules/09-architecture.md) | Before you design a system |
| 10 | [rules/10-async.md](rules/10-async.md) | Before anything async |
| 11 | [rules/11-networking.md](rules/11-networking.md) | Only if the project replicates |
| 12 | [rules/12-ui.md](rules/12-ui.md) | Before you build UI |
| 13 | [rules/13-performance.md](rules/13-performance.md) | Before you optimise, and before you ship |
| 14-15 | [rules/14-15-practice.md](rules/14-15-practice.md) | Once; and when something is wrong |
| 16 | [rules/16-engine-traps.md](rules/16-engine-traps.md) | Before you touch a named system |
| 17.1 | [rules/17-gate.md](rules/17-gate.md) | **Every commit** - the twelve-item gate |
| 17.2-17.4 | [rules/17-review.md](rules/17-review.md) | Reviewing someone's work; when a feature lands |
| 18 | [rules/18-adopting.md](rules/18-adopting.md) | Once, when a project starts |
| 19 | [rules/19-audio.md](rules/19-audio.md) | Before you play a sound |
| 20 | [rules/20-accessibility.md](rules/20-accessibility.md) | Before the first screen; before any player-facing text |
| 21 | [rules/21-online.md](rules/21-online.md) | Only if the project talks to a backend |
| 22 | [rules/22-upgrades.md](rules/22-upgrades.md) | Before an engine upgrade |
| 23 | [rules/23-content-pipeline.md](rules/23-content-pipeline.md) | Before you import a texture, mesh or level |
| 24 | [rules/24-save-data.md](rules/24-save-data.md) | Before you change anything a save file holds |
| 25 | [rules/25-gas.md](rules/25-gas.md) | Only if the project uses GAS |
| 26 | [rules/26-source-control.md](rules/26-source-control.md) | Choosing or setting up source control; pinning or upgrading this standard |
| 27 | [rules/27-ai-assistants.md](rules/27-ai-assistants.md) | When a project adopts the Claude kit, or Claude Code changes |
| 28 | [rules/28-cross-platform.md](rules/28-cross-platform.md) | More than one platform or store; before a release, a patch or a DLC |

**Lost, or something is behaving impossibly?** Go straight to the debugging playbook in
[rules/14-15-practice.md](rules/14-15-practice.md) (section 15). It is the highest-value page here on an
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

The standard is set up for **Claude Code** - section 27 and the kit in
[`tooling/claude/`](tooling/claude/). These are **file** names from the table above; a number in
prose is always a section.

- **Every project:** `00-core`, `14-15-practice` and `17-gate` - imported by the project's
  `CLAUDE.md`, so loaded in every session. Without the first of them the assistant has the rules and
  nothing to resolve them with - no pillars, no precedence order, no `<Project>` convention.
- **Everything else loads when it applies.** The kit's installer (27.7) turns the other rule files into
  rules Claude Code loads the first time it touches a matching file - the C++ files load with the
  first header, `24-save-data` with the first save class - and into skills loaded when the task calls
  for them: async, performance, engine traps, content, source control. **`11-networking` loads only
  if the project replicates.** [`tooling/claude/rule-groups.json`](tooling/claude/rule-groups.json)
  is the map.
- **Read by people, not loaded:** `17-review` is read by the reviewer agent when reviewing,
  `18-adopting` once when a project starts, `27-ai-assistants` when a project adopts the kit.
- **With an assistant other than Claude Code,** import `01-02-layout`, `03-cpp`, `04-cpp-naming`,
  `05-06-comments-logging`, `07-08-content-blueprint` and `09-architecture` as well, and the rest as
  the work needs them.
- **The always-loaded set has a budget: 8,000 tokens, and each rule group in `rule-groups.json` has
  its own,** counted at the rate measured in Claude Code sessions - 2.5 characters a token.
  `tooling/check-standard.py` fails the build when a change pushes one over, and when a rule file is
  left with nothing that loads it - so growth is a decision made on purpose, with the reason, in the
  same pull request.

Leave `why.md` out of assistant context unless you are changing a rule.

## Adopting it

**In tiers** (18). Doing all of it on day one is not the goal, and a standard that cannot be
partially adopted gets wholly ignored.

| Tier | When | What it buys |
|---|---|---|
| **1** (18.1) | Before the first feature | The decisions that are expensive or impossible to reverse: module split, content root, short name, replication, source control set up before the first asset |
| **2** (18.2) | Before the first milestone | Production discipline: tooling, CI, budgets, validators, accessibility and audio decisions |
| **3** (18.3) | When review alone stops working | Blueprint lint, reference budgets, perf regression gates, upgrade cadence |

A two-person prototype does Tier 1 and stops - it is not failing the standard by doing so. Adopting
it onto an existing codebase is 18.4: new code meets it in full from day one, nothing is renamed on
sight, and every deliberate deviation is written down as an override.

## Ownership

**The owner is @Vinnava.** One person decides when two readings of a rule conflict, approves every
change, and answers for the standard staying true.

- **While the owner is the only maintainer, `main` is protected by CI, not by review.** GitHub does not
  let an author approve their own pull request, so a required review would lock the owner out. Two
  GitHub rulesets do the protecting: on `main`, a commit is accepted only once every job in the
  [`standard`](.github/workflows/standard.yml) workflow has passed on that exact commit, and force-pushes
  and deletion are blocked; on `v*` tags, a release cannot be moved or deleted once pushed. When a
  second maintainer joins, add a `CODEOWNERS` file and a required review to the `main` ruleset.
- **Every quarter, the owner:** re-runs the engine re-verification list (22.2) if the engine moved,
  promotes project traps that a second project hit into section 16, prunes rules nobody cited or
  enforced, and checks the always-loaded budget still fits.
- **A project names its own contact** - the person who raises its `CONFLICT` blocks with the owner -
  in its `CLAUDE.md`. Projects do not each own a copy of the standard.

## Versioning

Releases follow semantic versioning, and **a project pins a release, not a branch**:

| Bump | When | Cadence |
|---|---|---|
| **Major** (`3.0.0`) | A rule changes meaning, a rule is removed, or a file is renamed | At most twice a year |
| **Minor** (`2.1.0`) | New rules or new sections, nothing existing changes meaning | At most monthly |
| **Patch** (`2.0.1`) | Wording, examples, typos, tooling fixes | Whenever needed |

- **Every release is a git tag** - `v2.0.0` - and carries `MANIFEST.sha256`, a hash of every file in it.
  A project pins one release - a vendored copy, or a submodule on git - and verifies it in CI (26.4),
  so it upgrades when it chooses, not whenever `main` moves, on whatever source control it uses.
- **A changelog bullet that changes a rule's meaning starts with "Rule change:"**, and
  `tooling/check-standard.py` fails a release that carries one without a major version. A reader
  pinned to `2.x` can trust that no `2.x` release reversed a rule under them.
- **The 1.x history predates this policy.** 1.0 to 1.9 were the drafting of the standard, before it was
  used in production; 2.0.0 is the first release meant for it.

## Changing this standard

This document is maintained the way the code is. A rule you cannot follow is a defect here, not a
reason to work around it quietly.

- **Proposing a change** uses the `CONFLICT` block (14.1): the rule, what it forces today, what the
  change needs, the options, and a recommendation. A change to a rule lands with its `why.md` entry
  in the same commit - a rule with no recorded reasoning is one the next person will delete.
- **Engine claims are re-verified on every upgrade** (22.2), and the version in the header above is
  updated with them. A claim that can no longer be verified is marked unverified rather than left
  implying it was checked.
- **Deprecating a rule** is an entry in the changelog saying what replaced it and why, not a silent
  deletion. Rules removed because the engine fixed the underlying problem say which version fixed it.
- **A project's trap becomes a general one** when a second project hits it: it moves from that
  project's section 16 into [rules/16-engine-traps.md](rules/16-engine-traps.md), with the incident
  in `why.md`.
- **Every change is versioned** in [CHANGELOG.md](CHANGELOG.md), under the policy above.

---

Nothing here is aspirational. If a rule is wrong, or you cannot follow it, that is a defect in the
standard - fix it here rather than quietly working around it, so the next project starts from what we
learned on this one.
