# 18. Adopting this on a new project

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

Read once, when a project starts. Adoption is tiered: a two-person prototype does Tier 1 and stops.

---

## 18. Adopting this on a new project

**Adopt it in tiers.** A two-person prototype does Tier 1 and stops; it is not failing the standard
by doing so. A team shipping on console does all three. Skipping a tier is a decision worth writing
down; doing Tier 3 before Tier 1 is how a project ends up with perfect CI and no module boundary.

### 18.1 Tier 1 - before the first feature

**Everything here is expensive or impossible to change later.** This is the minimum for any project
that will outlive the prototype.

- [ ] Module split decided (`<Project>` / `<Project>Online`) - 1.1
- [ ] Source folder skeleton in place - 1.3
- [ ] Content root `Content/_<Project>/` created, folder skeleton in place - 2.1
- [ ] Project short name pinned, for class infixes and short variable names - 4.4, 4.8
- [ ] Log category naming pinned: `Log<Project><Domain>`, `DEFINE_LOG_CATEGORY_STATIC` by default - 6.2
- [ ] GameplayTag root namespaces agreed - 4.10
- [ ] **Replication decided and written down in the README** - "this project replicates" or "this
      project is single-player" - 11.1
- [ ] Version control chosen, and **Git LFS with `.gitattributes` in place before the first asset
      commit**; locking on for `.uasset` and `.umap` - 14.3
- [ ] A `TEMP/` or `Developers/` content folder created, so prototypes have somewhere legitimate to
      live - 8.2
- [ ] A project **`CLAUDE.md`** from [`tooling/project-template/`](../tooling/project-template/),
      filling in every `<Project>` placeholder, importing `00-core` plus the rule files this
      project needs, and **holding the override table** - the assistant reads this file, not the
      README (00-core)
- [ ] A project `README.md` that links to that override table rather than keeping a second copy,
      and links back to this standard

### 18.2 Tier 2 - before the first milestone

Production discipline. Each of these gets cheaper the earlier it lands, but none of them is fatal to
retrofit.

- [ ] Console command namespace pinned: `<Project>.<system>.<verb>`, lowercased - 4.11
- [ ] [`tooling/.clang-format`](../tooling/.clang-format),
      [`tooling/.clang-tidy`](../tooling/.clang-tidy) and
      [`tooling/.editorconfig`](../tooling/.editorconfig) copied to the project root, and a compile
      database generated - 3.10, 4.1
- [ ] [`tooling/Validators/AssetNamingValidator`](../tooling/README.md) installed in the project's
      editor module - 7.1-7.3
- [ ] [`tooling/project-template/PULL_REQUEST_TEMPLATE.md`](../tooling/project-template/PULL_REQUEST_TEMPLATE.md)
      copied to `.github/` - the rules no tool can check, sized like 17.1 rather than 17.2
- [ ] Data-driven asset types registered as Primary Asset Types - 13.3
- [ ] CI every-commit tier in place: compile, tests, validators - 14.5
- [ ] Automation tests for the pure logic that exists so far - 14.4
- [ ] Frame budget per target written down, with line items and owners - 13.2
- [ ] On a replicated project: push model and Iris decided, and the missing-registration CVars set
      in `DefaultEngine.ini` - 11.3, 11.8
- [ ] Accessibility decisions made before the first screen is built - subtitles, remapping, colour
      channel, text scale - 20.1
- [ ] Audio concurrency groups and the voice budget established - 19.3, 19.9
- [ ] If the project talks to a backend: the wire boundary, the retry policy and where tokens live -
      21.1, 21.2, 21.4
- [ ] The rules no tool can check - header order, comment content, the pillars - listed in the pull
      request template, sized like 17.1 rather than 17.2

### 18.3 Tier 3 - production scale

For a team large enough that review alone stops working.

- [ ] **Blueprint lint** as further validators: `Event Tick` without an approval comment (3.12), a
      node-count budget per graph, `Cast To` a Blueprint class (8.3), hard references past the
      reference budget (13.3)
- [ ] A reference-budget commandlet that fails CI when an asset's hard-dependency size passes its
      budget - set budgets just above today's values and ratchet them down - 13.3
- [ ] Nightly and weekly CI tiers: cook, package, dedicated server, perf and memory gates - 14.5
- [ ] A deterministic performance regression gate on dedicated hardware - 13.9
- [ ] A save archived from every shipped version, loaded in CI - 9.14
- [ ] Engine upgrade cadence agreed and an owner named - 22.1
- [ ] Per-platform cert requirement lists, each with an owner - 20.9

### 18.4 Retrofitting onto an existing project

The standard is written for a new project. On an existing one:

- **New and modified code meets the standard in full, from the day you adopt it** (5.4, 6.5). That
  rule is what makes adoption possible at all.
- **Rename nothing on sight.** Asset and class renames are planned batches, agreed with whoever owns
  that content, in their own commits (7.6, 3.8).
- **Turn each validator on in warning mode first**, fix the backlog in planned passes, then make it
  fail the build. A gate that fails on day one gets disabled on day two (13.9).
- **Pick the three rules whose violation is costing you most right now** and fix only those first.
  For most projects that is ownership (9.4), hard references (13.3) and Tick (3.12).
- **Write down every deliberate deviation as a project override**, with its section number and
  reason. An unwritten deviation is a defect; a written one is a decision.

### 18.5 Ongoing

- [ ] A project-level `CLAUDE.md` or equivalent that imports the rule files the project needs (see
      the README), so assistants follow the same rules as people
- [ ] A **canonical examples** list in the project README: for each recurring pattern, the real class
      that implements it well - "countdowns: follow the time-bomb timer on the ball actor"
- [ ] A living document of project-specific decisions and traps - that project's section 16. Every
      trap you hit that is not in this standard goes there; the genuinely engine-general ones come back
      here (see "Changing this standard" in the README)
