# Your first week with the standard

The whole standard is about two hours of reading, and nobody should read it front to back. This page
is the fifteen minutes that matter in week one. Everything else, read the day you need it - the first
time you write Tick, read 3.12; the first time you touch networking, read section 11.

---

## Day one - twenty minutes

1. **[rules/00-core.md](rules/00-core.md)** - the four pillars, ranked, and which document wins when
   two disagree. When a rule seems to fight another, this page decides between them.
2. **[rules/17-gate.md](rules/17-gate.md)** - the twelve checks you run before every commit. They are
   the ones no tool can catch and that are expensive to undo.
3. **The debugging playbook, section 15** in [rules/14-15-practice.md](rules/14-15-practice.md) - read
   only the first five items. **Item 1 solves more mysteries than the rest combined: if something you
   just wrote appears to do nothing, do an editor-closed build before anything else.**

## The four pillars, in one line each

1. **Separation of concerns** - each class does one job.
2. **Loose coupling** - systems talk through delegates, interfaces and subsystems.
3. **Data-driven design** - what a designer tunes lives in data, not code.
4. **Event-driven first** - delegates and timers; Tick only with approval.

When two good rules pull against each other, the higher pillar wins, and you raise it in a
`CONFLICT` block (14.1) before writing code.

## Week one - the traps that cost the most time

Section 16 is every engine behaviour that fails silently. These are the ones new people hit first:

| Trap | Section |
|---|---|
| `SpawnActor<T>(T::StaticClass())` skips the Blueprint, so every Blueprint-set property is null | 16.3 |
| `TSoftObjectPtr::IsValid()` means "already loaded", not "assigned" | 16.3 |
| A hard `OpenLevel` destroys and recreates the PlayerController | 16.1 |
| `SetActorLocationAndRotation` leaves velocity at zero, so animation reads idle | 16.2 |
| A widget in an inactive switcher slot has zero size, permanently | 16.4 |
| `ReplicatedUsing` does not fire on the machine that set the value | 16.6 |
| A `TWeakObjectPtr` resolved off the game thread races the garbage collector | 16.5 |
| An actor's label does not exist in a cooked build | 16.3 |

## Where things are

- **What to read for the task in front of you** - the table in the [README](README.md).
- **Why a rule exists** - [why.md](why.md), by section number. Read it before arguing with a rule.
- **Something looks wrong** - it may be. Raise a `CONFLICT` block (14.1); a rule nobody can follow is
  a defect in the standard, and the owner fixes it.

## The two rules that surprise experienced Unreal developers

- **Members, locals and parameters are camelCase** (4.1) - Epic uses PascalCase. This is deliberate,
  and why.md 4.1 has the argument. The tooling flags it, so you will not have to remember it for long.
- **Comments are two lines unless they earn more** (5.2) - write the why, not the what.
