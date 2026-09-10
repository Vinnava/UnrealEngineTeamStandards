# Unreal Engine Team Standards

The rules every developer on this team follows, on every Unreal project.

The standard is **project-agnostic**: nothing in it depends on a particular game, module or feature.
Where a project has to pin something down - its module name, content root or short prefix - the
standard uses a `<Project>` placeholder, and that project's README fills it in.

**Version 1.3** - see the [changelog](CHANGELOG.md). Written against **Unreal Engine 5.x**. Every
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
  `.editorconfig` and an asset-naming validator.

**Section numbers are global and stable.** "(3.12)" means section 3.12 wherever it appears; this table
says which file holds it.

| Sections | File | Read it |
|---|---|---|
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

---

## Placeholders

`<Project>` is the only placeholder. It stands for the project's short name - PascalCase in class,
module and folder names, lowercased where the convention is lowercase (variables, console commands).
Code examples use **`Game`** as a concrete stand-in: `LogGameQuest`, `GAME_API`, `gameGI`,
`game.quest.launch`.

## Which document wins

When rules disagree, the higher item wins:

1. **The engine.** What Unreal actually does, verified in its source, beats every document - this
   standard included. A rule here that fights the engine is a defect here.
2. **A project's written override** - listed in that project's README with the section number and
   the reason. It wins inside that project only.
3. **This standard.**
4. **A project's other documents** - its `CLAUDE.md`, rule files, wiki. They may add rules and
   project detail; where they contradict this standard without a written override, this standard
   wins and the project document is the defect.
5. **Existing code and habit.** "The codebase already does it this way" is evidence of a past
   decision, not permission.

An unwritten deviation is a defect, not an override.

## Architecture pillars

Four pillars, **ranked**. Every rule serves one of them. When two rules pull against each other, or a
request conflicts with a rule, **the higher-ranked pillar decides** - and the conflict is raised in a
`CONFLICT` block (14.1) before any code is written.

1. **Separation of concerns** - each class, component and system does one job (1.3, 9.8).
2. **Loose coupling** - systems talk through delegates, interfaces and subsystems, never by reaching
   into each other's classes (9.3, 9.7).
3. **Data-driven design** - behaviour a designer tunes lives in DataAssets, tags and settings, not in
   code (9.2, 9.6).
4. **Event-driven first, Tick when right** - delegates, events and timers wherever they fit; Tick only
   with approval (3.7, 3.12, 10.5).

The pillars say *what* to optimise for. The pattern catalogue in 9.10 says *how*.

## Giving this to an AI assistant

Import only the files a project needs:

- **Every project:** 01 to 06, 11 and 13.
- **Add as needed:** 07 for async work, **08 only if the project replicates**, 09 for UI, 10 for
  performance work, 12 as a reference before touching a named system.

Reference them from the project's `CLAUDE.md` or equivalent. Leave `why.md` out of assistant context
unless you are changing a rule.

---

Nothing here is aspirational. If a rule is wrong, or you cannot follow it, that is a defect in the
standard - fix it here rather than quietly working around it, so the next project starts from what we
learned on this one.
