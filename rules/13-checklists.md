# 17-18. Checklists

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

---

## 17. Pre-commit checklist

**Build and verify**

- [ ] It compiles, and you did an **editor-closed build** (not Live Coding) if you touched a header,
      a delegate declaration, a constructor default or a new class - plus **regenerated project
      files** for a `.Build.cs` change (15, item 1)
- [ ] You **played it in PIE** - not just compiled it
- [ ] No new warnings in the Output Log from your code
- [ ] If an assistant wrote any of it, **you have read every line** and it meets every rule below
      (14.2)

**C++ structure**

- [ ] Header sections in the mandatory order, variables before functions
- [ ] No inline initialisation in any `.h` - defaults are in the constructor, structs included
      (`static constexpr`, default arguments and enumerator values excepted - 3.2)
- [ ] Every struct with number, bool, enum or pointer fields has a constructor that sets them (4.6)
- [ ] `TObjectPtr` on every `UPROPERTY` object reference; every `UObject*` member is a `UPROPERTY`
      or `TWeakObjectPtr`; no `AddToRoot` (3.8)
- [ ] `UObject` pointers tested with `IsValid`, not `!= nullptr` (3.4)
- [ ] No logic inside `check()` (3.9)
- [ ] Nothing world- or asset-dependent in a constructor; `OnConstruction` is idempotent (3.2, 3.11)
- [ ] Forward declares in headers, includes in the `.cpp`, nothing implicit
- [ ] Soft references by default; every hard reference is deliberate
- [ ] `const` correct; no magic numbers; any new Tick was approved first, is commented, and
      self-disables; no empty or polling tick left registered (3.7, 3.12)
- [ ] Debug draws inside `#if ENABLE_DRAW_DEBUG` and behind a runtime toggle (3.7)

**Naming**

- [ ] Variables and parameters `camelCase`; functions `PascalCase`; booleans `b`-prefixed
- [ ] Type prefixes correct: `A` `U` `F` `I` `E` `S` `T`
- [ ] Function names start with a verb from the established vocabulary (4.3)
- [ ] Enumerators PascalCase, no prefix; enumerator 0 is safe/`Unknown`
- [ ] Only approved short names used (4.8)
- [ ] File name matches the class name without its prefix

**Categories**

- [ ] Designer-facing properties have an `Initialize|...` Category
- [ ] Debug toggles are under `Initialize|Debug`, not a top-level `Debug`
- [ ] Runtime-only readouts are `Runtime|...`
- [ ] Designer-facing numbers carry `ClampMin` / `ClampMax` and `ForceUnits` (3.3)

**Architecture**

- [ ] The new state has exactly one owner - you did not add a second path that completes it (9.4)
- [ ] No `switch` on slot, item type or identity - a GameplayTag-keyed map or polymorphic
      DataAssets instead (9.2)
- [ ] Adding the *second* one of this thing is a content change, not a code change (9.2)
- [ ] Service logic is in a GameInstance or World subsystem; GameMode holds only match rules (9.1)
- [ ] Any conflict with a pillar or rule was raised in a `CONFLICT` block before the code (14.1)
- [ ] Abilities live in components; player `Do*` handlers only forward input (9.9)
- [ ] New state sits in its home per the ownership map (9.11); no `GetPlayerController(World, 0)`
- [ ] Any design pattern used is in the catalogue (9.10), or was agreed in a `CONFLICT` block
- [ ] Anything that must survive a map load lives on the GameInstance side (9.5)

**Comments**

- [ ] Every new `UPROPERTY` / `UFUNCTION` / enumerator has a Doxygen comment
- [ ] **Every comment is two lines or fewer**
- [ ] Any 3+ line comment you touched has been rewritten down to two
- [ ] Comments explain *why*, not *what*
- [ ] No emojis. No `U+FFFD`. No commented-out code. No anonymous `TODO`.

**Logging**

- [ ] Category declared with `DEFINE_LOG_CATEGORY_STATIC` in the `.cpp` unless several files share
      it (6.2), named `Log<Project><Domain>`
