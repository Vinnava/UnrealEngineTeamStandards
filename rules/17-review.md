# 17.2-17.4 Review list, reviewer's scan, and the tool backlog

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

**Not a per-commit ritual** - the commit gate is [17-gate.md](17-gate.md). Read this when you are
reviewing someone's work, when a feature lands, or when you are new and building the habit.

---

### 17.2 The full review list

**Not a per-commit ritual.** Read it when you are reviewing someone's work, when a feature lands, or
when you are new and building the habit. Items marked **[tool]** are already enforced mechanically
(18) - if one of those fails, the fix is the tool's configuration, not more human attention.

**C++ structure**

- [ ] Header sections in the mandatory order, variables before functions (3.1)
- [ ] No inline initialisation in any `.h` - defaults are in the constructor, structs included
      (`static constexpr`, default arguments and enumerator values excepted - 3.2)
- [ ] Every struct with number, bool, enum or pointer fields has a constructor that sets them (4.6)
- [ ] `TObjectPtr` on every `UPROPERTY` object reference; no `AddToRoot` (3.8)
- [ ] `UObject` pointers tested with `IsValid`, not `!= nullptr` (3.4)
- [ ] No logic inside `check()` (3.9)
- [ ] Nothing world- or asset-dependent in a constructor; `OnConstruction` is idempotent (3.2, 3.11)
- [ ] Forward declares in headers, includes in the `.cpp`, nothing implicit (3.4)
- [ ] `const` correct; no magic numbers; any new Tick was approved first, is commented, and
      self-disables; no empty or polling tick left registered (3.7, 3.12)
- [ ] Debug draws inside `#if ENABLE_DRAW_DEBUG` and behind a runtime toggle (3.7)
- [ ] **[tool]** Formatting - braces, indentation, line length (3.10, `.clang-format`)

**Naming**

- [ ] **[tool]** Variables and parameters `camelCase`; functions `PascalCase`; constants and
      enumerators `PascalCase` (4.1, `.clang-tidy`)
- [ ] Booleans `b`-prefixed, named for the true state (4.2)
- [ ] Delegate members are PascalCase `On*`, matching the Blueprint dispatcher (4.7, 7.4)
- [ ] Type prefixes correct: `A` `U` `F` `I` `E` `S` `T` (4.1)
- [ ] Function names start with a verb from the established vocabulary (4.3)
- [ ] Enumerator 0 is safe, inert or `Unknown` (4.5)
- [ ] Only approved short names used (4.8)
- [ ] File name matches the class name without its prefix (4.9)

**Categories**

- [ ] Designer-facing properties have an `Initialize|...` Category; debug toggles under
      `Initialize|Debug`, not a top-level `Debug` (3.3)
- [ ] Runtime-only readouts are `Runtime|...` (3.3)
- [ ] Designer-facing numbers carry `ClampMin` / `ClampMax` and `ForceUnits` (3.3)

**Architecture**

- [ ] No `switch` on slot, item type or identity - a GameplayTag-keyed map or polymorphic
      DataAssets instead (9.2)
- [ ] Service logic is in a GameInstance or World subsystem; GameMode holds only match rules (9.1)
- [ ] Abilities live in components; player `Do*` handlers only forward input (9.9)
- [ ] New state sits in its home per the ownership map (9.11); no `GetPlayerController(World, 0)`
- [ ] Any design pattern used is in the catalogue (9.10), or was agreed in a `CONFLICT` block
- [ ] Anything that must survive a map load lives on the GameInstance side (9.5)

**Comments**

- [ ] Every new `UPROPERTY` / `UFUNCTION` / enumerator has a Doxygen comment (5.1)
- [ ] Comments are two lines, or earn the space they take (5.2)
- [ ] Comments explain *why*, not *what* (5.3)
- [ ] **[tool]** No emojis, no `U+FFFD` (5.5, CI grep - 17.4)
- [ ] No commented-out code; no anonymous `TODO` (5.5)

**Logging**

- [ ] Category declared with `DEFINE_LOG_CATEGORY_STATIC` in the `.cpp` unless several files share
      it, named `Log<Project><Domain>` (6.2)
- [ ] `UE_LOGFMT`, not `UE_LOG`, in new and modified lines, with arguments in token order (6.5)
- [ ] Every line has class, function, description and a context value - `GetNameSafe`, never
      `GetName()`; enums via `UEnum::GetValueAsString` (6.1)
- [ ] Every failure guard-clause return logs; expected early-outs are `Verbose` or silent (6.6)
- [ ] Correct severity; nothing at `Log` level inside a per-frame path (6.3, 6.6)

**Async and threading**

- [ ] Every async and load callback resolves the weak pointer once, null-checks it, and checks
      `GetWorld()` before touching anything world-dependent (10.2)
- [ ] Delegates bound from a `UObject` use `AddUObject` / `AddWeakLambda`, never `AddLambda`
      capturing `this` (9.3)
- [ ] Every async load stores its handle and has a fallback for the not-loaded window; no gameplay
      path calls `LoadSynchronous` (10.3)
- [ ] Worker-thread code follows gather, compute, apply; AnimBP derivation is in the thread-safe
      update (10.4, 10.6)
- [ ] Any new `FRunnable` is stopped and joined from its owner's teardown (10.4)

