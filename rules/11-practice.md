# 14-15. Working style and debugging

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

---

## 14. Working style

### 14.1 How we work

- **Plan before implementing.** Full conflict analysis before code; identify structural mismatches
  before writing a line.
- **Diagnosis before code.** Root cause identified and agreed before a fix is written.
- **Flag conflicts in a `CONFLICT` block, before any code.** When new work conflicts with a pillar, a
  rule or the existing architecture - or an include-path or ordering problem changes the plan - raise
  it in this format and wait for a written answer:

  ```
  CONFLICT
  Rule:      <pillar or section, e.g. Pillar 2 / 9.4>
  Existing:  <what the code or design does now>
  Requested: <what the change needs>
  Options:   A) <approach> - <trade-off>
             B) <approach> - <trade-off>
  Recommend: <A or B, and why>
  ```

  People and assistants (14.2) use the same block.
- **Present architectural forks as explicit Option A / Option B with trade-offs** - before the
  decision.
- **Explain the why** of any pattern you introduce - in the PR, the review, the doc.
- **Do not assume a concept is understood because it appears in existing code.**

### 14.2 Working with an AI assistant

> **Ask for the plan first. If you can restate it and you agree with it, let the assistant do the
> whole thing. If you cannot, make it work one file at a time.**

- **One file at a time** - write, stop, show, wait - for an unfamiliar system, engine area or approach.
- **The whole thing in one go** when you understand and agree with the plan.
- The same calibration applies to anything hard to reverse: a batch rename, a refactor across many
  files, anything touching content.
- **You own the output.** Read every line an assistant wrote before committing it.
- **Every rule applies identically to assistant-written code.** Give the assistant the rule files
  (README) so it starts from the standard.
- **Never commit a large diff you did not understand.**

### 14.3 Source control

- **Binary assets go through Git LFS** - `.uasset`, `.umap`, source art and audio - configured in
  `.gitattributes` before the first asset is committed.
- **Lock a `.uasset` or `.umap` before you edit it** (`git lfs lock`, or the editor's source-control
  integration).
- **Fix up redirectors after a move or rename** (right-click the folder > Fix Up Redirectors) and commit
  the fix-up with the move.
- **Never commit** `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/` or `.vs/`.
- **Git + LFS with locking for a small, engineering-led team; Perforce with exclusive checkout for a
  team with artists editing daily.** Decide in the README. Keep feature branches short.
- **One File Per Actor** ends level merge conflicts and creates thousands of small files; budget for
  that on Git.
- **Rename a C++ class or property with a Core Redirect in the same commit** (3.8).
- **Commit messages:** an imperative summary under 72 characters, prefixed by the system -
  `Quest: Reset transition phase on map arrival`. A body when the why is not obvious. One logical
  change per commit.

### 14.4 Automated tests

- **Pure logic gets an automation test** - `IMPLEMENT_SIMPLE_AUTOMATION_TEST` or the spec form
  (`BEGIN_DEFINE_SPEC`), named `<Project>.<System>.<Case>`, run from the Session Frontend or
  `Automation RunTests`.
- **Test pure logic first** - damage rules, inventory rules, save migration, state machines, parsers,
  economy maths, anything with a bug history.
- **Gameplay flow gets a functional test** - an `AFunctionalTest` actor in a dedicated test map that
  runs the real systems and calls `FinishTest` - for flows that have broken before, not for coverage.
- **A bug fix adds the test that would have caught it**, wherever the bug is testable.
- **Tests run before a merge to the main branch.** A failing test blocks the merge.

### 14.5 Continuous integration

Every gate fails the build.

| Tier | Time | Contents |
|---|---|---|
| Every commit | ~10 min | Compile (editor and game), automation tests, asset validators (18), reference budget check |
| Nightly | 1-2 h | Cook and package, dedicated server build, perf and memory against budget (13.9), functional tests |
| Weekly | Longer | Test and Shipping builds on every platform, a full clean cook, loading archived saves from every shipped version (9.14) |

