# 0. Core: pillars, precedence and placeholders

Part of the [Unreal Engine Team Standards](../README.md). The reasoning is in [why.md](../why.md).

**Load this file first, and load it always.** Every other rule file assumes it. A `CONFLICT` block
(14.1) cannot be written without the pillars, and no rule in this standard can be applied without
knowing what beats what.

This file carries no numbered sections of its own; it is what the numbered sections rest on.

---

## Placeholders

`<Project>` is the only placeholder. It stands for the project's short name - PascalCase in class,
module and folder names, lowercased where the convention is lowercase (variables, console commands).
Code examples use **`Game`** as a concrete stand-in: `LogGameQuest`, `GAME_API`, `gameGI`,
`game.quest.launch`.

---

## Which document wins

When rules disagree, the higher item wins:

1. **The engine.** What Unreal actually does, verified in its source, beats every document - this
   standard included. A rule here that fights the engine is a defect here.
2. **A project's written override** - listed in that project's **`CLAUDE.md`** with the section
   number and the reason, because that is the file an assistant is given; the project README links to
   that list rather than keeping a second copy of it. It wins inside that project only.
3. **This standard.**
4. **A project's other documents** - its `CLAUDE.md`, rule files, wiki. They may add rules and
   project detail; where they contradict this standard without a written override, this standard
   wins and the project document is the defect.
5. **Existing code and habit.** "The codebase already does it this way" is evidence of a past
   decision, not permission.

An unwritten deviation is a defect, not an override.

---

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

---

## How strong is a rule

Most rules here are unconditional: they cost nothing to follow and the standard expects them on a
two-person prototype and a hundred-person production alike.

A few are **marked `[team-size]`**. Those need a team, a budget or dedicated hardware to be worth
doing, and a solo project that skips them is not violating the standard - it is reading it correctly.
Section 18 says when each one lands. A rule with no marker has no size exemption.

Nothing here is aspirational. If a rule is wrong, or you cannot follow it, that is a defect in the
standard: raise it (README, "Changing this standard"), do not quietly work around it.