**Networking** (if the project replicates)

- [ ] `bReplicates` set in the constructor, not later (11.5, section 16)
- [ ] Every `UPROPERTY(Replicated*)` registered in `GetLifetimeReplicatedProps`, and the project
      runs with the missing-registration ensure on (11.3)
- [ ] `Super::GetLifetimeReplicatedProps` called; state a late joiner needs is a property, not an
      RPC (11.3)
- [ ] Server RPCs carry intent, never outcome, and `_Implementation` re-checks the rules (11.4)
- [ ] Dormant actors are flushed before they change (11.5)
- [ ] Replication condition chosen deliberately - `COND_OwnerOnly` where only the owner needs it
      (11.3)
- [ ] `OnRep_` named after its property, and called explicitly on the authority where the response is
      needed there too (11.3, 11.6)
- [ ] Initial replicated values set in the constructor or `PostInitializeComponents`, not
      `BeginPlay` (11.5, section 16)
- [ ] Reliable used only where it is required; cosmetic and frequent traffic is unreliable (11.4)
- [ ] `SetNetUpdateFrequency` set for any new replicating actor - the 100 Hz default is almost never
      right (11.5)
- [ ] `bAlwaysRelevant` left false unless the actor genuinely is (11.5)
- [ ] **[tool]** RPC prefixes correct: `Server` / `Client` / `Multicast` / `OnRep_` (11.6,
      `.clang-tidy` partially)
- [ ] Tested with two clients, and once as a dedicated server rather than only a listen server (11.7)

**Performance**

- [ ] A new subsystem has its CPU scope, counters, CSV stat and LLM tag (13.6)
- [ ] Any optimisation has a before and an after capture, from a Test build on the target (13.2)
- [ ] Anything numerous and short-lived is pooled (13.4)

**Content**

- [ ] **[tool]** New assets carry the correct type prefix and PascalCase name (7.1-7.3,
      `AssetNamingValidator`)
- [ ] No vendor, tool, scratch or history names (`_Final`, `_v2`, `_test`) (7.3)
- [ ] Any prototype or test Blueprint is named `BP_TEMP_` / kept in `TEMP/`, and nothing shipping
      references it (8.2)
- [ ] Blueprint variables have tooltips and categories; graphs have comment boxes (8.3)
- [ ] Widget bind names are `<role>_<Type>`, identical in UMG and C++ (7.4)
- [ ] New DataAsset types override `IsDataValid` and are registered with the Asset Manager (6.7,
      13.3)
- [ ] Binary assets you edited were locked; redirectors fixed up after any move (14.3)

**Audio, accessibility and online** (where the change touches them)

- [ ] No sound played by hard asset reference from gameplay; every new sound has a concurrency group
      with a cap (19.1, 19.3)
- [ ] Every new spoken line has a subtitle; nothing communicates by colour alone (20.2, 20.3)
- [ ] New player-facing strings come from a string table and format with named arguments (20.8)
- [ ] Every new request has a timeout, a retry policy, a cancellation path and a defined failure
      behaviour; no secret and no token is logged or committed (21.2, 21.4)

**Docs**

- [ ] Docs updated in the same commit if you changed a documented system, and this standard itself
      if you found a rule that is wrong (14.1)

### 17.3 Reviewer's scan

What a general C++ reviewer misses in Unreal code:

a `UObject*` member without `UPROPERTY` - `!= nullptr` instead of `IsValid` - gameplay in a
constructor - a missing `Super::` call - an unbound delegate - Tick that should be an event - a
runtime component without `RegisterComponent` - a mutation without `HasAuthority` - an unvalidated
Server RPC - a multicast where state was needed - a dormancy change without a flush - a new hard
reference - `LoadSynchronous` in gameplay - a dropped streamable handle - game rules in Blueprint -
an expensive `BlueprintPure` - a call to `_Implementation` - a `UObject` touched off the game thread -
`check()` with a side effect - `FText::FromString` on player text - an unversioned save format -
`GetPlayerController(World, 0)` - an uncapped sound - a hard-coded key glyph - a logged token.

### 17.4 What should be a tool

**A checklist item that a tool could check is a defect in the tooling, not a reason to read harder.**
This is the backlog; each entry moves out of 17.2 when it lands.

| Check | How |
|---|---|
| Emojis and `U+FFFD` in source, content and commit messages (5.5) | A CI grep, and a commit hook |
| `LogTemp` in committed code (6.2) | A CI grep |
| `UE_LOG` in a file that also uses `UE_LOGFMT` (6.5) | A CI grep, warning only |
| Header section order (3.1) | A clang-tidy style check, or a small parser |
| A `UObject*` member without `UPROPERTY` (3.8) | UHT already knows the reflected set - a commandlet can diff it |
| `Event Tick` in a Blueprint with no approval comment (3.12) | A `UEditorValidatorBase` subclass (18) |
| `Cast To` a Blueprint class (8.3) | The same |
| Hard-reference size past an asset's budget (13.3) | A reference-budget commandlet (18) |
| Missing `ClampMin` / `ForceUnits` on a designer-facing number (3.3) | A reflection walk in a validator |
| A sound with no concurrency group (19.3) | An asset validator |
| A `UPROPERTY` or `UFUNCTION` with no comment (5.1) | A reflection walk, warning only |

---