- [ ] `UE_LOGFMT`, not `UE_LOG`, in new and modified lines, with arguments in token order (6.5)
- [ ] Every line has class, function, description and a context value - `GetNameSafe`, never
      `GetName()`; enums via `UEnum::GetValueAsString` (6.1)
- [ ] Every failure guard-clause return logs; expected early-outs are `Verbose` or silent (6.6)
- [ ] Correct severity; nothing at `Log` level inside a per-frame path

**Async and threading**

- [ ] No `UObject` accessed, created or destroyed off the Game Thread - weak-pointer resolution
      included
- [ ] Every lambda that outlives the frame captures `TWeakObjectPtr`, never a raw `UObject*` and
      never by reference
- [ ] Every async and load callback resolves the weak pointer once, null-checks it, and checks
      `GetWorld()` before touching anything world-dependent
- [ ] Every `FTimerHandle` stored and cleared in teardown; every delegate unbound
- [ ] Delegates bound from a `UObject` use `AddUObject` / `AddWeakLambda`, never `AddLambda`
      capturing `this` (9.3)
- [ ] Every async load stores its handle and has a fallback for the not-loaded window; no gameplay
      path calls `LoadSynchronous` (10.3)
- [ ] Worker-thread code follows gather, compute, apply; AnimBP derivation is in the thread-safe
      update (10.4, 10.6)
- [ ] Any new `FRunnable` is stopped and joined from its owner's teardown

**Networking** (if the project replicates)

- [ ] Every replicated state change guarded by `HasAuthority()`
- [ ] `bReplicates` set in the constructor, not later
- [ ] Every `UPROPERTY(Replicated*)` registered in `GetLifetimeReplicatedProps`, and the project
      runs with the missing-registration ensure on (11.3)
- [ ] `Super::GetLifetimeReplicatedProps` called; state a late joiner needs is a property, not an
      RPC (11.3)
- [ ] Server RPCs carry intent, never outcome, and `_Implementation` re-checks the rules (11.4)
- [ ] Dormant actors are flushed before they change (11.5)
- [ ] Replication condition chosen deliberately - `COND_OwnerOnly` where only the owner needs it
- [ ] `OnRep_` named after its property, and called explicitly on the authority where the response is
      needed there too
- [ ] Initial replicated values set in the constructor or `PostInitializeComponents`, not `BeginPlay`
- [ ] Every `Server` RPC has `WithValidation`, and the validation actually validates
- [ ] Reliable used only where it is required; cosmetic and frequent traffic is unreliable
- [ ] `SetNetUpdateFrequency` set for any new replicating actor - the 100 Hz default is almost never
      right (11.5)
- [ ] `bAlwaysRelevant` left false unless the actor genuinely is
- [ ] RPC prefixes correct: `Server` / `Client` / `Multicast` / `OnRep_` (11.6)
- [ ] Tested with two clients, and once as a dedicated server rather than only a listen server

**Performance**

- [ ] A new subsystem has its CPU scope, counters, CSV stat and LLM tag (13.6)
- [ ] Any optimisation has a before and an after capture, from a Test build on the target (13.2)
- [ ] Anything numerous and short-lived is pooled (13.4)

**Content**

- [ ] New assets carry the correct type prefix and PascalCase name (7.1-7.3)
- [ ] No vendor, tool, scratch or history names (`_Final`, `_v2`, `_test`)
- [ ] Any prototype or test Blueprint is named `BP_TEMP_` / kept in `TEMP/`, and nothing shipping
      references it
- [ ] Blueprint variables have tooltips and categories; graphs have comment boxes
- [ ] No new hard references to heavy assets in a widely-instanced Blueprint
- [ ] Widget bind names are `<role>_<Type>`, identical in UMG and C++ (7.4)
- [ ] Player-facing text is `FText` - `LOCTEXT` and `FText::Format`, no concatenation (12.5)
- [ ] New DataAsset types override `IsDataValid` and are registered with the Asset Manager (6.7,
      13.3)
- [ ] Binary assets you edited were locked; redirectors fixed up after any move (14.3)

