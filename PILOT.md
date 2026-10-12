# Pilot plan - from written to proven

The standard has been meant for production since 2.0.0. It is not yet **proven**: no project has
shipped a milestone under it. This is how it earns that, on one project, over one milestone, with numbers
rather than impressions.

**Owner:** the standard's owner (README, "Ownership"). **Length:** one milestone.

---

## Before the pilot starts

- [ ] **Pick the project** and record it in that project's `CLAUDE.md` and measurement table - not in
      this file, which stays the same for every pilot. One project, not several - a pilot that is
      everywhere is measured nowhere.
- [ ] **camelCase (4.1) is settled before the pilot, not during it.** With one developer the owner
      decides, and 4.1.0 recorded the decision to keep it (why.md, 4.1). With a team, the team votes
      once and the result is recorded the same way. Either way, it is not reopened mid-pilot.
- [ ] **If the project has art or design leads, name them to review section 23.** Without leads, its
      conventions stand as written, and the review waits for the first lead to join.
- [ ] **Pin the standard at `v4.1.0`** (26.4) and verify the copy with `verify-standard.py`, and
      create the project `CLAUDE.md` from [`tooling/project-template/`](tooling/project-template/).
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
| **Claude Code usage per task** | `/usage` and `/context` on comparable tasks, before and after a change to the kit (27.6) | Whether the kit's loading, agents and workflow cost less for the same work |
| **New-hire time to first merged change** | Measured for anyone who joins during the pilot, using [ONBOARDING.md](ONBOARDING.md); not measured when nobody joins | Whether the onboarding page is enough |

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
- **If art or design leads reviewed section 23,** their changes land here - each convention kept,
  changed or deleted like any other rule.

The retro's changes ship as the next minor version if no rule changes meaning, or the next major if
any does (README, "Versioning").

## The standard is proven when

- It has run for one full milestone on one project.
- Every check runs in CI in failing mode, not warning mode.
- The retro has been held and its changes released.
- The override count has stabilised - new overrides have stopped appearing in the final weeks.
- At least one person has onboarded using [ONBOARDING.md](ONBOARDING.md) alone - or, with nobody
  joining, that check is carried open to the first person who does.

Until then, projects other than the pilot adopt Tier 1 only (18.1).