- **Commandlets in CI return non-zero on failure** and never prompt, open a dialog or wait for input -
  run them with `-unattended -nopause -nosplash`.
- **Archive symbols for every build from day one**, and bake the version and changelist into the
  binary.
- **Instrument telemetry before you need it** - frame-time percentiles, crash rate, load times - and
  collect nothing you cannot name a decision for.
- **Pre-ship, every check runs in a packaged Shipping build on the lowest target platform.**

---

## 15. Debugging playbook

Before you spend an hour on a mystery, work down this list:

1. **Did you do the right kind of build?** Live Coding is for function bodies only. **Any header
   change** - especially new or changed `UPROPERTY` / `UFUNCTION` / `USTRUCT` / `UENUM`, delegate
   declarations, new classes, class layout, or constructor defaults - needs **a normal build with the
   editor closed**. A `.Build.cs`, `.uproject` or `.uplugin` module change also needs **regenerated
   project files**. **If something you just wrote appears to do nothing, do an editor-closed build
   before you debug anything else.** Deleting `Intermediate/` and `Binaries/` is a last resort for a
   corrupted build, not a routine step.
2. **Is the property null because you spawned raw C++?** `SpawnActor<T>(T::StaticClass())` bypasses
   the Blueprint CDO.
3. **Is the delegate the right kind?** Non-dynamic delegates are invisible to Blueprint.
4. **Is the widget in an inactive switcher slot?** Then its geometry is zero, permanently.
5. **Did the PlayerController get destroyed?** Any hard `OpenLevel` recreates it.
6. **Is it a soft pointer you gated on `IsValid()`?** Then it never loaded.
7. **Is the GameplayTag on the branch you think it is?** Matching is strict.
8. **Is the data actually authored?** Check the asset, not the code - then add a validation pass.

**If it is intermittent, or it crashes with a stack trace that makes no sense:**

9. **Is a lambda capturing a raw `UObject*` or capturing by reference?** Both are use-after-free.
10. **Is a background thread touching a `UObject`?** Including resolving a weak pointer.
11. **Is an async or load callback guarding `IsValid(this)`** before it touches any member, and
    checking `GetWorld()` before anything world-dependent?
12. **Does a timer or delegate outlive its owner?**

**If it works for you but not for someone else, on a networked project:**

13. **Is the state change guarded by `HasAuthority()`?**
14. **Is `bReplicates` set, and was it set in the constructor?**
15. **Is the property registered in `GetLifetimeReplicatedProps`?** By default an unregistered
    property is auto-registered with no condition - it replicates to everyone. With
    auto-registration off it never replicates. Neither warns unless the project enabled the ensure
    (11.3).
16. **Is an `OnRep_` handler expected to run on the server?** It does not - call it explicitly there.
17. **Does the client own the actor** it is calling a `Server` RPC on? For a multicast, is the actor
    replicating and net-relevant to that client?
18. **Was the initial value set in `BeginPlay`?** Move it to the constructor or
    `PostInitializeComponents`.

**If it works in the editor but not in a packaged build:**

19. **Is the asset referenced from anything the cooker can see?** Register its type with the Asset
    Manager (13.3).
20. **Is it `WITH_EDITOR`-only code, or an editor-only module?**
21. **Is logic living inside a `check()`?** Its expression is not evaluated in Shipping (3.9).
22. **Did you test the actual configuration?** Development and Shipping differ in asserts, logging and
    optimisation.

**Always:**

23. **Check the log.** Filter the Output Log by the system's category before you set a breakpoint.
24. **Suspect a missing `UPROPERTY` or a dangling pointer?** Run with `gc.CollectGarbageEveryFrame 1`.
25. **Slow, or hitching?** Start from `stat unit` (13.2) and the hitch table (13.5), not from the code
    you suspect.