**Docs**

- [ ] Docs updated in the same commit if you changed a documented system

**Reviewer's scan** - what a general C++ reviewer misses in Unreal code:

a `UObject*` member without `UPROPERTY` - `!= nullptr` instead of `IsValid` - gameplay in a
constructor - a missing `Super::` call - an unbound delegate - Tick that should be an event - a
runtime component without `RegisterComponent` - a mutation without `HasAuthority` - an unvalidated
Server RPC - a multicast where state was needed - a dormancy change without a flush - a new hard
reference - `LoadSynchronous` in gameplay - a dropped streamable handle - game rules in Blueprint -
an expensive `BlueprintPure` - a call to `_Implementation` - a `UObject` touched off the game thread -
`check()` with a side effect - `FText::FromString` on player text - an unversioned save format -
`GetPlayerController(World, 0)`.

---

## 18. Adopting this on a new project

**Pin these before the first feature**

- [ ] Module split decided (`<Project>` / `<Project>Online`) - 1.1
- [ ] Source folder skeleton in place - 1.3
- [ ] Content root `Content/_<Project>/` created, folder skeleton in place - 2.1
- [ ] Project short name pinned, for class infixes and short variable names - 4.4, 4.8
- [ ] Log category naming pinned: `Log<Project><Domain>`, `DEFINE_LOG_CATEGORY_STATIC` by default - 6.2
- [ ] GameplayTag root namespaces agreed - 4.10
- [ ] Console command namespace pinned: `<Project>.<system>.<verb>`, lowercased - 4.11
- [ ] A `TEMP/` or `Developers/` content folder created, so prototypes have somewhere legitimate to
      live - 8.2
- [ ] **Replication decided and written down in the README** - "this project replicates" or "this
      project is single-player" - 11.1
- [ ] On a replicated project: push model and Iris decided, and the missing-registration CVars set
      in `DefaultEngine.ini` - 11.3, 11.8
- [ ] Git LFS and `.gitattributes` in place before the first asset commit; locking on for `.uasset`
      and `.umap` - 14.3
- [ ] Data-driven asset types registered as Primary Asset Types - 13.3
- [ ] Frame budget per target written down, with line items and owners - 13.2
- [ ] Version control chosen (Git + LFS or Perforce) - 14.3
- [ ] CI tiers in place: every commit, nightly, weekly - 14.5
- [ ] A project `README.md` that fills in every `<Project>` placeholder, lists every project override
      with its section number and reason, and links back to this standard

**Enforcement tooling** - so the mechanical rules are checked by a tool, not by memory

- [ ] [`tooling/.clang-format`](../tooling/.clang-format) and
      [`tooling/.editorconfig`](../tooling/.editorconfig) copied to the project root (3.10)
- [ ] A `.clang-tidy` with `readability-identifier-naming` for the case rules in 4.1, as far as it
      can express them
- [ ] [`tooling/Validators/AssetNamingValidator`](../tooling/README.md) installed in the project's
      editor module. It fails any asset under `Content/_<Project>/` without its 7.1 prefix or with a
      non-PascalCase name, on save and in CI (14.5)
- [ ] **Blueprint lint**, as further validators when the project needs them: `Event Tick` without an
      approval comment (3.12), a node-count budget per graph, `Cast To` a Blueprint class (8.3), hard
      references past the reference budget (13.3)
- [ ] A reference-budget commandlet that fails CI when an asset's hard-dependency size passes its
      budget - set budgets just above today's values and ratchet them down
- [ ] The rules no tool can check - header order, comment content, the pillars - listed in the pull
      request template

**Ongoing**

- [ ] A project-level `CLAUDE.md` or equivalent that imports the rule files the project needs (see
      the README), so assistants follow the same rules as people
- [ ] A **canonical examples** list in the project README: for each recurring pattern, the real class
      that implements it well - "countdowns: follow the time-bomb timer on the ball actor"
- [ ] A living document of project-specific decisions and traps - that project's section 16. Every
      trap you hit that is not in this standard goes there; the genuinely engine-general ones come back
      here.
