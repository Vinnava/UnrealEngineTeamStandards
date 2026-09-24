# Pilot plan - from written to proven

Version 2.0.0 is the first release meant for production. It is not yet **proven**: no team has shipped
a milestone under it. This is how it earns that, on one project, over one milestone, with numbers
rather than impressions.

**Owner:** the standard's owner (README, "Ownership"). **Length:** one milestone.

---

## Before the pilot starts

- [ ] **Pick the project** and name it in this file. One project, not several - a pilot that is
      everywhere is measured nowhere.
- [ ] **Hold the camelCase vote** (4.1) with the whole team, and record the result in 4.1 with its
      reasoning either way. It is the most expensive rule in the standard and the only one the team
      should decide by vote rather than inherit. Do not reopen it during the pilot.
- [ ] **Name the art lead and the design lead who will extend section 23.** It covers only what is
      verified in engine source; their workflows are the rest of it.
- [ ] **Add the standard as a submodule pinned to `v2.0.0`**, and create the project `CLAUDE.md` from
      [`tooling/project-template/`](tooling/project-template/).
- [ ] **Install the validators in the project's editor module** and confirm they load. They are
      proven to compile and to catch what they claim in a scratch project on 5.7
      ([tooling/README.md](tooling/README.md)); this proves they integrate with this project.
- [ ] **Run `check-project.py` and the `DataValidation` commandlet in CI with `--warn-only`** (18.4),
      so the existing backlog is visible before anything fails the build.
- [ ] **Record the baseline** - the counts below as they stand on day one.

## What to measure

Keep one table in the project repository, updated weekly. The point is the trend, not the absolute.

| Measure | How | What it says |
|---|---|---|
| **Overrides written** | Rows in the project `CLAUDE.md` override table, by section | Several on one section: that rule is wrong for real work. None anywhere: nobody is following it closely enough to disagree |
| **Gate items skipped** | Ask at review; one line per skip with the item and the reason | An item skipped often is too expensive or not useful - it gets cut or turned into a tool |
| **Checker and validator findings** | The CI counts from `check-project.py` and `DataValidation` | Should fall week on week; flat means new code is adding violations as fast as old ones are fixed |
| **Traps added** | Entries in the project's own section 16 | Evidence the standard is being used as a reference. A trap a second project hits moves into the standard |
| **Section numbers cited in review** | Count review comments that cite a section | The standard is being used to settle questions rather than being ignored |
| **New-hire time to first merged change** | Measured for anyone who joins during the pilot, using [ONBOARDING.md](ONBOARDING.md) | Whether the onboarding page is enough |

## During the pilot

- **Switch each check from warning to failing** once its backlog is cleared (18.4). A check that
  fails on day one gets disabled on day two.
- **Every `CONFLICT` block raised against the standard is logged**, with its outcome. These are the
  most direct evidence of where the standard and real work disagree.
- **Do not change the standard mid-pilot** except to fix a defect that blocks work (a patch release).
  Rule changes wait for the retro, so the pilot measures one version, not a moving target.

## The retro at the end of the milestone

For every section, decide one of **keep, change or delete**, and record the reason in `why.md`:

- **A rule overridden repeatedly is changed or deleted.** Repeated overrides are the team telling the
  standard it is wrong.
- **A rule never cited and never enforced is a candidate for deletion.** If nobody needed it for a
  whole milestone, it is costing reading time and returning nothing.
- **A gate item skipped repeatedly is cut from the gate or turned into a tool** (17.4).
- **Section 23 absorbs what the art and design leads wrote.**

The retro's changes ship as **2.1.0** if no rule changes meaning, or **3.0.0** if any does
(README, "Versioning").

## The standard is proven when

- It has run for one full milestone on one project.
- Every check runs in CI in failing mode, not warning mode.
- The retro has been held and its changes released.
- The override count has stabilised - new overrides have stopped appearing in the final weeks.
- At least one person has onboarded using [ONBOARDING.md](ONBOARDING.md) alone.

Until then, projects other than the pilot adopt Tier 1 only (18.1).
