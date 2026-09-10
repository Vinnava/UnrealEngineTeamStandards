# Unreal Engine Team Standards

The rules, conventions and best practices every developer on this team follows, on every Unreal
project.

This document is **project-agnostic**. Nothing in it depends on a particular game, module or
feature - it is the standard we carry from one project to the next. Where a project needs to pin
something down (its module name, its content root, its short prefix), those are marked as
`<Project>` placeholders for that project's own README to fill in.

**Version 1.2** - changelog at the end. Written against **Unreal Engine 5.x**; every claim about
engine behaviour was checked against **UE 5.7** source, and the defaults that matter re-checked in
**5.8**. Where a rule depends on the engine version, it says so.

**Placeholders.** `<Project>` is the only placeholder. It stands for the project's short name -
PascalCase in class, module and folder names, lowercased where the convention is lowercase
(variables, console commands). Code examples use **`Game`** as a concrete stand-in: `LogGameQuest`,
`GAME_API`, `gameGI`, `game.quest.launch`.

**Which document wins.** When rules disagree, the higher item wins:

1. **The engine.** What Unreal actually does, verified in its source, beats every document - this one
   included. A rule here that fights the engine is a defect here.
2. **A project's written override** - listed in that project's README with the section number and
   the reason. It wins inside that project only.
3. **This document.**
4. **A project's other documents** - its `CLAUDE.md`, rule files, wiki. They may add rules and
   project detail; where they contradict this document without a written override, this document
   wins and the project document is the defect.
5. **Existing code and habit.** "The codebase already does it this way" is evidence of a past
   decision, not permission.

An unwritten deviation is a defect, not an override.

**Sections 1 and 2 tell you where things go. Sections 3 through 8 are the core standard - read them
before you write your first line of code. Sections 9 through 13 are per-system rules; read the one
you are about to work in. Sections 14 through 18 are practice - the playbook, the traps, and the
checklist you run before every commit.**

Nothing here is aspirational. If a rule in this document is wrong, or you cannot follow it, that is
a defect in the document - fix it (see the closing note) rather than quietly working around it.

---

## Architecture pillars

Four pillars, **ranked**. Every rule in this document serves one of them. When two rules pull against
each other, or a request conflicts with a rule, **the higher-ranked pillar decides** - and the
conflict is raised in a `CONFLICT` block (14.1) before any code is written.

1. **Separation of concerns** - each class, component and system does one job (1.3, 9.8).
2. **Loose coupling** - systems talk through delegates, interfaces and subsystems, never by reaching
   into each other's classes (9.3, 9.7).
3. **Data-driven design** - behaviour a designer tunes lives in DataAssets, tags and settings, not in
   code (9.2, 9.6).
4. **Event-driven first, Tick when right** - delegates, events and timers wherever they fit; Tick
   only with approval (3.7, 3.12, 10.5).

The pillars say *what* to optimise for. The pattern catalogue in 9.10 says *how* - each approved
pattern names what it serves.

---

## Contents

| # | Section | Group | Read it |
|---|---|---|---|
| 1 | Project and module structure | Layout | Before you add a file |
| 2 | Content folder structure | Layout | Before you add an asset |
| 3 | **C++ coding standards** | Core | Before your first line of code |
| 4 | **C++ naming conventions** | Core | Before your first line of code |
| 5 | **Comment standard** | Core | Before your first line of code |
| 6 | **Logging standard** | Core | Before your first line of code |
| 7 | **Blueprint and content naming conventions** | Core | Before your first asset |
| 8 | **Blueprint discipline** | Core | Before your first Blueprint |
| 9 | Architecture rules | Systems | Before you design a system |
| 10 | Async and threading | Systems | Before anything async |
| 11 | Networking and replication | Systems | Only if the project replicates |
| 12 | UMG and Slate rules | Systems | Before you build UI |
| 13 | Performance and platform | Systems | Before you optimise |
| 14 | Working style | Practice | Once |
| 15 | Debugging playbook | Practice | When something is wrong |
| 16 | Known engine traps | Practice | Before touching a named system |
| 17 | Pre-commit checklist | Practice | Every commit |
| 18 | Adopting this on a new project | Practice | Starting a project |

---

## 1. Project and module structure

### 1.1 Modules

Split runtime code from anything that talks to a backend or an external service:

| Module | Contains |
|---|---|
| `<Project>` | Main game module - gameplay, characters, UI, subsystems |
| `<Project>Online` | HTTP, JSON, auth, backend service classes, wire types |
| `<Project>Editor` | Editor-only tooling, if any |

The split is not ceremony. It keeps `HTTP`/`Json` dependencies out of the gameplay module and makes
the wire contract reviewable in isolation. It also limits rebuild scope: a change confined to the
online module's `.cpp` files does not recompile the game module. A change to its **public headers**
still does - which is a reason to keep the public surface of that module small.

### 1.2 Build.cs discipline

- **Every dependency you add gets a one-line comment saying which feature needs it.** A dependency
  list nobody can prune is a dependency list that only grows.

```csharp
PrivateDependencyModuleNames.AddRange(new string[]
{
    "AIModule",
    "Slate",
    "SlateCore",
    // FX steps spawn Niagara systems as fire-and-forget beats
    "Niagara",
    // Voice - mic capture and procedural audio playback
    "AudioCapture",
});
```

- Prefer `PrivateDependencyModuleNames` unless a public header genuinely exposes the type.
- Platform-conditional dependencies go in an `if (Target.Platform == ...)` block, not the common list.
- **Any `.Build.cs` change requires regenerating project files and a full build with the editor
  closed** - Live Coding cannot apply it. Full trigger list: section 15, item 1.

### 1.3 Source folder layout

Folder path mirrors the class's role, not its feature. A reader should be able to guess where a
class lives from what it *is*:

```
Source/<Project>/
  Actor/                 placed and spawned actors, triggers, interactables
  Character/             Player, NPC hierarchies
  Components/            ActorComponents, grouped by owner
  Core/                  cross-cutting core systems
  Data/
    DataAsset/           typed UDataAsset subclasses
    DataTypes/           shared structs and enums, no behaviour
  GameInstance/
    Subsystem/           the service layer
  GameMode/
  Interface/             C++ interfaces
  Save/                  SaveGame classes
  UI/                    all UMG C++ base classes
```

**If you cannot tell which folder a new class belongs in, that usually means the class is doing two
jobs.** Split it.

### 1.4 Compile-time gating

| Code that exists only for | Gate |
|---|---|
| Editor-only member variables | `#if WITH_EDITORONLY_DATA` |
| Editor-only functions and logic | `#if WITH_EDITOR` |
| Development tooling stripped from Shipping | `#if !UE_BUILD_SHIPPING` |
| Dedicated-server-only code | `#if UE_SERVER` |

- **Editor tooling goes in an editor module** (`"Type": "Editor"` in the `.uproject` or `.uplugin`),
  which the cook strips - not in the game module behind `#if WITH_EDITOR`.
- **Every `StartupModule` registration has a matching `ShutdownModule` release.** An unbalanced pair
  crashes on exit and on Live Coding.

### 1.5 Plugins and engine changes

- **A plugin is a product.** It never references game code, talks outward only through interfaces
  and delegates, is configured by data, versions its serialised data - and **works in an empty
  project**. Automate that last test.
- **Before changing engine behaviour, go down this list and stop at the first that works:** design
  around it, an engine extension point, a plugin, a patch, a fork.
- **If you patch the engine,** do it on a branch, wrap every change in `// <PROJECT>-BEGIN` /
  `// <PROJECT>-END` markers, record it in a written patch register, and upstream what you can. The
  cost is paid again at every engine upgrade.

---

## 2. Content folder structure

### 2.1 One root for everything you author

All project content lives under a single, underscore-prefixed root:

```
Content/_<Project>/
```

The leading underscore sorts it to the top of the Content Browser, above every marketplace and
engine folder. Inside it, mirror the source layout where it makes sense:

```
Content/_<Project>/
  Core/          Blueprint counterparts to C++ classes (GM, PC, GI, characters)
    Data/        primary cooked DataAssets
  Characters/
  Maps/
    Blockouts/
    Final/
    SubLevels/
  UI/
  Audio/
  Animation/
  Art/
  Cinematics/
```

### 2.2 Third-party content

Marketplace, Fab, Quixel and MetaHuman content **stays where it landed**. Do not reorganise it and
do not edit it in place - both break the vendor's update path and produce enormous redirector churn.

**If you need to modify a third-party asset, duplicate it into `_<Project>/` first.**

### 2.3 No content outside the root

An asset saved to `Content/` directly, or into a marketplace folder, will be lost track of. If you
find one, move it - and expect a redirector, so do it deliberately, not in the middle of unrelated
work.

---

## 3. C++ coding standards

Enforced on every file. These are not preferences.

### 3.1 Header section order - mandatory

```cpp
private:   // Variables
protected: // Variables
public:    // Variables

private:   // Functions
protected: // Functions
public:    // Functions
```

Variables always before functions, within each access level. **Access level is the only grouping
rule.**

- Never reorder to keep "related" things together.
- Never merge a variables block and a functions block under one specifier.

The reason is diffability and scan speed: being able to read any header in the codebase the same way
is worth more than local cohesion.

### 3.2 Never initialise in the header

All defaults live in the constructor - initializer list or body - in the `.cpp`. Applies to every
type: primitives, pointers, bools, enums, structs.

```cpp
// WRONG
UPROPERTY()
int32 currentHealth = 100;

// CORRECT - MyClass.h
UPROPERTY()
int32 currentHealth;

// CORRECT - MyClass.cpp
AMyClass::AMyClass()
{
    currentHealth = 100;
}
```

Why: an inline default in a header and a constructor assignment can disagree, and the header value
is the one that is easy to miss in review. One place for defaults means one place to look.

Three things are not per-instance defaults, and stay in the header:

- **`static constexpr` constants** - `static constexpr float MaxSpeed = 600.f;` is a compile-time
  value, and 3.7 wants it next to what it governs.
- **Default arguments** - `void Fire(float spread = 0.f);` is part of the signature.
- **Explicit enumerator values** - `Unknown = 0` in a `UENUM`.

**The constructor also builds the class default object** - at editor startup, with no world. So it
sets defaults, creates subobjects and configures tick, and never touches the world, other actors or
assets. `ConstructorHelpers::FObjectFinder` is a blocking load at editor startup; use a soft pointer
set in Blueprint defaults instead. Blueprint defaults override the C++ values set here.

### 3.3 UPROPERTY categories

Every designer-facing `UPROPERTY` (`EditDefaultsOnly`, `EditAnywhere`, `EditInstanceOnly`) needs a
Category. The hierarchy is:

```
"Initialize|<System>|<Subsystem>"
```

**Rule of thumb: if a designer or developer sets it once in Blueprint defaults and it drives system
behaviour, it is an `Initialize` property.**

```cpp
UPROPERTY(EditDefaultsOnly, Category = "Initialize|Movement")
float maxWalkSpeed;

UPROPERTY(EditDefaultsOnly, Category = "Initialize|WidgetClass|Inventory")
TSubclassOf<UInventoryDesktopWidget> inventoryDesktopWidgetClass;

UPROPERTY(EditDefaultsOnly, Category = "Initialize|Socket")
FName weaponAttachSocketName;
```

**Debug toggles are `Initialize` properties too.** A debug draw flag or a verbose-trace switch is
set once in Blueprint defaults and drives behaviour, which is exactly the rule above - so it goes
under the `Initialize` hierarchy, in a `Debug` branch:

```cpp
UPROPERTY(EditDefaultsOnly, Category = "Initialize|Debug")
bool bDrawDebugTraces;

UPROPERTY(EditDefaultsOnly, Category = "Initialize|Debug|Movement")
bool bLogMovementStateChanges;
```

Common branches: `Initialize|Movement`, `Initialize|WidgetClass|<Feature>`, `Initialize|Socket`,
`Initialize|Config`, `Initialize|Debug`.

**Every designer-facing number carries its limits and its unit** - `ClampMin` / `ClampMax` (plus
`UIMin` / `UIMax` where the slider should be narrower than the legal range), and `ForceUnits` wherever
the value has a unit:

```cpp
UPROPERTY(EditDefaultsOnly, Category = "Initialize|Movement",
    meta = (ClampMin = "0.0", ClampMax = "2000.0", ForceUnits = "cm/s"))
float maxWalkSpeed;
```

A designer cannot enter an invalid value, and the Details panel shows what the number means.

**Design the Details panel, too.** Gate dependent properties with `EditCondition` (plus
`EditConditionHides` when the property means nothing otherwise), give struct arrays a
`TitleProperty` so their rows are readable, and restrict gameplay-tag pickers with
`Categories = "Damage.Type"`. A designer should not be able to author a combination the code does
not handle.

**What is not `Initialize`:**

| Kind | Category |
|---|---|
| Runtime state (`VisibleAnywhere`, `BlueprintReadOnly`) | `"Runtime\|..."` |
| Transient pointers cached at `BeginPlay` | No Category needed - they are not designer-facing |

The distinction is authored versus observed. **Anything you set is `Initialize`** - including debug
switches. **Anything you only watch at runtime is `Runtime`.**

### 3.4 Pointers and includes

- **`TObjectPtr<T>` for all `UPROPERTY` object references.** Raw pointers only for locals and
  parameters - never for a member (3.8).
- **Forward declare in headers, include in the `.cpp`.**
- **No implicit includes** - every file includes exactly what it directly uses, and nothing it does
  not. Relying on a transitive include is a build break waiting for someone else's refactor.
- **`.generated.h` is the last include in its header.** UHT rejects anything after it.
- **Export only what other modules call.** Put `<Project>_API` on a class or function another module
  links against, not by reflex - every export is public surface (1.1).
- **Validate before use. Early return on null**, logged as section 6.6 describes.
- **Test `UObject` pointers with `IsValid(ptr)`, not `ptr != nullptr`.** An actor that has been
  destroyed but not yet collected is still non-null and passes a null check; `IsValid` also rejects
  objects marked as garbage. Plain null checks are for non-`UObject` pointers.

### 3.5 Soft vs hard references

**Default to `TSoftObjectPtr` / `TSoftClassPtr` for asset references.**

Reach for a hard reference deliberately - a small, always-needed asset owned by an object that is
only loaded when the asset is needed anyway is a legitimate hard reference. Default to soft; reach
for hard on purpose, not by accident.

An accidental hard reference in a widely-included header pulls a large slice of content into memory
at load, and the cost does not show up anywhere obvious.

Before your first soft-pointer load, read the `IsValid()` trap in section 16 - it is the single most
common soft-pointer bug.

### 3.6 Function style

Guard clauses first, log the failure, early return. Happy path unindented at the bottom:

```cpp
void UQuestRunner::AdvanceToNextStep()
{
    if (!currentStep)
    {
        UE_LOGFMT(LogGameQuestRunner, Error,
            "[{Obj}] [AdvanceToNextStep] currentStep is null",
            GetNameSafe(this));
        return;
    }

    currentStep->Execute(this);
}
```

Note the log form: **`UE_LOGFMT` with descriptive `{Tokens}`**, values passed directly in token order,
with no `TEXT()` wrapper and no `*` dereference. That is the standard for all new code - see section 6.

### 3.7 General quality bar

- **`const` correctness throughout** - parameters, methods, locals.
- **Event-driven first; Tick needs approval** (pillar 4). Reach for a delegate, an event or a timer
  first. When Tick genuinely is the right tool - continuous per-frame work with no natural event -
  flag it in the plan and get it approved **before** writing it. An approved Tick carries a one-line
  comment saying why, and self-disables the moment it has nothing to do. A component ticking for the
  life of the game to check a bool is a real cost at scale. How to tick, when you must: 3.12.
- **Every debug draw sits inside `#if ENABLE_DRAW_DEBUG`** - off in Shipping and Test builds
  (`EngineDefines.h`) - **and behind a runtime bool** under `Initialize|Debug` (3.3), so it compiles
  out of the shipped game and can be switched off in a development build.
- **Countdowns run on a timer, not in Tick.** Arm one `FTimerHandle` for the duration, read
  `GetTimerRemaining` for display, and clear it in teardown (10.5) - rather than accumulating
  `DeltaTime` every frame.
- **No magic numbers.** Named `static const` or `constexpr`, declared next to what they govern.
- **No switch statements on identity.** See section 9.2.
- Prefer composition over deep inheritance chains. A five-level actor hierarchy is a refactor you
  will not be able to afford later.

### 3.8 Object lifetime and garbage collection

The garbage collector only knows about references it can see. Everything else can dangle.

- **Every `UObject*` member is a `UPROPERTY` (`TObjectPtr`) or a `TWeakObjectPtr`.** A raw member
  pointer is invisible to GC: the object can be collected under it, and the pointer still reads
  non-null.
- **Strong versus weak is an ownership decision.** A `UPROPERTY` keeps the object alive; a
  `TWeakObjectPtr` observes it and goes null when it dies. Cache what you do not own - another
  system's actor or widget - as weak.
- **A non-`UObject` class that holds a `UObject` uses `TStrongObjectPtr`**, or derives from
  `FGCObject` and reports its references in `AddReferencedObjects` when it holds several.
- **Never call `AddToRoot`.** A rooted object is never collected, and nothing records who rooted it or
  why. Give the object a real owner instead.
- **Never hold a `UObject` in a `TSharedPtr`.** That gives one object two owners - the GC and a
  reference count.
- **Data in quantity is a `USTRUCT`, not a `UObject`.** GC cost scales with object count, not bytes
  (13.4).

**Which pointer:**

| Situation | Type |
|---|---|
| I own it; it loads with me | `UPROPERTY() TObjectPtr<T>` |
| I observe it; someone else owns it | `TWeakObjectPtr<T>` |
| A heavy asset, loaded on demand | `TSoftObjectPtr<T>` |
| A heavy class, loaded on demand | `TSoftClassPtr<T>` |
| A class to spawn, loaded with me | `TSubclassOf<T>` |
| Held by a plain C++ (non-`UObject`) class | `TStrongObjectPtr<T>` |

**Renames are identity changes.** Renaming a C++ class or a `UPROPERTY` orphans every asset that
saved it - add a Core Redirect (`[CoreRedirects]` in `DefaultEngine.ini`) in the same commit. Never
rename a `CreateDefaultSubobject` name: it is the component's saved identity.

### 3.9 Assertions

| Macro | On failure | In Shipping | Use for |
|---|---|---|---|
| `check(expr)` | Halts | Removed - **`expr` is not evaluated** | Invariants whose failure means continuing would corrupt state |
| `verify(expr)` | Halts | Check removed - **`expr` still evaluated** | The same, when `expr` has a side effect you need |
| `ensure(expr)` | Reports a callstack once, continues | Report removed - **`expr` still evaluated** | Programmer errors the game can survive |

Shipping builds default `DO_CHECK` and `DO_ENSURE` to off (`Build.h`, `AssertionMacros.h`).

- **Never put logic inside `check`.** It is not evaluated in Shipping, so the side effect vanishes.
- **`ensureMsgf` is the default assertion.** Prefer a guarded `ensure` to `check` for anything a
  player can survive -
  `if (!ensure(IsValid(runner))) { return; }`. A crash in Shipping is worse than a missing feature.
- **Keep `check` for true invariants** - `check(IsInGameThread())` (10.1).
- **Expected failures are not assertions.** Bad authored data and network input are logged (6.6,
  6.7), never `ensure`d.

### 3.10 Formatting

- **Opening braces go on their own line** - functions, classes, structs and control flow alike.
  That is Epic's style and the style of every example in this document.
- Indentation, spacing and line length are set by the repository's `.clang-format` (`tooling/.clang-format`: tabs, 120 columns), not
  by memory or preference. Run it on the lines you changed.

### 3.11 Where code goes in the actor lifecycle

| Work | Goes in |
|---|---|
| Defaults, default subobjects, tick configuration | Constructor (3.2) |
| Fixing up loaded data | `PostLoad` |
| Building appearance from properties | `OnConstruction` - **idempotent**, it re-runs on every edit |
| Wiring this actor's own components together | `PostInitializeComponents` |
| Touching other actors or the world; binding delegates | `BeginPlay` |
| Unbinding, clearing timers, cancelling loads | `EndPlay` |
| Releasing native (non-`UObject`) resources | `BeginDestroy` |

- **Components:** `CreateDefaultSubobject` + `SetupAttachment` in the constructor; at runtime,
  `NewObject` + `RegisterComponent` + `AttachToComponent` - an unregistered component does nothing.
  `InitializeComponent` only runs with `bWantsInitializeComponent = true`.
- **An actor that needs configuring before its `BeginPlay`** is spawned with `SpawnActorDeferred`,
  configured, then finished with `FinishSpawning`.
- **Spawning can fail - null-check the result.** Replicated actors are spawned on the server only.
- **Cache `FindComponentByClass`**; never call it per frame.
- **A component never knows its owner's type.** It broadcasts; it does not call up (pillar 2).
- **`Destroy()` marks the actor for collection; the pointer stays non-null** until GC runs.
  `IsValid()` before every use (3.4).

### 3.12 Tick

A tick costs something before your code runs - the dispatch itself, per actor and **per component**
(one NPC is often ten tick functions). Most tick fixes are deletion, not optimisation.

| State | Cost |
|---|---|
| `bCanEverTick = false` | Not registered - zero. **The engine default for `AActor`**; delete the `true` the editor's C++ class template writes unless you need it |
| `bStartWithTickEnabled = false`, or `SetActorTickEnabled(false)` | Registered, dormant |
| `TickInterval = 0.25f` | Dispatched every frame; the body runs periodically |
| `bCanEverTick = true` with an empty or polling body | Full cost for nothing - **the bug** |

- **Prefer, in order:** a delegate (something already knows the value changed), a timer,
  `SetTimerForNextTick`, tick with an interval, tick. Collision and overlap events are delegates, not
  polls.
- **The door pattern.** Tick on when an episodic behaviour starts, off when it ends - a door ticks
  while *opening*, not while being a door. Status effects, interpolators and VFX all work this way.
- **Stagger intervals and looping timers** with a random first delay, or a thousand actors on the
  same interval spike on the same frame.
- **Tick groups:** `TG_PrePhysics` is the default; `TG_DuringPhysics` runs alongside physics for work
  that does not touch it; read physics results in `TG_PostPhysics`; cameras in `TG_PostUpdateWork`.
  **Order within a group is undefined** - declare it with `AddTickPrerequisiteActor` /
  `AddTickPrerequisiteComponent`, or do not rely on it.
- **Many similar things tick as one.** A manager iterating an array beats a thousand ticking actors;
  pair it with the significance manager to spend a fixed budget on the most important N.
- **Blueprint cost is nodes x instances x frames.** Move the loop to C++ and keep the decision in
  Blueprint. Deleting the nodes in `Event Tick` may not unregister the tick - verify with `dumpticks`.

---

## 4. C++ naming conventions

This is the section people get wrong most often. It is exhaustive on purpose.

### 4.1 The core table

| Concept | Convention | Examples |
|---|---|---|
| **Member variables** | `camelCase` | `currentHealth`, `activeRunner`, `loadedRegistry`, `boundActivityManager` |
| **Local variables** | `camelCase` | `resumeFromSectionId`, `detailValue`, `tempIndex` |
| **Function parameters** | `camelCase` | `contactId`, `newIndex`, `slotTag` |
| **Functions and methods** | `PascalCase` | `AdvanceToNextStep`, `ApplyBackground`, `RebuildInventoryGrid` |
| **Booleans** | **`b` prefix** + PascalCase remainder | `bIsWalking`, `bSearchActive`, `bSuppressAutoLaunch` |
| **Constants** | `constexpr` / `static const`, `PascalCase` | `MaxInventorySlots`, `DefaultDwellSeconds` |
| **Class - Actor** | `A` prefix | `AGamePlayerController`, `ANPCBase`, `AQuestTrigger` |
| **Class - UObject / Component / Subsystem** | `U` prefix | `UInventorySubsystem`, `UQuestMovementComponent` |
| **Struct** | `F` prefix | `FAnchorSpec`, `FNotificationEntry`, `FDialogueRow` |
| **Interface** | `I` prefix (plus its `U` companion) | `IInteractInterface` |
| **Enum class** | `E` prefix | `ECallOutcome`, `EWidgetState`, `EInputLockMode` |
| **Enumerator values** | `PascalCase`, **no prefix** | `Answered`, `Declined`, `Missed`, `Passive`, `Ring` |
| **Delegate type** | `F` + `On` + PascalCase | `FOnTransitionReady`, `FOnStandUpComplete` |
| **Template / smart pointer** | `T` prefix | `TObjectPtr`, `TSoftObjectPtr`, `TSubclassOf` |
| **Slate widget** | `S` prefix | `SCustomTextBox` |
| **Log category** | `Log` + project + domain | `LogGameQuestRunner`, `LogGameInventory` |

> **We deviate from Epic's own standard in one place, deliberately: Epic uses PascalCase for member
> variables; we use camelCase.** This is consistent across every project on this team. Follow ours,
> not the engine's.

Everything else follows Epic: type prefixes, `PascalCase` functions, `b` booleans.

### 4.2 Booleans in detail

The `b` prefix is mandatory everywhere a boolean appears - member, local, parameter, and Blueprint
variable.

```cpp
bool bIsWalking;                        // member
bool bSuppressAutoLaunchOnNextLoad;     // member, a latch
bool bFreshOpen;                        // parameter
const bool bHadPendingOpen = ...;       // local
```

**Accessors that return a bool do not carry the `b`.** They are PascalCase functions starting with
`Is` / `Has` / `Can`:

```cpp
bool IsTransitioning() const;
bool HasCompletedOnboarding() const;
bool CanAffordPurchase(int32 cost) const;
```

Name a boolean for the **true** state, never the negative. `bIsVisible`, not `bIsNotHidden` - a
double negative in an `if` is a bug waiting to happen.

### 4.3 Function verb vocabulary

Function names are `PascalCase` and **start with a verb**. Use the established vocabulary rather
than inventing a synonym - a reader should be able to guess what a function does from its first word
alone.

| Verb | Means | Examples |
|---|---|---|
| `Get` | Returns a value, **no side effects** | `GetEquippedItem`, `GetActiveNotification` |
| `Set` | Writes a value | `SetChatPanel`, `SetActiveWidgetIndex` |
| `Is` / `Has` / `Can` | Boolean query | `IsTransitioning`, `HasPendingRequest` |
| `Try` | May fail - returns bool, or validates first | `TryLoadOlderPage`, `TryGetStringField` |
| `Begin` / `Start` | Opens a stateful operation | `BeginCall`, `StartOutgoingRequest` |
| `End` / `Stop` / `Terminate` | Closes it | `EndSequence`, `TerminateCall` |
| `Handle` | **The bound callback body** | `HandleNotificationExpired`, `HandleRunnerFinished` |
| `On` | **The event itself**, or a Blueprint-facing hook | `OnPlayerControllerReady`, `OnPostLoadMapWithWorld` |
| `Apply` | Pushes state onto a visual or component | `ApplyBackground`, `ApplyListVisibility` |
| `Init` | One-time setup with arguments | `InitInventoryPanel`, `InitTile` |
| `Ensure` | **Idempotent** - creates only if absent | `EnsureFadeWidget`, `EnsureGameplayHUD` |
| `Refresh` / `Populate` / `Rebuild` | Recomputes a view from source data | `RefreshBadges`, `PopulateItemList` |
| `Resolve` / `Find` | Looks up and returns, may load | `ResolveAnchor`, `FindTriggerInWorld` |
| `Notify` / `Request` | Crosses a system boundary | `NotifyDestinationReady`, `RequestTransition` |
| `Mark` | Records a state transition into save data | `MarkQuestComplete`, `MarkTutorialSeen` |
| `Validate` | Checks authored data, logs on failure | `ValidateCatalogue` |
| `Do` | **Input adapter only** - forwards input to a component, holds no logic | `DoSprintStart`, `DoThrow` |

Three distinctions that matter:

- **`On` vs `Handle`.** `On*` is the event or virtual hook that fires; `Handle*` is the bound
  callback that does the work. They are not interchangeable, and mixing them makes a delegate graph
  unreadable.
- **`Get` must have no side effects.** If it lazily loads, caches, or hydrates, it is not a `Get` -
  it is a `Resolve` or an `Ensure`.
- **`Do*` holds no logic.** It lives only on the player-facing class and forwards to a component, so
  the AI can drive the same component from a behaviour-tree task (9.9).

### 4.4 Class name composition

Read names as a pattern, not a list:

| Kind | Pattern | Examples |
|---|---|---|
| GameInstance subsystem | `U<Domain>Subsystem` or `U<Domain>GISubsystem` | `UQuestDirectorSubsystem`, `UInventoryGISubsystem` |
| World subsystem | `U<Domain>WorldSubsystem` | `USpawnWorldSubsystem` |
| Component | `U<Domain><Role>Component` | `UDialoguePresenterComponent`, `UQuestMovementComponent` |
| Widget base | `U<Domain><Role>Widget` | `UInventoryGridWidget`, `UNotificationCardWidget` |
| Platform variant | `U<Feature>DesktopWidget` / `U<Feature>MobileWidget` | `UInventoryDesktopWidget`, `UInventoryMobileWidget` |
| DataAsset | `U<Thing>Asset` / `Catalogue` / `Registry` / `Definition` | `UItemDefinitionAsset`, `UAppearanceCatalogue`, `UQuestRegistry` |
| Polymorphic family member | `U<Family>_<Verb><Noun>` | `UQuestStep_SpawnNPC`, `UQuestStep_WaitForProximity` |
| SaveGame | `U<Project><Domain>SaveGame` | `UGameProgressSaveGame`, `UGameSettingsSaveGame` |
| Online service | `U<Domain>Service` / `U<Domain>ServiceSubsystem` | `UChatService`, `UChatServiceSubsystem` |

Two rules on top of the table:

- **A project short-name infix marks a class as project-core rather than feature-local.** A
  `U<Project>SaveGame` is core; a `UInventorySubsystem` is a feature's service. Use it consistently or
  not at all - inconsistent use is worse than none.
- **An underscore in a class name is reserved for a polymorphic family** (`UQuestStep_*`). Do not
  introduce underscores anywhere else.

### 4.5 Enums

```cpp
UENUM(BlueprintType)
enum class ECallOutcome : uint8
{
    /** Connected and talked. First so the default never accuses the player of anything. */
    Answered,

    /** The player rejected the call - zero duration, but a deliberate choice. */
    Declined,

    /** Rang out with no player input. Raised by the ring timeout, never derived from duration. */
    Missed
};
```

Rules:

- **`E` prefix, PascalCase name, always `enum class`, always `: uint8`.** The explicit underlying
  type matters for serialisation size and for Blueprint exposure.
- **Enumerators are PascalCase with no prefix and no redundant type name.** `Answered`, not
  `ECallOutcome_Answered` or `ECO_Answered`.
- **Every enumerator gets a Doxygen comment.** See section 5.
- **Think hard about enumerator 0.** Three rules learned the hard way:
  - For a **wire/parsed** enum, reserve 0 as `Unknown` so "field absent" stays representable. See
    section 16.
  - For a **behaviour** enum, make 0 the safe, inert case, so a half-authored data row can never
    accidentally latch active state.
  - For a **player-facing outcome** enum, never let 0 be the accusatory or failure state - a default
    should not blame the player for something they did not do.
- **Never use a `UENUM` as a `UPROPERTY TMap` key.** Section 16 explains why in full: keys serialise
  by byte value, so editing the enum silently corrupts every stored row.

### 4.6 Structs

```cpp
USTRUCT(BlueprintType)
struct FAppEntry
{
    GENERATED_BODY()

    /** Row id, matched against the catalogue. NAME_None means the slot is empty. */
    UPROPERTY(EditDefaultsOnly, Category = "Initialize|Config")
    FName typeId;

    /** Which badge source paints this tile. None on any tile that is not Available. */
    UPROPERTY(EditDefaultsOnly, Category = "Initialize|Config")
    EAppBadgeSource badgeSource;
};
```

- **`F` prefix, PascalCase name.**
- **Struct fields follow the same `camelCase` rule as class members** - `typeId`, `badgeSource`,
  `startedAtUnix`. Do not switch to PascalCase inside a struct.
- A DataTable row struct inherits `FTableRowBase` and is named `F<Domain>Data` or `F<Domain>Row`.
- Pure data only. A struct with behaviour usually wants to be a `UObject` or a DataAsset.

**Struct initialisation - if the struct needs defaults**

The no-inline-initialisation rule (3.2) applies to structs exactly as it does to classes.
**Declare a default constructor and assign in its body**, never with inline member initialisers:

```cpp
// AppTypes.h
USTRUCT(BlueprintType)
struct FAppEntry
{
    GENERATED_BODY()

    /** Default constructor - all defaults are assigned in the body, never inline above */
    FAppEntry();

    /** Row id, matched against the catalogue. NAME_None means the slot is empty. */
    UPROPERTY(EditDefaultsOnly, Category = "Initialize|Config")
    FName typeId;

    /** Which badge source paints this tile. None on any tile that is not Available. */
    UPROPERTY(EditDefaultsOnly, Category = "Initialize|Config")
    EAppBadgeSource badgeSource;

    /** Seconds the card dwells before it expires. Zero means it never auto-dismisses. */
    UPROPERTY(EditDefaultsOnly, Category = "Initialize|Config")
    float dwellSeconds;
};
```

```cpp
// AppTypes.cpp
FAppEntry::FAppEntry()
{
    typeId = NAME_None;
    badgeSource = EAppBadgeSource::None;
    dwellSeconds = 4.0f;
}
```

Two notes:

- **A types-only header with no `.cpp`** is the one accepted exception - define the constructor
  inline in the header, but still **inside the constructor body**, never as member initialisers.
  The point of the rule is one place to look for defaults, and a constructor body satisfies that
  wherever it lives.
- **Any struct with a number, bool, enum or raw pointer field needs a constructor that sets it.**
  Reflected fields are only zeroed when the engine allocates the struct (inside a `UObject`, a
  `TArray` property, a DataTable row). A local `FAppEntry entry;` holds garbage in every such field,
  and the engine's uninitialised-struct check (`Class.cpp`) flags the type. A struct whose fields
  all have their own constructors (`FName`, `FString`, `TArray`, `FGameplayTag`, `TObjectPtr`) may
  omit it.

### 4.7 Delegates

```cpp
// Non-dynamic - C++ only, INVISIBLE to Blueprint
DECLARE_MULTICAST_DELEGATE(FOnStandUpComplete);
DECLARE_MULTICAST_DELEGATE_OneParam(FOnTriggerEntered, AGamePlayerController*);
DECLARE_MULTICAST_DELEGATE_TwoParams(FOnActivityFinished, FGameplayTag, EActivityEndReason);

// Dynamic - Blueprint-visible, needs UPROPERTY(BlueprintAssignable)
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAssemblyReady);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnLoadoutSaved, const FLoadoutData&, SavedLoadout);
```

- Type name is **`F` + `On` + PascalCase describing the event**, not the handler.
- **Dynamic delegate parameter names are PascalCase.** The name you write in the macro becomes the
  **Blueprint pin label**, so it is user-visible text, not a C++ parameter name. This is the one
  place a parameter is not camelCase, and the reason is that a designer reads it.
- The **member that holds the delegate** is a member variable, so 4.1 applies: drop the `F` and use
  camelCase - `onTransitionReady`. The PascalCase `On*` in 4.3 names functions and virtual hooks,
  not members.
- **More than two parameters? Pass one context struct instead** - `FOnHitReceived` carrying a
  `const FHitContext&` rather than five loose arguments. A new field then goes into the struct, and
  no existing listener or signature changes. For a dynamic delegate the struct must be a
  `USTRUCT(BlueprintType)`.
- Choosing the wrong kind is the most common new-developer bug in Unreal. See section 9.3.

### 4.8 Approved short names

These are the **only** abbreviations accepted. Use them consistently.

| Full name | Short name |
|---|---|
| GameInstance | `<Project>GI`, lowercased - `gameGI` |
| PlayerController | `<Project>PC`, lowercased - `gamePC` |
| CharacterMovementComponent | `movementComp` |
| SkeletalMeshComponent | `skeletalMeshComp` |
| StaticMeshComponent | `staticMeshComp` |
| WidgetComponent | `widgetComp` |
| AnimationInstance | `animInstance` |
| EnhancedInputLocalPlayerSubsystem | `inputSubsystem` |

**The rule behind the table: readable beats short.** A project-prefixed `gameGI` is good; `gi` and
`ggi` are not. **If a name is not in this table, write it out in full.**

### 4.9 File naming

- **One class per file pair.**
- **File name matches the class name without the type prefix.** `UQuestDirectorSubsystem` lives in
  `QuestDirectorSubsystem.h` / `.cpp`.
- Folder path mirrors the class's role (section 1.3).
- **Shared type-only headers are named for their contents:** `AnchorTypes.h`, `DialogueTypes.h`,
  `ChatTypes.h`, `TimeUtils.h`. These hold structs and enums with no behaviour, and exist so two
  systems can share a shape without depending on each other's classes.

### 4.10 GameplayTags

Authored in `Config/DefaultGameplayTags.ini`. **Hierarchical, PascalCase segments, dot-separated:**

```
Activity.Crafting
Customization.Category.Hair
Customization.Slot.Outfit
Level.Hub
Level.Interior.Apartment
NPCMontage.PickupHandover
SpawnMarker.Hub.Intro
Quest.Chapter1.Intro
```

- Establish the **root namespaces** early on a project and keep the list short. A flat sprawl of
  unrelated roots is as bad as no tags.
- **Always fill in `DevComment`.** A tag with an empty comment is a tag nobody else can safely reuse,
  and you will end up with three tags meaning the same thing.
- **Tag matching is strict.** `Level.Interior.Apartment` and `Level.Portal.Interior.Apartment` are
  separate branches and will *never* satisfy `MatchesTag`. Authored data must use the exact tag the
  runtime sends. See section 16.
- **Prefer tags over strings and enums** for level destinations, spawn points and identity. A tag is
  a content-side addition; an enum is a code change.
- **Tags used in C++ are declared natively** - `UE_DECLARE_GAMEPLAY_TAG_EXTERN` in a header,
  `UE_DEFINE_GAMEPLAY_TAG` in the `.cpp` (the macro refuses to compile in a header). Never
  `RequestGameplayTag("Literal")` in gameplay code: a typo is a silent no-match.
- **`MatchesTag` is hierarchical** (`Damage.Type.Fire` matches `Damage.Type`); `MatchesTagExact` is
  not. Choose deliberately.

### 4.11 Console commands

Any system with non-trivial internal state should register console commands for driving it - launch,
skip, reset, list, abort. They cost an hour to write and save days of clicking through content to
reach the state you need to test.

**Naming: `<Project>.<system>.<verb>`** - lowercase project and system segments, camelCase verb when it
is more than one word.

```
game.quest.launch
game.quest.skipSection
game.quest.clearProgress
game.quest.listSections
game.quest.abort
```

Register them in the owning subsystem's `Initialize`, and **release the handles in `Deinitialize`** -
a leaked `IConsoleCommand` outlives the subsystem and fires into a dead object.

---

## 5. Comment standard

Comments are enforced as strictly as code, because a codebase carries non-obvious decisions that
nothing else records.

### 5.1 What must be commented

- **Every `UPROPERTY` declaration** - Doxygen `/** */`
- **Every `UFUNCTION` declaration** - Doxygen `/** */`
- **Every variable and every function in a header** - including private and non-reflected ones.
  The comment must add what the name does not: a unit, a lifetime, what null means, a caller
  contract. **A trivial accessor whose name says everything** (`GetCurrentHealth`, `IsTransitioning`)
  **is exempt** - a comment that repeats it is the self-evident comment 5.3 bans.
- **Every enumerator** in a `UENUM`
- **Every class** - a `/** */` block above `UCLASS()` stating its role and its lifetime

### 5.2 The two-line rule

> **Two lines maximum. No exceptions.** This applies to every comment you *write*, not only to ones
> you clean up.

- No paragraph comments. No multi-line rationale blocks.
- **If the reasoning needs more than two lines, it belongs in a design doc** - not above the code.
- Keep them plainly worded. State the point, not the full argument behind it.
- Applies to `//` inline, `/** Doxygen */`, and file-scope comments alike.
- **Per-parameter comments may sit on their own line, but each is one line maximum** - never wrap a
  single parameter across two lines.

```cpp
/** Currently active runner - null when no quest is running */
UPROPERTY()
TObjectPtr<UQuestRunner> activeRunner;

/** Loaded registry asset - held strong so soft-resolved quests don't unload mid-execution */
UPROPERTY()
TObjectPtr<UQuestRegistry> loadedRegistry;
```

The **class-level block** is the one place a slightly longer form is acceptable, because it documents
a contract rather than a line of code:

```cpp
/**
 * Persistent orchestrator. Lives for the GameInstance's lifetime, but its memory
 * footprint is one runner pointer plus one registry pointer when idle.
 */
UCLASS()
class GAME_API UQuestDirectorSubsystem : public UGameInstanceSubsystem
```

### 5.3 Inline comments

`//` comments are for **non-obvious rationale only**. Do not comment self-evident code.

```cpp
// WRONG - restates the code, adds nothing
// Set health to 100
currentHealth = 100;

// CORRECT - explains a decision the code cannot show
// Built BEFORE the step starts, so a step that hides the HUD finds one to hide.
EnsureGameplayHUD();
```

**A good test: if deleting the comment loses nothing but words, delete it.**

Comment the *why*, never the *what*. The code already says what it does.

### 5.4 Comment maintenance (enforced on new and modified code)

- **Code you add or change meets this standard in full.** If a declaration you touch has no
  comment, add one; if its comment is three lines or longer, rewrite it down to two, preserving its
  meaning.
- **Do not repair the rest of the file as a drive-by.** Untouched code is brought up to standard in a
  planned cleanup pass, in its own commit - the same rule as logging (6.5), for the same reason: a
  real edit should not hide inside cleanup noise.

Documentation decays unless it is repaired, so the cleanup pass is planned work, not optional work.

### 5.5 Forbidden content

- **No emojis anywhere.** Not in comments, logs, documentation, commit messages, or code.
- **Never write the Unicode replacement character `U+FFFD`.** It is a mojibake / encoding-corruption
  artifact, not valid content. **When you find one while editing, remove it and restore the intended
  character** where the meaning is recoverable. Encoding corruption spreads silently through a
  codebase once it is committed once.
- **No commented-out code in a commit.** Delete it; git remembers.
- **No anonymous `TODO`.** A `TODO` without a name and a reason is noise. Either fix it, ticket it,
  or delete it.

---

## 6. Logging standard

Logging is the only debugging instrument you have on device, in a packaged build, and over remote
streaming - anywhere a debugger cannot attach. **Treat log lines as a deliverable, not as
scaffolding.**

### 6.1 Mandatory format

```cpp
UE_LOGFMT(LogGameQuestDirector, Log, "[{Obj}] [FunctionName] Description: {Detail}",
    GetNameSafe(this), detailValue);
```

**Every log line must include four things:**

1. **What happened** - the description
2. **The class** - `GetNameSafe(this)`, in the leading `[{Obj}]`
3. **The function name** - in its own `[Brackets]`
4. **The relevant context value** - the id, tag, index or count that makes the line actionable

A line that says "failed" without saying *what* failed, *where*, and *with what input* is not a log
line. You will read it at 2am and learn nothing.

Three rules on how those values are produced:

- **`GetNameSafe(obj)`, never `obj->GetName()`.** `GetNameSafe` returns `"None"` for a null pointer
  instead of crashing - and a log line is most often written exactly when something is null.
- **Enums through `UEnum::GetValueAsString(value)`**, never a `(uint8)` cast. A number in a log goes
  stale the moment the enum is edited; a name does not.
- **Conditional lines use `UE_CLOGFMT(condition, ...)`** instead of wrapping `UE_LOGFMT` in an `if`.

### 6.2 Category naming and declaration

**Every log category starts with `Log` + the project short name**, then the domain.

**Declare it with `DEFINE_LOG_CATEGORY_STATIC` at the top of the `.cpp`** that owns it:

```cpp
// QuestRunner.cpp
#include "QuestRunner.h"

DEFINE_LOG_CATEGORY_STATIC(LogGameQuestRunner, Log, All);
```

This is a single line, file-local, and needs no header declaration and no matching `DEFINE` -
which is exactly what you want for the overwhelming majority of categories. **A category belongs to
one system, and one system is usually one `.cpp`.**

Rules:

- **`DEFINE_LOG_CATEGORY_STATIC` is the default.** Reach for it first.
- **Only use the `DECLARE_LOG_CATEGORY_EXTERN` (header) + `DEFINE_LOG_CATEGORY` (cpp) pair when
  several translation units genuinely need to log to the same category** - a subsystem plus its
  helper classes, for example. A static category is invisible outside its own file, so sharing one
  requires the extern pair.
- **One category per meaningful subsystem** - not one per class, and not one for the whole project.
  The point of a category is that you can filter the Output Log down to one system.
- Keep a module-wide fallback category (`LogGame`) for genuinely cross-cutting code, and use it
  sparingly.
- **Never `LogTemp` in committed code** - it cannot be filtered down to a system.

### 6.3 Severity

| Level | Use for | Example |
|---|---|---|
| `Error` | Critical failure - the feature cannot proceed | A null definition, an unresolved catalogue row |
| `Warning` | Recoverable issue, **or a tripwire for a state that should not occur** | "Could not resolve PlayerController - steps requiring PC will fail" |
| `Log` | Normal flow worth tracing | "Quest 'X' starting at section index 2" |
| `Verbose` | Detailed per-frame or per-item debug | Per-message parse detail |

**`Warning` is for tripwires, and we use it deliberately.** When an invariant is re-established
rather than enforced - a flag unexpectedly true, a cache unexpectedly empty - log a Warning and
proceed. **A silent recovery is a bug you will meet again later with no evidence.**

### 6.4 Examples

```cpp
UE_LOGFMT(LogGameQuestRunner, Error, "[{Obj}] [LaunchQuest] Quest definition is null",
    GetNameSafe(this));

UE_LOGFMT(LogGameQuestRunner, Warning,
    "[{Obj}] [LaunchQuest] Section '{Section}' not found in quest '{Quest}' - starting from beginning",
    GetNameSafe(this), resumeFromSectionId, quest->GetQuestId());

UE_LOGFMT(LogGameQuestRunner, Log,
    "[{Obj}] [LaunchQuest] Quest '{Quest}' starting at section index {Index}",
    GetNameSafe(this), quest->GetQuestId(), currentSectionIndex);
```

### 6.5 UE_LOGFMT vs UE_LOG

| | `UE_LOGFMT` | `UE_LOG` |
|---|---|---|
| Placeholders | `{Tokens}` | `%s`, `%d` |
| FString | Pass directly | Needs `*` dereference |
| Literals | Plain string | Needs `TEXT()` |
| Type safety | High - a type mismatch cannot corrupt the output | Low - a wrong specifier compiles and prints garbage |

**`{Tokens}` are readable labels, not a binding.** Passing bare values - `"{Obj} {Id}", a, b` - is
`UE_LOGFMT`'s *positional* form: values match tokens by order, and the names do nothing. `{0}` and
`{Obj}` behave identically there. Only the pair form, `("Obj", a), ("Id", b)`, matches by name
(`StructuredLog.h`). We use the positional form with descriptive token names, so **keep the argument
order matching the token order** - reordering compiles and lies, exactly as with `UE_LOG`.

- **`UE_LOGFMT` is the standard for all new and modified code.**
- **Do not convert an existing file's logging as a side effect of an unrelated change** - that is
  diff noise hiding a real edit. Lines you write or change use `UE_LOGFMT`; the rest of the file is
  converted in a planned cleanup pass, in its own commit. Same principle as 5.4.

### 6.6 What to log

- **Every early return from a guard clause that signals a problem.** A silent `return` on a failure
  is a bug that costs an hour to find. Match the log to the kind of return:
  - **Unexpected but recoverable** - `Warning` or `Error`, per 6.3.
  - **Expected** - no target in range, an optional component absent, a hot-path early-out - `Verbose`,
    or no log at all. A guard that fires every frame by design is not news.
  - **A programmer error that should never happen** - `ensure` (3.9), which reports a callstack once.
- **Every state transition** in a subsystem or runner - entered, completed, aborted.
- **Every DataAsset validation failure**, naming the asset and the row that failed. Authored-data
  errors otherwise surface at runtime as "a thing that never appears", which reads as a missing
  feature rather than bad data.
- **Never log at `Log` level inside Tick or a per-frame loop.** Use `Verbose`. On a hot path, pass
  raw values as tokens - never build an `FString` (with `FString::Printf` or concatenation) only to
  log it.
- **No emojis in log strings.**

### 6.7 Validation passes

Any system driven by authored data should have a `Validate*` function that runs **once on load** and
logs an `Error` for every unresolvable reference, duplicate id, or miscategorised row.

This is the highest-value logging you will write. Bad authored data fails silently by default; a
validation pass converts a mystery into a line in the log.

**Catch it in the editor too.** Override `IsDataValid(FDataValidationContext&) const` (inside
`#if WITH_EDITOR`) on DataAsset and actor classes, so bad data fails on save and in the Data
Validation pass before anyone presses Play. Keep the runtime `Validate*` pass as well - it catches
data that only goes wrong in combination, at load.

---

## 7. Blueprint and content naming conventions

### 7.1 Asset prefixes

**Every asset carries a type prefix.** No exceptions, including for temporary and test assets.

| Prefix | Asset type | Example |
|---|---|---|
| `BP_` | Blueprint class | `BP_AvatarCharacter`, `BP_PressurePlate` |
| `WBP_` | Widget Blueprint | `WBP_InventoryGrid`, `WBP_MainMenu` |
| `ABP_` | Animation Blueprint | `ABP_PlayerCharacter` |
| `DA_` | Data Asset | `DA_TutorialSequence`, `DA_Hair_1_Female` |
| `DT_` | Data Table | `DT_NPCDialogue`, `DT_ItemDefinitions` |
| `L_` | Level / map | `L_MainHub`, `L_SplashMap` |
| `SM_` | Static Mesh | `SM_TeaTable` |
| `SKM_` | Skeletal Mesh | `SKM_PlayerBody` |
| `SK_` | Skeleton | `SK_PlayerSkeleton` |
| `PHYS_` | Physics Asset | `PHYS_PlayerBody` |
| `M_` | Material | `M_Wood` |
| `MI_` | Material Instance | `MI_Wood_Dark` |
| `MF_` | Material Function | `MF_WorldAlignedUV` |
| `MPC_` | Material Parameter Collection | `MPC_TimeOfDay` |
| `T_` | Texture | `T_UIIcon_Home` |
| `RT_` | Render Target | `RT_MirrorCapture` |
| `AS_` | Anim Sequence | `AS_PickupHandover` |
| `AM_` | Anim Montage | `AM_Player_SitToStand` |
| `BS_` | Blend Space | `BS_Idle_Walk_Run` |
| `AO_` | Aim Offset | `AO_RifleAim` |
| `IA_` | Input Action | `IA_Interact`, `IA_Move` |
| `IMC_` | Input Mapping Context | `IMC_Default`, `IMC_Vehicle` |
| `NS_` | Niagara System | `NS_Sparks` |
| `NE_` | Niagara Emitter | `NE_Embers` |
| `SC_` | Sound Cue | `SC_FootstepStone` |
| `SW_` | Sound Wave | `SW_Ambience_Forest` |
| `LS_` | Level Sequence | `LS_OpeningCinematic` |
| `HDRI_` | HDRI backdrop | `HDRI_Overcast` |
| `E_` | Blueprint Enum | `E_ContactTab` |
| `F_` | Blueprint Struct | `F_LoadoutData` |
| `BB_` | Blackboard | `BB_Guard` |
| `BT_` | Behavior Tree | `BT_Guard` |
| `ST_` | State Tree | `ST_GuardPatrol` |
| `BPI_` | Blueprint Interface | `BPI_Interactable` |
| `BFL_` | Blueprint Function Library | `BFL_InventoryUtils` |
| `BPC_` | Blueprint Actor Component | `BPC_Inventory`, `BPC_Health` |
| `PM_` | Physical Material | `PM_Metal`, `PM_Grass` |
| `ATT_` | Sound Attenuation | `ATT_Footsteps` |
| `SCL_` | Sound Class | `SCL_Music`, `SCL_SFX` |
| `MSS_` | MetaSound Source | `MSS_Explosion` |
| `MSP_` | MetaSound Patch | `MSP_RandomPitch` |
| `CR_` | Control Rig | `CR_Mannequin` |
| `IK_` | IK Rig | `IK_Mannequin` |
| `RTG_` | IK Retargeter | `RTG_MannyToPlayer` |
| `CF_` | Curve Float | `CF_DamageFalloff` |
| `CV_` | Curve Vector | `CV_CameraShake` |
| `CLC_` | Curve Linear Color | `CLC_SkyTint` |
| `CT_` | Curve Table | `CT_XPPerLevel` |
| `GE_` | Gameplay Effect (GAS) | `GE_Damage_Fire` |
| `GA_` | Gameplay Ability (GAS) | `GA_Dash` |

**One prefix per type, never a choice of two.** Blueprint structs are `F_`, matching the C++ `F`
struct prefix in 4.1 - not `S_`, which is also seen in the wild. Where the community uses two
prefixes interchangeably, we pick the one that matches our C++ convention and hold it, because a
prefix that is sometimes one thing and sometimes another cannot be searched for.

### 7.2 Blueprint role infixes

Core-framework Blueprints carry a second segment naming their role. This makes the framework skeleton
of any project readable at a glance in the Content Browser:

| Infix | Role | Examples |
|---|---|---|
| `BP_GM_` | GameMode | `BP_GM_Main`, `BP_GM_Onboarding` |
| `BP_GS_` | GameState | `BP_GS_Main` |
| `BP_PC_` | PlayerController | `BP_PC_Player` |
| `BP_PS_` | PlayerState | `BP_PS_Player` |
| `BP_GI_` | GameInstance | `BP_GI_Main` |
| `BP_CH_` | Character | `BP_CH_Player`, `BP_CH_NPCGuard` |
| `BP_AIC_` | AI Controller | `BP_AIC_Guard` |

Everything else is simply `BP_<Thing>`: `BP_PortalTrigger`, `BP_Wardrobe`, `BP_ApartmentDoor`.

### 7.3 Naming the rest of the name

- **PascalCase after the prefix.** `SM_TeaTable`, not `SM_teatable` or `SM_tea_table`.
- **Underscores separate meaningful segments only** - variant, gender, index, LOD:
  `DA_Hair_1_Female`, `MI_Wood_Dark`, `BS_Idle_Walk_Run_Guard`.
- **No spaces, ever.** They break command-line tooling and cook paths.
- **No trailing duplication numbers.** `_1` and `_2` mean "a variant we chose", never "I pressed
  Ctrl+W". A `BS_Idle_Walk_Run_1` sitting next to `BS_Idle_Walk_Run` is a decision nobody made.
- **Spell it correctly, and spell it the same way every time.** A misspelled asset name is permanent
  in practice - see 7.6.
- **Never ship a vendor, tool or scratch name.** Rename on import. `ChatGPT_image_3`, `Icosphere`,
  `Retopo_final`, `test_`, `yy_`, `Wood058` do not belong in a shipping content tree.
- **Suffix by variant, not by history.** `_Final`, `_v2`, `_New`, `_Old`, `_Fixed`, `_Copy`,
  `_Backup` are all history. Git holds history; the asset name holds identity.

### 7.4 Naming inside a Blueprint

**Blueprint follows the C++ conventions. The boundary between them should be invisible.**

| Concept | Convention | Example |
|---|---|---|
| Variables | `camelCase` | `currentSpeed`, `activeContact` |
| Booleans | `b` prefix | `bIsOpen`, `bHasPlayed` |
| Functions and custom events | `PascalCase`, verb-first (section 4.3) | `OpenPanel`, `HandleCallEnded` |
| Function parameters | `camelCase` | `contactId`, `newIndex` |
| Local variables | `camelCase` | `tempIndex` |
| Macros | `PascalCase` | `IsValidTarget` |
| Event Dispatchers | `On` + PascalCase | `OnPanelChanged`, `OnInventoryUpdated` |
| Components in a Blueprint | `camelCase` + role suffix | `movementComp`, `widgetComp`, `collisionBox` |
| Timelines | `PascalCase` + `Timeline` | `FadeInTimeline` |
| Widget bind names | `<role>_<Type>` | `back_Btn`, `chat_ScrollBox`, `title_Text`, `background_Img` |
| Categories | Mirror the C++ hierarchy | `Initialize\|Movement` |

**Widget bind names are load-bearing.** A `meta = (BindWidget)` property matches on **object name**,
case-insensitively, and is a hard compile requirement. Rename the widget in UMG and the bind breaks.
See section 12.1.

**The bind name is also the C++ member name - a deliberate exception to 4.1.** A `BindWidget` member
must match the widget's object name, so it carries the `_<Type>` underscore:
`TObjectPtr<UButton> back_Btn;`. It is the only member-variable name with an underscore. One form
everywhere - camelCase role, PascalCase type - in UMG, in C++, and in every example in this document.

Common widget type suffixes: `_Btn`, `_Text`, `_Img`, `_ScrollBox`, `_Switcher`, `_SizeBox`,
`_Panel`, `_Bar`, `_Box`, `_Slot`.

### 7.5 Folder naming

- **PascalCase folder names.** `Characters`, `LevelPrototyping`, `SubLevels`.
- **No spaces, no abbreviations you would not use in code.**
- Folder depth mirrors ownership, same principle as section 1.3.
- **Do not create a folder for one asset.** Create it at three.

### 7.6 Why this is strict

Asset names are effectively permanent. A rename in Unreal creates a redirector, rewrites a binary
file, and risks breaking every reference to it - so in practice, misspellings and vendor names
survive to ship.

Real damage this prevents, taken from projects this team has worked on:

- **One character with four spellings** across 69 assets, because the first import had a typo and
  every later asset copied it.
- **"Circle" misspelled two different ways** in the same UI folder.
- **A folder name misspelled** in the core content path, permanently.
- **Vendor names in the shipping tree** - tool exports, stock-site downloads, and scratch geometry
  names.
- **Maps inconsistently prefixed**, so half the level list sorts away from the other half.

**Get it right on import. It is the only cheap moment.**

If you inherit non-compliant content: **new assets follow this standard with no exceptions, and you
do not rename existing assets opportunistically.** Batch renames are a planned task, agreed with
whoever owns that content, done in one commit.

---

## 8. Blueprint discipline

### 8.1 The C++/Blueprint boundary

> **C++ owns core systems, interfaces and data shape. Blueprint inherits from C++ and owns game
> logic and presentation.**

**System architecture in Blueprint is never acceptable** - that half of the rule has no exceptions.
The gameplay half is the default split, suited to a designer-heavy team. A C++-first project (small
team, programmer-driven design) may keep gameplay flow in C++, and records that as a project override
(see the top of this document). What no project may do is choose per feature.

| Belongs in C++ | Belongs in Blueprint |
|---|---|
| Subsystems and services | Per-actor gameplay logic |
| Interfaces and data shape | Visual and audio response |
| Save/load | Animation hookups |
| Networking and HTTP | Widget layout and bindings |
| Anything performance-critical or ticking | Designer-tunable behaviour |
| Anything two systems must agree on | One-off scripted moments |

Mark functions `BlueprintImplementableEvent` (C++ declares, BP implements) or `BlueprintNativeEvent`
(C++ provides a default, BP may override) when Blueprint needs to respond to a C++ event.

- **The drift diagnostic: a Blueprint branching on a game rule.** Rules must be correct, testable
  and diffable - that is C++. Tuning is data. Composition, look and feel are Blueprint.
- **Call a `BlueprintNativeEvent` by its plain name** from C++ - never `Foo_Implementation`, which
  skips the Blueprint override.
- **`BlueprintPure` only for trivial, side-effect-free functions.** A pure node re-runs for every pin
  that reads it.
- **Blueprint logic has one writer at a time.** A `.uasset` cannot merge, so shared logic that changes
  often belongs in C++, where two people can work on it at once.
- **The test:** a new enemy type is one DataAsset, one Blueprint and zero compiles.

### 8.2 Prototyping, testing and temporary work

**Blueprint is the right tool for trying something out.** Nothing above forbids it - the boundary in
8.1 governs what *ships*, not what you build to answer a question.

Use Blueprint freely for:

- **Prototyping a mechanic** before you know its final shape. Iterating in BP is faster than
  iterating a header, and finding out a design is wrong is cheaper there.
- **Test harnesses** - a `BP_` actor that spawns the state you need, fires the delegate you are
  chasing, or drives a system without playing through content to reach it.
- **Debug and cheat actors** - level-placed helpers that skip a sequence, grant an item, or teleport
  the player.
- **Blocking out a scripted moment** before it becomes a data-driven step.

The rules that keep this from becoming technical debt:

- **Name it as temporary.** Prefix the asset `BP_TEMP_` / `WBP_TEMP_`, or keep it in a `TEMP/` or
  `Developers/` folder. A prototype that is indistinguishable from shipping content becomes shipping
  content by accident.
- **Keep it out of shipping paths.** No shipping asset should reference a temp Blueprint. If it does,
  it is not temp any more - promote it properly or cut the reference.
- **Port or delete before feature sign-off.** A prototype has one of two ends: it becomes a C++
  implementation, or it is deleted. "Left in because it works" is how a codebase acquires a second,
  undocumented architecture.
- **Do not build a temp Blueprint on top of another temp Blueprint.** One layer of scaffolding is a
  prototype; two is a system nobody designed.
- **Do not skip the naming rules** (section 7) because it is temporary. Temp assets outlive their
  intent more often than not, and an unprefixed one is the hardest to find later.

Debug and cheat actors are the one category that may stay indefinitely, because their job is
permanent. Hold them to the same naming and hygiene rules as anything else, keep them out of the
shipping cook, and gate anything player-visible behind a build configuration check.

### 8.3 Graph hygiene

- **Comment boxes on every graph section.** A graph with no comment boxes is unreviewable.
- **Every variable gets a tooltip and a category**, exactly like a `UPROPERTY` does.
- **Reroute nodes over crossing wires.** If you cannot read it, neither can the next person.
- **Collapse to functions** rather than growing the Event Graph. If `Event Tick` has more than a
  handful of nodes, the logic belongs in C++.
- **Never leave orphan or disconnected nodes** in a graph. Delete them.
- **No `Cast To` in Tick.** Cache the result once.
- **`Cast To BP_X` is a hard reference** - it loads `BP_X` and everything `BP_X` references. Cast to
  the C++ base class, or call through an interface (9.7).
- **Blueprint is for events, not loops.** A loop over many items per frame belongs in C++.
- **Avoid `Get All Actors Of Class`** outside one-time initialisation - never in Tick, never per
  event. Cache the result, or have the actors register themselves.
- **No hard references to heavy assets** in a widely-instanced Blueprint - it pulls them into memory
  at load. Soft-reference and load on demand.
- **Use the Reference Viewer and Size Map** before committing a Blueprint that references content. A
  surprising dependency chain is easier to see there than to debug later.

### 8.4 Blueprint nativization is not a plan

Do not write heavy logic in Blueprint on the assumption it can be nativized or ported later. Port it
when you write it, or accept the cost permanently.

---

## 9. Architecture rules

### 9.1 The five key conventions

- **Desktop/Mobile split - if the project ships on both.** Where it does, any UI system that touches
  player interaction gets separate `*DesktopWidget` and `*MobileWidget` subclasses **from the start**,
  because the layout, the input model and the hit targets all differ, and retrofitting the split is
  far more expensive than starting with it. Where the project is single-platform, do not build the
  second path speculatively.

- **GameplayTags over enums and strings** for level destinations, identity and spawn points. A tag is
  a content-side addition; an enum is a code change.

- **DataAssets over DataTables** for new game data. Typed `UDataAsset` subclasses give you
  polymorphism, inline authoring (`EditInlineNew` + `Instanced`), and per-asset validation. DataTables
  are for flat, uniform rows - dialogue lines, localisation, tuning tables - and are one binary file,
  so two designers cannot edit one at once. Choose the container by shape: many uniform rows,
  `UDataTable`; one entity, `UPrimaryDataAsset`; a value over a curve, a curve asset or `UCurveTable`;
  project-wide or per-platform, `UDeveloperSettings` (text `.ini`, mergeable); a shared vocabulary,
  `FGameplayTag`.

- **Subsystems for services.** Game-wide services that must outlive a map are **GameInstance
  subsystems**; services scoped to one level - spawning, level-local registries - are **World
  subsystems**, created and destroyed with the world. Do not put service logic directly in GameMode
  or GameInstance - GameMode is destroyed on map load, and anything caching it dies with it.
  **GameMode does legitimately own the match rules** - win and lose conditions, player spawning,
  round flow - because those are per-map and server-only by nature. On a replicated project, note that **a subsystem has no network authority of its
  own** - see 11.2 before you put authoritative state in one.

- **One owner per piece of state.** See 9.4.

### 9.2 Scalability rules

These exist because content always grows faster than code:

- **No switch statements on identity.** A `switch` on slot, item type or state means every new case
  is a code change in a file that has nothing to do with the new content. Use one of two patterns:
  - **A map keyed by `FGameplayTag`**, authored in a DataAsset -
    `TMap<FGameplayTag, TObjectPtr<UItemBehaviourAsset>>`. A new case is a new tag and a new row.
  - **Strategy via polymorphic DataAssets** - the data carries an `Instanced` behaviour object (the
    `UQuestStep_*` family in 4.4) and the caller invokes its virtual. A new case is a new subclass or
    asset, and the caller never changes.
- **No progression state in domain enums.** An enum describes what a thing *is*, never how far the
  player has got.
- **No implicit contracts in comments.** If two things must agree, enforce it in the data - a
  validation pass that logs an Error (section 6.7).
- **No single-point assumptions.** `TArray<FAttachmentPoint>` always, even when today's design only
  needs one. The second one always arrives.
- **Every new slot, item type or unlock should be a content or config change - zero code change.** If
  adding the *second* one of something requires touching C++, the first one was built wrong.

**A counter-example worth internalising:** an *enum*-keyed `TMap` is not one of those patterns. If
the key is a C++ enum, adding a case is already a code change - so the map was never content-only,
and it carries the serialisation hazard in section 16 for nothing. When the set of cases is genuinely
fixed in code, one named `EditDefaultsOnly` field per case is the honest shape; when it should grow
with content, key by GameplayTag instead.

### 9.3 Delegates - choosing the right kind

| | Non-dynamic | Dynamic |
|---|---|---|
| Declaration | `DECLARE_MULTICAST_DELEGATE*` | `DECLARE_DYNAMIC_MULTICAST_DELEGATE*` |
| Blueprint-visible | **No** | Yes, with `UPROPERTY(BlueprintAssignable)` |
| Bind | `AddUObject`, `AddWeakLambda` | `AddDynamic` |
| Unbind | `RemoveAll(this)` | `RemoveDynamic` |
| Performance | Faster | Slower (reflection) |

- **Default to non-dynamic** unless Blueprint genuinely needs to bind.
- **From a `UObject`, bind with `AddUObject` or `AddWeakLambda(this, ...)`** - never `AddLambda` with a
  `[this]` capture, which the delegate cannot see and will fire into a dead object (10.2). A template
  deduction error from `AddUObject` almost always means the handler's signature does not match the
  delegate's, not an engine limit.
- **Binding must match the declaration.** Mixing them does not compile, which is the one merciful
  part of this.
- **Always unbind in the matching teardown** - `EndPlay`, `Deinitialize`, `NativeDestruct`. A dangling
  bind on a destroyed object is a crash you will reproduce once a week.
- **A new delegate declaration requires a full build with the editor closed** - Live Coding cannot
  patch reflection data, and the delegate simply never fires. Full trigger list: section 15, item 1.

### 9.4 Ownership

> **Every transition, every state machine, every timer has exactly one owner.**

Two paths that can both advance the same state produce restart loops that are extremely hard to
reproduce. When you add a second caller to something that completes a phase, you are almost certainly
introducing a bug - **find the existing owner instead.**

Corollaries:

- **State must be owned by an event guaranteed to run.** Never by a cosmetic callback, a UMG tick, or
  an animation notify that a map load or a blend-out can interrupt. See section 16.
- **A completion signal fires exactly once**, and the code that fires it is the code that owns the
  operation.
- **If an invariant is re-established rather than enforced, log a Warning** (section 6.3).
- **Capture before you transition.** A state transition often clears the fields that describe the
  state it is leaving. Copy what you still need into a local *before* calling it:

  ```cpp
  AActor* const instigator = lastInstigator;   // Idle clears lastInstigator
  TransitionToState(EPickupState::Idle);
  NotifyPickupReleased(instigator);
  ```

### 9.5 Persistence across level transitions

Anything that must outlive a map load lives on the **GameInstance** or a GameInstance subsystem.
Everything else is destroyed and recreated - including the PlayerController, the HUD, every widget,
and every world timer.

Design the handoff explicitly:

- Re-acquire the PlayerController on arrival, do not cache it across the load.
- Re-add persistent widgets to the viewport; they are dropped even though the object survives.
- Drive anything time-based from a **subsystem** timer, not a widget tick.

Section 16 covers each of these as a concrete trap.

**What survives travel:** the GameInstance and its subsystems, and each LocalPlayer and its
subsystems, always. Seamless travel also keeps the PlayerController and PlayerState - and the
PlayerState carries data across only what you copy in `CopyProperties`. The world, its subsystems,
the GameMode, the GameState and every other actor are always destroyed.

**Under World Partition, any actor can unload at any time** (`EndPlay` with `RemovedFromWorld`).
Never hold a hard reference to a level actor from anything that outlives it, and keep durable state
in a World subsystem or higher, never on a placed actor.

### 9.6 Project settings

- **Project-wide tunables live in a `UDeveloperSettings` subclass** -
  `UCLASS(Config = Game, DefaultConfig)` - which appears under Project Settings and saves to
  `DefaultGame.ini`. Read it with `GetDefault<U<Project>QuestSettings>()`, and add the
  `DeveloperSettings` module dependency.
- Not a hard-coded constant, not a property on the GameMode Blueprint, not a hand-parsed ini section.
- Per-level and per-asset values stay in DataAssets. A setting is for values that apply to the whole
  project.
- **Console variables are namespaced** `<Project>.<system>.<name>`, lowercased like console commands
  (4.11), with every value documented in the help text. Anything that grants an advantage is
  `ECVF_Cheat`.
- **Per-platform differences live in per-platform config**, not in `if (platform)` branches in C++.
- **`Saved/Config` is local and beats every other config layer.** A setting that works on one machine
  only is usually a stale value there.

### 9.7 Interfaces

Interfaces are how two systems talk without including each other's classes.

- **Test with `obj->Implements<UInteractInterface>()`.** It sees both C++ and Blueprint
  implementations. `Cast<IInteractInterface>(obj)` returns null when a Blueprint implements the
  interface, because there is no C++ vtable to cast to.
- **Call Blueprint-facing interface functions through `IInteractInterface::Execute_Interact(obj, ...)`**,
  never directly on a cast pointer. A direct call skips the Blueprint implementation.
- **Hold an interface reference as `TScriptInterface<IInteractInterface>`** in a `UPROPERTY`, so the
  object stays visible to GC (3.8).
- A C++-only interface (`meta = (CannotImplementInterfaceInBlueprint)`) may be called through
  `Cast<>` directly.

### 9.8 Layered responsibility chains

When one event crosses several classes - a hit, an interaction, a pickup - split it into layers, each
owned by the class that has the knowledge:

1. **Detect** - the sensor (projectile, trigger, trace) notices contact and broadcasts it with a
   context struct (4.7). It never decides the outcome.
2. **Resolve** - the target decides what the contact means *for it*, using only its own components -
   a shield, a dodge window, armour - and returns a result enum.
3. **Act** - the authority, usually the GameMode (9.1), applies the consequence: damage, elimination,
   score.

Each layer can be tested alone, and a new modifier - a power-up, a status effect - slots into the
resolve step without touching the sensor, the authority or any delegate signature.

### 9.9 Input adapters and shared abilities

- **Abilities live in components on the shared base class** - sprint, dodge and throw sit on
  `A<Project>CharacterBase` - so the player and the AI have exactly the same capabilities.
- **The player class only adapts input.** Its `Do*` handlers (4.3) forward to those components and
  hold no logic. The AI drives the same components from behaviour-tree or State Tree tasks.
- If a behaviour exists only in a `Do*` handler, the AI cannot use it and the player's version cannot
  be tested without input. Move it into the component.

### 9.10 Design patterns - the approved catalogue

Use the Unreal-native form of a pattern before inventing one.

| Pattern | Unreal form | Use for | Serves |
|---|---|---|---|
| **Observer** | Delegates (4.7, 9.3) | "This changed" - UI, audio, achievements reacting to gameplay | Pillar 2 |
| **Strategy** | A polymorphic `UObject` or DataAsset, `Instanced` into data (9.2) | Behaviour that varies per item, step or ability, without a `switch` | Pillar 3 |
| **Type Object** | A `UPrimaryDataAsset` that defines a kind of thing | New enemy, weapon or item types as content, not classes | Pillar 3 |
| **Service locator** | Subsystems (9.12) | Game-, world- or player-scoped services - never a hand-rolled singleton | Pillar 2 |
| **Component** | `UActorComponent` / `USceneComponent` | Capabilities any actor can gain (9.9) | Pillar 1 |
| **State machine** | StateTree, or an enum with a single owner (9.4) | AI, match phases, UI flow - anything with transitions | Pillar 1 |
| **Command** | Enhanced Input actions (9.13); GAS abilities where GAS is used | Intent, separated from the key that produced it and the code that runs it | Pillar 2 |
| **Factory** | `TSubclassOf<T>` + `SpawnActorDeferred` (3.11) | Spawning a designer-chosen class, configured before `BeginPlay` | Pillar 3 |
| **Object pool** | A subsystem-owned pool of pre-spawned actors | Projectiles, impacts, damage numbers, one-shot VFX (13.4) | Performance |
| **Message bus** | A tag-keyed message subsystem | Two systems that must not know each other exist | Pillar 2 |
| **Dirty flag** | Push-model replication (11.8); invalidation (12.6) | Doing work only when its input changed | Performance |

Choosing between the three decoupling patterns:

- **Delegate** when the listener may know the source.
- **Interface** (9.7) when you call *into* objects of varying type.
- **Message bus** when neither side may know the other. `UGameplayMessageSubsystem` ships with Epic's
  Lyra sample, not with the engine - copy it or write the equivalent. It is local only (it never
  crosses the network) and carries notifications, never requests.

**Do not force a pattern.** One that is not in this table needs a `CONFLICT` block (14.1) naming the
problem it solves. Pooling anything that is not numerous and short-lived is complexity with no
payback.

### 9.11 Where state lives

Two questions place every piece of state: **who owns it**, and **how long it lives**. If the answers
disagree, it is two pieces of state - split it.

| State | Home | Why |
|---|---|---|
| Match rules, win conditions | `AGameModeBase` | Server-only; clients never have one |
| Match timer, team scores, phase | `AGameStateBase` | Server-owned; every client displays it |
| Player name, score, team | `APlayerState` | Per player, visible to all, survives pawn death |
| Camera, input mapping, UI ownership | `APlayerController` | Exists on the server and the owning client only |
| Health, ammo, position | The pawn or its components | Belongs to the body; dies with it |
| Settings, account, cross-level progress | `UGameInstance` or its subsystems | Survives level transitions |
| Level-scoped managers and spawners | `UWorldSubsystem` | Lifetime tied to the world |
| Per-human UI state, local preferences | `ULocalPlayerSubsystem` | One per local player; split-screen correct |
| This frame only | A local variable | - |

- **Client code asking for the GameMode is an architecture bug.** `GetAuthGameMode()` is null on
  clients by design; whatever the client needs belongs on the GameState.
- **Never `GetPlayerController(World, 0)` in gameplay code.** It is the wrong player on a dedicated
  server and in split-screen. Walk up the chain instead: component, owner, controller, PlayerState.
- **Cross-machine time** is `GameState->GetServerWorldTimeSeconds()`, never
  `GetWorld()->GetTimeSeconds()`.
- **Smells:** "I'll make a manager actor" - a World subsystem. "I'll add a singleton" - a subsystem.
  "It resets on respawn" - it belongs on the PlayerState.

### 9.12 Subsystem design

| Type | Lifetime | For |
|---|---|---|
| `UEngineSubsystem` | Process | Engine-level services; rare in game code |
| `UGameInstanceSubsystem` | Survives level loads | Save, session, settings, cross-level services |
| `UWorldSubsystem` | One world | Managers, spawners, level-scoped registries |
| `ULocalPlayerSubsystem` | One local human | Input, UI layers, local preferences |

Every subsystem does four things:

- **`ShouldCreateSubsystem` filters where it exists** - a World subsystem checks the world type, or it
  spawns into editor previews and thumbnail worlds.
- **`Collection.InitializeDependency<T>()` declares initialisation order** instead of relying on luck.
- **`Deinitialize` mirrors `Initialize` exactly** - every bind, timer and console command released
  (4.11).
- **A tickable subsystem guards `IsTickable`**, or it ticks before it is ready.

**A subsystem is a service, not a bag.** If you cannot state its job in one sentence, split it.

### 9.13 Input

- **An input action names the intent, never the key** - `IA_Interact`, not `IA_PressE`. Keys belong
  in mapping contexts.
- **Continuous input binds to `Triggered`.** Movement bound to `Started` moves for one frame - the
  classic bug. Hold actions pair `Started` with `Completed` (section 16).
- **Bind on the pawn what should die with the body** (move, fire, abilities); **bind on the
  PlayerController what survives death** (pause, scoreboard, spectate). The test: should this work
  while the pawn is dead?
- **Mapping contexts:** add one on top at a higher priority for an overlay (menu, aim); remove and
  replace for a mode change (vehicle).
- **Never `if (bIsGamepad)`** in gameplay code. Device differences are mapping-context and platform
  data.
- **Input sets intent; the movement component decides.** Never call `SetMovementMode` from an input
  handler - on a networked project the server never sees it.
- **Movement tuning is data.** `MaxWalkSpeed`, `JumpZVelocity` and `AirControl` belong in a DataAsset
  or settings, not scattered across Blueprint defaults.

### 9.14 Save data and versioning

- **Mark saved fields `UPROPERTY(SaveGame)`** and serialise with `ArIsSaveGame = true`.
- **A version field from day one**, and the migration for a format change lands **in the same
  commit** as the change.
- **Migrations are sequential** (v1 to v2 to v3), never per-version branches - players skip versions.
  Keep every migration forever.
- **Save identity and data** - a GameplayTag, an `FPrimaryAssetId`, a GUID - never a pointer, which
  means nothing on the next load.
- **Save asynchronously**, never blocking the game thread.
- **Archive a save from every shipped version and load them all in CI** (14.5). A migration never run
  against a real old save is a hypothesis.

### 9.15 GAS and AI

- **GAS is a large commitment.** Skip it for a few fixed actions, no status effects, a single-player
  prototype, or a team that does not know it. The middle path - gameplay tags plus a damage pipeline
  built like 9.8 - transfers to GAS later.
- **If you use GAS:** the ability system component lives on the PlayerState for respawning players
  (raise its `NetUpdateFrequency`) and on the pawn for AI and one-life enemies. Initialise it from one
  idempotent function called from both `PossessedBy` and `OnRep_PlayerState`. Activate abilities by
  tag, never by class. Health loss happens in exactly one place (a meta attribute resolved in
  `PostGameplayEffectExecute`). Cues are cosmetic only - they do not run on a dedicated server.
- **AI:** StateTree for new work; Behavior Trees are mature and fine - do not migrate on principle.
  Perception is event-driven; never poll for targets.

---

## 10. Async and threading

### 10.1 The rule that has no exceptions

> **All `UObject` access, creation and destruction happens on the Game Thread.**

The garbage collector, the `UObject` registry and every `UPROPERTY` pointer are not thread-safe.
Touching a `UObject` from a background thread is a data race, and a race is **nondeterministic
everywhere** - it does not fail in a way you can reproduce on demand in any configuration. What
changes between builds is only how often you get away with it: tighter optimisation and different
thread timing make a latent race surface later, not never. Passing a test pass is not evidence.

**There is no correct way to access a `UObject` off the Game Thread.** Any result produced on a
background thread must be marshalled back before it touches one:

```cpp
AsyncTask(ENamedThreads::AnyBackgroundThreadNormalTask,
    [weakSelf = TWeakObjectPtr<UInventorySubsystem>(this), payload = payloadCopy]()
{
    // Background - heavy work only, no UObject access of any kind
    const FInventoryResult result = ProcessPayload(payload);

    AsyncTask(ENamedThreads::GameThread, [weakSelf, result]()
    {
        // Back on the Game Thread - safe to resolve and use
        UInventorySubsystem* self = weakSelf.Get();
        if (!IsValid(self))
        {
            return;
        }

        self->ApplyResult(result);
    });
});
```

Note the payload is **captured by value**. The background lambda must not reach back into anything
owned by the calling frame.

**Assert the contract where it matters.** A function that must only run on the Game Thread should say
so in code, not just in a comment:

```cpp
void UInventorySubsystem::ApplyResult(const FInventoryResult& result)
{
    check(IsInGameThread());
    ...
}
```

This costs nothing in shipping and turns a rare, unexplainable crash into an immediate, obvious one.

### 10.2 Lambda captures

**Never capture a raw `UObject*` in a lambda that outlives the current frame.**

The object can be garbage-collected between the lambda being created and the lambda running. A raw
pointer will pass a null check and then read freed memory - a use-after-free, which typically does
not crash at the point of the bug and often does not crash at all until the allocation is reused.
An address sanitiser build will catch it; ordinary testing frequently will not.

**Capture `TWeakObjectPtr<T>` and resolve it inside the lambda:**

```cpp
TWeakObjectPtr<UInventorySubsystem> weakSelf(this);

RequestSomethingAsync([weakSelf]()
{
    UInventorySubsystem* self = weakSelf.Get();
    if (!IsValid(self))
    {
        return;
    }

    self->DoWork();
});
```

Rules:

- **`[this]` is only safe when the lambda is guaranteed to finish before the owner can be
  destroyed** - a same-frame inline call, a sort predicate, a `ForEach` body. Anything that crosses
  a frame boundary, an async load, an HTTP response or a background task uses a weak pointer.
- **Never capture by reference (`[&]`) in a lambda that outlives the frame.** The referenced stack
  memory is gone by the time it runs. This is the same bug as the raw pointer with none of the
  warning signs - copy what you need instead.
- **For non-`UObject` shared state, use `TSharedPtr` / `TSharedRef`**, and capture a `TWeakPtr` if
  the lambda can outlive the owner.
- **Resolve the weak pointer once at the top and null-check it.** Do not call `.Get()` repeatedly -
  between two calls the answer can change.

### 10.3 Async asset loading

Section 3.5 says soft-reference by default. This is how you load one.

Use `UAssetManager::GetStreamableManager()`. Calling `LoadSynchronous()` on the Game Thread stalls
the frame for the whole duration of the I/O, and on a cold cache that is not a small number.

```cpp
void UInventorySubsystem::RequestIconLoad()
{
    streamableHandle = UAssetManager::GetStreamableManager().RequestAsyncLoad(
        iconAsset.ToSoftObjectPath(),
        FStreamableDelegate::CreateUObject(this, &UInventorySubsystem::HandleIconLoaded));
}

void UInventorySubsystem::HandleIconLoaded()
{
    UTexture2D* loaded = iconAsset.Get();
    if (!IsValid(loaded))
    {
        UE_LOGFMT(LogGameInventory, Warning,
            "[{Obj}] [HandleIconLoaded] Icon was collected before the callback fired: {Path}",
            GetNameSafe(this), iconAsset.ToString());
        return;
    }

    ApplyIcon(loaded);
}
```

Rules:

- **The callback fires on the Game Thread.** You do not need to marshal back from it.
- **Null-check the loaded asset in the callback anyway.** The requesting object can be destroyed, or
  PIE can stop, between the request and the callback.
- **The handle is the ownership.** Store the `TSharedPtr<FStreamableHandle>` in a member; drop it and
  the asset can be collected, often in the same frame. Cancel it in `EndPlay`.
- **Define the not-yet-loaded window.** Every async load has a moment where the asset is absent; the
  code needs an explicit fallback there, with a Warning log - never a hope.
- **Every soft reference needs a named preload moment** - load one step ahead of need. A hitch is
  almost always a load that started when the asset was needed.
- **`LoadSynchronous` in a gameplay path is the bug** (13.5). It is fine in editor tools and behind a
  loading screen - as are `LoadObject` and `StaticLoadObject`, which block the same way.
- **Load only what the screen needs.** Tag DataAsset fields with `meta = (AssetBundles = "UI")` so a
  catalogue screen loads 100 icons, not 100 meshes.

### 10.4 Background work

**Prefer `Async` / `AsyncTask` and the TaskGraph over `FRunnable`.** Reach for `FRunnable` only when
you genuinely need a persistent thread with its own lifecycle - a long-lived I/O pump, an audio
capture loop - not for a one-off computation.

The pattern in 10.1 covers almost every case: do the work on a background thread, marshal the result
back to the Game Thread, resolve a weak pointer there. Prefer it to a `TFuture` continuation chain,
because `.Then()` runs on an unspecified thread and you end up hand-writing the same marshalling step
with an extra layer of indirection around it.

**The only safe shape is gather, compute, apply:**

1. **Gather** on the game thread - copy the world state you need into a plain-value snapshot.
2. **Compute** on workers - a pure function of the snapshot, writing to disjoint outputs. One output
   slot per input index needs no lock.
3. **Apply** on the game thread - re-validate the owner (a `TWeakObjectPtr`) and write the results
   back.

If phase 2 needs a lock, the split is wrong - widen the snapshot. If the gather costs more than the
compute, do not parallelise.

- **Launch new work with `UE::Tasks::Launch`**, many independent items with `ParallelFor`, and use
  `AsyncTask` where you need a named thread. A `UE::Tasks::FPipe` serialises access without blocking
  and cannot deadlock - prefer it to a mutex.
- **`ParallelFor` pays only when each item's work is substantial and independent.** Pre-size the
  output and write to `[Index]` - never `Add` to a shared container, never lock inside the body.
  Measure it both ways; `EParallelForFlags::ForceSingleThread` is the one-token A/B test.
- **`Wait()` right after `Launch()` is a slow function call.** An unintended sync is a bug, not a cost.
- **Capture by value, `MoveTemp` large payloads, and cross threads with a `TQueue`.**

If you do need an `FRunnable`:

- Implement a real `Stop()` and `Exit()`, and make the run loop actually check the stop flag.
- **Call `Stop()` and join the thread from the owner's `Deinitialize` or `BeginDestroy`.**
- **Never let a thread outlive the object that owns it.** A thread firing a callback into a destroyed
  subsystem is an intermittent crash with a stack trace that points nowhere near the cause.

### 10.5 Timers, delegates and other deferred callbacks

Every deferred callback is the same class of bug as an async lambda: something fires later, into an
object that may be gone.

- **Store every `FTimerHandle` and clear it in teardown** - `EndPlay`, `Deinitialize`,
  `NativeDestruct`. A fire-and-forget timer that outlives its owner is a crash.
- **Unbind every delegate in the matching teardown** (section 9.3).
- **A world timer does not survive a hard `OpenLevel`** (section 9.5). Anything that must survive a
  map load belongs on a GameInstance subsystem's timer manager, not the world's.

### 10.6 Animation Blueprints

**Gather on the game thread, derive on a worker.** `NativeUpdateAnimation` runs on the game thread:
copy what the graph needs - velocity, flags, aim - out of the pawn and its components into member
variables, and do nothing else there. `NativeThreadSafeUpdateAnimation` runs on a worker before the
graph updates: compute everything derived from those copies there - blend weights, speed bands,
lean. The engine's own header gives the same advice (`AnimInstance.h`).

- **The thread-safe update never touches another `UObject`.** It reads only what the game-thread
  update copied; that is what makes it safe.
- **In Blueprint, mark AnimBP functions Thread Safe and read through property access**, keep
  multi-threaded animation update on, and fix every thread-safety warning the Anim Blueprint
  compiler raises.
- **Animation is usually the largest game-thread line.** Use update rate optimisation (URO) and the
  animation budget allocator for crowds, and tune by screen size, not distance.

---

## 11. Networking and replication

**This section applies if the project replicates.** If it does not, read 11.1 and skip the rest.

### 11.1 Decide before the first feature

**Retrofitting replication is a rewrite, not a feature.** Authority checks, RPC boundaries and
replicated state change who owns every piece of state in the game - they are not something you layer
on afterwards.

If there is any realistic chance of multiplayer, **write authority-aware code from the start even in
a single-player build.** Guarding a state change with `HasAuthority()` costs one line and is a no-op
in standalone. Not having done it costs a rewrite.

If the project is definitively single-player, say so in the project README and skip this section
rather than half-applying it. Code that is authority-aware in some places and not others is worse
than code that is consistently neither.

### 11.2 Authority model

> **The server is the truth. The client is a guess.**

Every mutation of game state - spawning, destroying, state machine advances, inventory changes -
runs on the server and replicates down. The client handles input, local prediction and cosmetics.

| Check | Method | When to use |
|---|---|---|
| Running on the server | `HasAuthority()` | Before any authoritative write |
| This is our own pawn | `IsLocallyControlled()` | Input, and local cosmetic feedback |
| Dedicated vs listen vs client | `GetNetMode()` | When the three genuinely differ |

**Authority-gate every mutation.** A function that writes replicated state either returns early when
`!HasAuthority()`, or is only reachable through a `Server` RPC.

```cpp
void AQuestVolume::AdvanceToNextStep()
{
    if (!HasAuthority())
    {
        UE_LOGFMT(LogGameQuest, Warning,
            "[{Obj}] [AdvanceToNextStep] Called without authority - no-op",
            GetNameSafe(this));
        return;
    }

    // Authoritative logic only below this line
    currentStep->Execute(this);
}
```

A client writing replicated state directly **works silently in single-player PIE and fails silently
on a dedicated server** - the worst failure mode there is, because the code that is wrong is the code
that tested fine.

**Where `HasAuthority()` lives:** it is an `AActor` method.

- **In an `AActor`** - call it directly, as above.
- **In a `UActorComponent`** - `GetOwner()->HasAuthority()`, null-checked.
- **In a `UObject` or a subsystem** - there is no authority to ask about. A plain `UObject` has no
  network role. Route the decision through the owning actor, or check
  `GetWorld()->GetNetMode() != NM_Client` if you genuinely only need "am I not a client".

That last case matters here, because section 9 pushes service logic into subsystems. **A subsystem is
not a network actor.** If a subsystem drives authoritative state, it must do so through an actor that
has authority - usually the GameMode, GameState or a PlayerController - not by reasoning about the
net mode on its own.

### 11.3 Replicated properties

```cpp
/** Current health. Read by clients, written only by the server. */
UPROPERTY(Replicated)
int32 currentHealth;

/** Active quest. Clients repaint the HUD from OnRep_ActiveQuestTag. */
UPROPERTY(ReplicatedUsing = OnRep_ActiveQuestTag)
FGameplayTag activeQuestTag;

/** RepNotify for activeQuestTag. The parameter carries the PREVIOUS value. */
UFUNCTION()
void OnRep_ActiveQuestTag(const FGameplayTag& previousTag);
```

Rules:

- **Register every replicated property in `GetLifetimeReplicatedProps`.** What happens to one you
  forget depends on two console variables, and both defaults are silent in UE 5.7 (`NetCVars.cpp`):
  - `Net.AutoRegisterReplicatedProperties` (default **on**) registers it for you with no condition. It
    replicates - to everyone - so a property you meant to be `COND_OwnerOnly` leaks to every client.
  - With auto-registration off, it never replicates and the client holds its constructor default
    forever. `Net.EnsureOnMissingReplicatedPropertiesRegister` (default **off**) makes that an
    `ensure`.

  **On a replicated project, set auto-registration to `0` and the ensure to `1`** under
  `[ConsoleVariables]` in `DefaultEngine.ini`, and fix everything the ensure reports - plugin classes
  included - before committing the setting. A missing registration is then loud instead of silently
  wrong. If a property is deliberately not replicated in a subclass, say so with
  `DISABLE_REPLICATED_PROPERTY`.
- **Name the `OnRep_` after the property it responds to, not after what it does.**
  `OnRep_ActiveQuestTag`, not `OnRep_QuestChanged`. The engine matches on the declared name, and a
  reader needs to see which property fired it.
- **The `OnRep_` parameter holds the previous value.** The member itself already carries the new
  value by the time the callback runs. Take the parameter when you need the delta; omit it when you
  do not.
- **`OnRep_` does not fire on the server.** It is a client-side change notification. Logic that must
  run on both sides goes in a separate function, called from the mutation site on the server **and**
  from the `OnRep_` on clients.
- **Replicate state, not events.** `currentHealth` is state; "took damage" is an event and belongs in
  an RPC, or in a local response to the state change.
- **Do not replicate what a client can derive**, and **never replicate UI state.** Widgets are local;
  replicate the data the UI reads.
- **The test for property versus RPC:** *if a player joined right now, would they need to know this?*
  Yes - a replicated property; late joiners get it. No - an RPC. A door opened by a multicast is
  closed for everyone who joins later.
- **Call `Super::GetLifetimeReplicatedProps` first.** Forgetting it silently stops every inherited
  property replicating.
- **Clients never see intermediate values** - replication sends the latest state, not every change.
  Never count events by diffing a replicated value.
- **Replicated means readable.** Anything replicated to a client is in that client's memory;
  `COND_OwnerOnly` is the only defence against another player reading it.
- **`OnRep_` also fires on initial replication and on re-entering relevancy, and is skipped when the
  value returns to what the client already had.** Use `REPNOTIFY_Always` for values that can
  oscillate (health, ammo).
- **Collections that change more than rarely use `FFastArraySerializer`**, mutated only through the
  list's own methods with `MarkItemDirty` / `MarkArrayDirty`. A plain `TArray` resends the whole
  array.
- **Quantise vectors** (`FVector_NetQuantize`, `_10`, `_100`, `_Normal`) wherever full precision is
  not needed.
- **Replicated subobjects use the registered list** - `bReplicateUsingRegisteredSubObjectList = true`,
  with matched `AddReplicatedSubObject` / `RemoveReplicatedSubObject` calls.

**Use replication conditions deliberately - the default sends to everyone:**

| Condition | Receivers |
|---|---|
| `COND_None` (default) | All clients |
| `COND_OwnerOnly` | The owning client only |
| `COND_SkipOwner` | Everyone except the owner |
| `COND_InitialOnly` | Once, on spawn or join |

```cpp
void AGamePlayerState::GetLifetimeReplicatedProps(
    TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);

    DOREPLIFETIME(AGamePlayerState, currentHealth);

    // Private economy - only the owning client has any use for this
    DOREPLIFETIME_CONDITION(AGamePlayerState, currency, COND_OwnerOnly);
}
```

**The initialisation race.** The controller, the PlayerState and replicated properties arrive in any
order, possibly after `BeginPlay`. Write one idempotent `TryInitialise()` that checks its own
preconditions, and call it from `BeginPlay`, `PossessedBy`, `OnRep_Controller` and
`OnRep_PlayerState` - whichever arrives last does the work.

**Cutting bandwidth, in this order:** replicate less, conditions, lower frequencies, fast arrays,
quantisation, a property instead of a frequent multicast, dormancy, custom `NetSerialize`, push model.
Exhaust "send less" before "send it smaller".

### 11.4 RPCs

Three kinds. Choose by who initiates and who executes.

| Type | Macro | Initiator to executor | Use for |
|---|---|---|---|
| Server | `UFUNCTION(Server, Reliable, WithValidation)` | Owning client to server | Input-driven requests |
| Client | `UFUNCTION(Client, Reliable)` | Server to owning client | Targeted notifications |
| Multicast | `UFUNCTION(NetMulticast, Unreliable)` | Server to server + all clients | Cosmetic fire-and-forget |

```cpp
// Header
UFUNCTION(Server, Reliable, WithValidation)
void ServerRequestInteract(AActor* target);

// .cpp - you implement the _Implementation and _Validate halves; UHT generates the thunk
void AGamePlayerController::ServerRequestInteract_Implementation(AActor* target)
{
    if (!IsValid(target))
    {
        return;
    }

    // Authoritative logic - this body only ever runs on the server
}

bool AGamePlayerController::ServerRequestInteract_Validate(AActor* target)
{
    // Returning false disconnects the sender as a cheat. Reserve it for
    // arguments a legitimate client could never send.
    return IsValid(target);
}
```

Rules:

- **`Reliable` is guaranteed and ordered. Use it for any game-state change.**
- **`Unreliable` is droppable. Use it for cosmetics** - a one-shot effect, a hit sound - where losing
  a packet is acceptable. **Never send a state change unreliably.**
- **Reliable is a finite resource.** The reliable buffer can overflow and disconnect the client.
  Do not put a per-frame call on a reliable RPC.
- **Always add `WithValidation` to a `Server` RPC.** Without it there is no validation step at all -
  the RPC executes with whatever arguments arrive over the wire. The `_Validate` function is your one
  clean opportunity to reject a hostile client.
- **A `Server` RPC only routes if the calling client owns the actor.** No warning, no error - it
  simply never executes on the server. Ownership, not proximity, is what decides.
- **A `NetMulticast` RPC does not depend on ownership** - it depends on the actor **replicating** and
  being **net-relevant** to each client. It does not reach a client who joins later, and it does not
  reach anyone the actor is not relevant to. Multicast is for cosmetic, fire-and-forget effects only.
- **Never fire an RPC from a constructor or from `GetLifetimeReplicatedProps`.** Both run before any
  connection exists.
- **The client sends intent, never outcome.** "Fire at this point" is a request; "I hit them for 87"
  is a cheat. Never accept a client's hit result "for performance".
- **`_Validate` rejects only the impossible or malformed** - failing it disconnects the player.
  Gameplay rules are re-checked in `_Implementation`, assuming the client checked nothing.
- **Call an RPC by its plain name**, never `_Implementation`.
- **`Unreliable` also suits streaming data that is superseded shortly after** - a reliable stream
  stalls behind one lost packet. `NetMulticast` is throttled; never use it as a state channel.

### 11.5 Relevancy and update frequency

`NetUpdateFrequency` controls how often the server considers an actor for replication. **The default
is 100 Hz**, which is far more than almost anything needs. It is the most common replication
performance leak in multiplayer projects, and nothing warns you about it.

Set it in the constructor:

```cpp
AGameCharacter::AGameCharacter()
{
    bReplicates = true;

    SetNetUpdateFrequency(30.0f);
    SetMinNetUpdateFrequency(10.0f);   // Floor used when the actor is deprioritised
}
```

**Check which form your engine version exposes.** `NetUpdateFrequency` and `MinNetUpdateFrequency`
were public members historically and moved behind `SetNetUpdateFrequency()` /
`GetNetUpdateFrequency()` accessors during UE 5. Depending on your version, direct assignment may
compile, may warn as deprecated, or may fail outright. **Prefer the accessor where it exists** - and
if you are copying an older sample that assigns the member directly, that mismatch is why it does not
build.

| Actor type | Typical frequency |
|---|---|
| Player-controlled character | 30-60 Hz |
| AI or NPC character | 10-20 Hz |
| Interactive world object | 5-10 Hz |
| Rarely-changing actor | 1-5 Hz |

Relevancy is the bigger lever, and it is free:

- **An actor whose state never changes at runtime should not replicate at all.** Leave `bReplicates`
  false, or turn it off on the authority. A non-replicating actor costs nothing per tick.
- **`bAlwaysRelevant` defaults to false, and should stay that way.** Setting it true opts the actor
  out of distance and visibility culling, so it replicates to every client for the whole session.
  Reserve it for things that genuinely are always relevant - GameState, PlayerState.
- **A non-relevant actor sends no packets regardless of its update frequency.** Fix relevancy before
  you tune frequency.
- **Dormancy is the cheapest lever and the most forgotten.** An actor that rarely changes - a door, a
  chest, a spawner - starts `DORM_Initial`. **Call `FlushNetDormancy()` before changing a dormant
  actor**, or server and clients disagree forever, silently.
- **`NetPriority` decides what survives when bandwidth saturates.** The PlayerState has a low update
  frequency by default - raise it if you put fast-changing data there.
- **Work through these in order before any architecture change:** relevancy, dormancy, frequency,
  priority, then an audit that deletes unused properties and makes the rest owner-only where it can.
  Replication Graph and Iris are mutually exclusive replication systems; justify either with a
  server capture (13.8).

### 11.6 Naming

Extending the verb vocabulary in section 4.3 - an RPC prefix states **where the function runs**, and
is mandatory because nothing else at the call site tells you:

| Kind | Prefix | Example |
|---|---|---|
| `Server` RPC | `Server` | `ServerRequestInteract` |
| `Client` RPC | `Client` | `ClientNotifyPurchaseFailed` |
| `NetMulticast` RPC | `Multicast` | `MulticastPlayHitEffect` |
| RepNotify handler | `OnRep_` | `OnRep_ActiveQuestTag` |

**Underscores in function names are reserved for engine-required forms** - the `OnRep_` prefix and
the `_Implementation` / `_Validate` suffixes (11.4). The only other underscore in a name is the
polymorphic class family in 4.4, and the bind-name member in 7.4. RPC prefixes stay PascalCase and unbroken - `ServerRequestInteract`, not
`Server_RequestInteract` - consistent with the verb-first rule in 4.3. Pick one form and hold it;
a codebase with both is one where nobody can grep for either.

### 11.7 Testing

- **Test in PIE with at least two clients**, and **with Run Under One Process disabled** at least once
  per feature. Single-process PIE shares statics and hides a whole category of bug.
- **Test as a dedicated server, not only as a listen server.** A listen server is both authority and
  client, so it silently masks missing `OnRep_` calls and missing authority checks.
- **Keep simulated latency and loss on in your normal setup** (`Net PktLag=120`, `Net PktLoss=3`), not
  only during bug hunts. Prediction bugs are invisible at 0 ms.
- **Default PIE to a dedicated server**, and package and run a real dedicated server build weekly from
  the first month.
- **On a listen server the host has both authority and local control** - code that handles each
  separately fires twice there.
- **Watch the bandwidth.** `stat net` and the Network Profiler will show you a 100 Hz actor long
  before a player reports it.

### 11.8 Push model and Iris

Both are **off by default in UE 5.7 and 5.8** (`Net.IsPushModelEnabled`,
`net.Iris.UseIrisReplication`). Decide on both alongside the replication decision in 11.1, and write
the answer in the README.

- **Push model** lets game code tell the network system what changed, instead of the server comparing
  every replicated property on every net update. Enable it with `Net.IsPushModelEnabled=1` and a
  `NetCore` dependency, register properties with `DOREPLIFETIME_WITH_PARAMS_FAST` and
  `bIsPushBased = true`, and call `MARK_PROPERTY_DIRTY_FROM_NAME` at every write. **Route every write
  through a setter** - a write that is not marked dirty does not replicate. Push model pays off for
  many properties that change rarely; it is the last step of the bandwidth order in 11.3, not the
  first.
- **Iris** is Epic's replacement replication system - production-ready in 5.8 according to Epic's
  release notes, but still opt-in. It changes how replication is configured and
  prioritised, not the rules in this section: authority, conditions, RPCs and `OnRep_` all still
  apply. Do not switch a project to it mid-development without a spike on a branch first.

### 11.9 Prediction

- **Predict only what passes all three:** would the player feel the latency; does the client have all
  the information; is being wrong cleanly reversible? Never predict damage to others, server-only
  information or randomness.
- **Custom movement goes inside the CharacterMovementComponent**, with its own
  `FSavedMove_Character`: every custom field captured in `SetMoveFor` and restored in `PrepMoveFor`,
  and intent packed into the four custom compressed flags. Capture without restore is an
  intermittent desync that LAN testing never shows.
- **A custom movement mode reads only velocity, acceleration, intent flags and the world; uses no
  randomness; and checks its exit condition first.**
- **Corrections are not failures.** The goal is zero corrections the player can feel - watch them
  with `p.NetShowCorrections 1`.
- **Server-side rewind** for hit registration is a design decision - it moves the unfairness to the
  victim. Cap the rewind window.

---

## 12. UMG and Slate rules

### 12.1 BindWidget

`meta = (BindWidget)` matches on **object name**, case-insensitively, and is a **hard compile
requirement** - the Blueprint will not compile if the widget is missing.
`meta = (BindWidgetOptional)` is the soft form.

A widget may move anywhere in the tree as long as its **name survives**. A rename breaks the bind.

### 12.2 Widget structure

- **Use the right panel.** An `Overlay` with two side-by-side children is a `HorizontalBox` written
  wrong - Overlay stacks, it does not lay out.
- **Strip wrapper hierarchy.** A single-child `Overlay` or `ScaleBox`, a `ScaleBox` around an
  already-fixed-size `SizeBox`, a `Spacer` where slot padding does the same job, a `RenderTransform`
  scale where a brush `ImageSize` would do - each is an extra layout pass and a place for alignment
  to go wrong.
- **`bOverride_*` flags left off make the value inert.** A property you set that does nothing is
  worse than one you did not set.
- **Name by role, never by engine default.** `headerTitle_Text`, not `TextBlock_45` (form: 7.4). Set both `Name`
  and `DisplayLabel` to the same string.
- **One widget, one job.** A widget that both fetches and displays is two widgets.

### 12.3 T3D pastes

When exchanging widget trees as T3D text between developers:

- Apply everything in 12.2 before sending - a paste-ready tree, not a dump.
- **Preserve every `BindWidget` name exactly.**
- **State that the old root must be deleted before pasting.** UMG suffixes duplicates (`back_Btn_1`)
  and silently breaks every bind.
- **Flag layout bugs you find on the way** rather than quietly fixing them - the other developer
  needs to know.

### 12.4 Slate

If you drop to Slate, two hard rules from section 16 apply:

- **Never resolve layout by walking an engine widget's `GetChildren()`.** Engine internals are private
  layout and change between versions. Use the published `SLATE_ATTRIBUTE` / `SLATE_ARGUMENT`, or the
  style struct, or subclass and override the virtual.
- **Check whether the engine widget already implements the input hook** before you override it. One
  owner per input.

### 12.5 Player-facing text

- **Everything a player reads is `FText`**, never `FString` or `FName`. Only `FText` is gathered for
  localisation.
- **C++ literals use `LOCTEXT` / `NSLOCTEXT`**, with `LOCTEXT_NAMESPACE` defined and undefined inside
  the `.cpp`. In Blueprint and assets, leave player-facing text localisable, not culture-invariant.
- **Build sentences with `FText::Format` and named arguments**, never by concatenating strings. Word
  order changes between languages.
- **Numbers, dates and times go through `FText::AsNumber` / `AsDate` / `AsTime`** so they follow the
  player's culture.
- **Wire and save data stay `FString`.** Convert at the UI boundary, not before.
- **Never `FText::FromString` on player-facing text** - it is invisible to localisation. Use
  `LOCTEXT` or a string table.
- **Format with `FText::AsPercent`, `AsCurrency` and `AsTimespan`** as well, never by hand. Never
  hard-code a key name in text - show the current binding's glyph (`UCommonActionWidget`).
- **`FName` is for identity** (map keys, bones, sockets, tags), **`FString` for manipulation**
  (paths, parsing, logs), **`FText` for anything a player reads.**

### 12.6 UI architecture and cost

**A widget displays. It never owns, decides or polls.** The test: delete every widget, and the game
is still fully playable and correct.

- **UI is client-only**, owned by the PlayerController or a `ULocalPlayerSubsystem` - never the pawn.
  A dedicated server has no widgets at all.
- **Lifecycle:** `NativeOnInitialized` for one-time setup; `NativePreConstruct` for appearance only
  (guard editor-only work with `IsDesignTime()`); `NativeConstruct` binds and **seeds the initial
  value**; `NativeDestruct` unbinds, mirroring Construct exactly. `NativeTick` - don't.
- **Update by push, not pull.** UMG property bindings are evaluated every frame, and `NativeTick`
  polling is the same cost written by hand. Push with a delegate on change, or use a view model
  (MVVM, `FieldNotify`) - the third widget that needs the same value is the point to introduce one.
- **Screens are pushed, not opened.** With Common UI, set the Game Viewport Client class to
  `CommonGameViewportClient` (without it, input routing silently does nothing), give every
  activatable widget a desired focus target (`NativeGetDesiredFocusTarget`), and push screens onto
  layer stacks through a subsystem.
- **Widget count is the cost.** Toggle with `Collapsed`, not `Hidden` - hidden still pays for layout.
  Non-interactive widgets are `HitTestInvisible` or `SelfHitTestInvisible`; list views recycle their
  entries; an `InvalidationBox` helps only static content and makes animated content slower; every
  world-space widget is its own render target - project to a screen canvas where you can.
- **Budget the HUD** (a project number - 0.5 ms is typical) and measure with `stat slate` and the
  Widget Reflector.

---

## 13. Performance and platform

### 13.1 Platform constraints

| Platform | Constraints |
|---|---|
| **Mobile** (Android/iOS) | Aggressive LOD. Texture streaming. Strict draw-call and material-complexity budgets. **Never multiple high-fidelity characters in the same view.** |
| **Remote / Pixel Streaming** | Minimise per-frame messages over the streaming data channel, and batch state updates. Latency is the budget, not framerate. (This is the browser-to-engine channel, unrelated to the replication RPCs in section 11.) |
| **PC** | No artificial constraints, **but must not break the lowest target platform's build.** |

**Whichever platform is most constrained is the binding one, and on a mobile project that is
mobile.** "It runs fine on my 4090" is not a result.

If the project ships on both desktop and mobile, every interactive UI system has two paths (9.1) and
the mobile one is the one under pressure. **If the project is desktop-only, do not build the second
path** - an unused Mobile widget tree is maintenance cost with no user.

### 13.2 Measure, then decide

Six principles govern every performance decision:

1. **The bottleneck is singular.** One stage - game thread, render thread, RHI thread or GPU - sets
   the frame time. Work anywhere else returns nothing.
2. **Measure on the target, in the build you ship.** Profile a **Test** build (Shipping-like, with
   stats and the console) on the lowest target device. A Development editor build is a different
   program, and PIE can rank the stages in the wrong order, not merely inflate them.
3. **Optimise the distribution, not the mean.** Players feel the 99th percentile and the hitch. A
   change that lowers the average and raises p99 is a regression.
4. **Deletion beats optimisation.** Before making something faster, ask whether it should run at
   all (3.12).
5. **Instrument once, benefit forever** (13.6).
6. **A fix without an after-capture did not happen.** Capture, hypothesise, change, capture again -
   and keep both numbers.

**Milliseconds are the only unit.** Frame rate is a reciprocal and misstates severity - "we lost 15
fps" is 1.2 ms at 120 fps and 11 ms at 45. State the target in fps once, then work in ms.

**Start every investigation with `stat unit`:**

| Highest line | You are | Look at |
|---|---|---|
| Game | Game-thread bound | Tick count, gameplay code, AI, animation, replication |
| Draw | Render-thread bound | Primitive count, culling, draw submission |
| GPU | GPU bound | Shading, overdraw, resolution, shadows, Lumen, Nanite |
| RHIT | RHI-thread bound | Submission count, driver cost |
| Numbers fine, feels bad | Variance | Hitches and frame pacing (13.5) - `stat unitgraph` |

Then one stat group for that stage, then a trace. Does `r.ScreenPercentage 50` halve the GPU time?
You are pixel-bound. **Read the count before the time** - 340 calls of 6 microseconds is an
algorithm problem no micro-optimisation fixes, which is why `dumpticks` and `obj list` come first.

**A budget has line items and owners.** The project README writes the frame budget per target:
ceiling minus a reserve, divided into lines (game thread, animation, UI, GPU passes, memory, VRAM),
**each with a named owner**, judged on p99 and hitches per minute. A line with no owner is a wish.

- **Check the Size Map** on any Blueprint or widget that references content.
- **Build a packaged build for the lowest target platform early and often.** Problems that only
  appear in a cook are the expensive kind, and they compound the longer you wait to find them. See
  section 15 for the editor-versus-packaged symptom list.

### 13.3 Getting assets into the cook

The cooker includes what it can reach from the maps being cooked and from the Asset Manager. Nothing
else ships.

- **Register every data-driven asset type as a Primary Asset Type** - Project Settings > Asset
  Manager, with its directory and cook rule. An asset reached only through a soft path or a string is
  otherwise absent from the build (section 15, item 19).
- **Derive those DataAssets from `UPrimaryDataAsset`**, which supplies `GetPrimaryAssetId` for you.
- **Load them by `FPrimaryAssetId` through `UAssetManager`**, not by path, so the code and the cook
  agree on what exists.
- **After adding a new asset type, check a packaged build's contents** with the Asset Audit window.
- **Set a cook rule per type** (`AlwaysCook`, `DevelopmentCook`, `NeverCook`), and decide chunk
  assignments when you decide asset types - chunking cannot be retrofitted.
- **Default every asset reference in a DataAsset to soft.** Hard references come from `TObjectPtr`
  and `TSubclassOf` properties, `Cast To BP_X` nodes, Blueprint-typed variables, Details-panel
  default values, child actor components and DataTable rows that point at assets. Soft pointers,
  `FPrimaryAssetId`, interfaces and tags create none.
- **Find reference debt with a loop:** the Size Map shows what it costs, the Reference Viewer (depth
  raised) shows which edge pulled it in; fix that one node and repeat.
- **Cook nightly from the first week.** Cook-only bugs exist nowhere else. Treat incremental cooking
  as an iteration accelerator, and validate against a clean cook before every milestone.
- **Exclude `Developers/` and `TEMP/` from the cook** (Project Settings > Packaging > Directories to
  never cook) - see 8.2.

### 13.4 Memory, GC and pooling

- **Memory is four budgets:** physical memory (the OS kills you), VRAM (on PC, overcommit degrades
  into erratic GPU time), address space, and **object count**. GC cost scales with the number of
  `UObject`s and references, not with bytes - a project under its byte budget can still hitch every
  few seconds.
- **Track `UObject` count beside bytes** (`obj list`, `stat gc`). Every component is an object: 400
  NPCs with ten components each is 4,400 objects.
- **Read `memreport -full` in pairs, from a packaged build.** One report is usage; two are the
  answer. Editor reports include the editor.
- **Tag every system you own with an LLM tag** (`LLM_DEFINE_TAG`, `LLM_SCOPE_BYTAG`) when you write
  it, named like its trace scopes. Untagged memory has no budget line and no owner.
- **Find reference leaks with `obj refs name=X`.** A `UObject` held alive by a forgotten reference is
  correctly tracked memory, so allocation tools cannot see it.
- **Pool what is numerous and short-lived** - projectiles, impacts, damage numbers, one-shot VFX,
  list rows - and nothing else. `Reset()` must clear **every** member; the classic pool bug is the one
  field nobody remembered.
- **Blurry textures are a budget conversation** (`stat streaming`): the scene wants X MB and the pool
  has Y. UI textures are set to `Never Stream`, or they pop.

### 13.5 Hitches and loading

A hitch is one frame that did a second's work. Report **hitches per minute** alongside p99. Nearly
every hitch is one of five things:

| Archetype | Tell | Fix |
|---|---|---|
| Synchronous load | Tied to a gameplay event; `FlushAsyncLoading` in the trace | Async load one step ahead (10.3) |
| PSO / shader compile | **First time only**, never again | PSO precaching plus a bundled PSO cache; test on a cold machine |
| Garbage collection | Regular, no gameplay link | Fewer objects, clustering, incremental GC (13.4) |
| Spawn burst | Exact gameplay-event link | Pool, stagger across frames, or do not make them actors |
| Level streaming | Same place on the map | Smaller cells, fewer actors per cell, an earlier loading range |

- **Ask "does it happen again?" first** - no means PSO. Then look two or three frames *before* the
  spike; the cause is often there.
- **Stagger one-off work.** 300 spawns in one frame is a freeze; 30 a frame for ten frames is
  invisible.
- **Never fix pop-in by blocking.** It trades a visual bug for a freeze.
- **Loading is the most build-sensitive cost in the engine.** Only a packaged IO Store build, on the
  slowest target storage, counts.

### 13.6 Instrumentation

A subsystem is not done until it has all four:

1. **A CPU scope on its update** - `TRACE_CPUPROFILER_EVENT_SCOPE(Quest_Tick)`, named `System_Verb`
   so traces group by owner. Never the `_TEXT` form on a hot path; it allocates.
2. **A counter on every queue, pool and active set** - `TRACE_DECLARE_INT_COUNTER` and
   `TRACE_COUNTER_SET`.
3. **A CSV stat matching its budget line**, with the same name (`CSV_SCOPED_TIMING_STAT`).
4. **An LLM tag** (13.4).

Scope entry points and phases, not every function - a scope earns its place at about 50
microseconds. **Bookmark the game's state machine** (`TRACE_BOOKMARK` on wave start, level loaded),
never per frame. These macros compile to nothing when their facility is disabled, so they need no
`#if`.

### 13.7 Content costs

- **Chase draw calls only when Draw or RHIT is the highest `stat unit` line.** One parent material
  with many instances batches; many materials do not.
- **Review materials by screen coverage, not instruction count.** Cost is instructions x pixels x
  layers, so a cheap translucent effect covering the screen twice outcosts a complex opaque one.
  Budget VFX overdraw in screen multiples, and test effects together, not alone.
- **Static switches multiply shader permutations** - ten switches, 1,024 variants. Use Quality
  Switches for scalability and static switches sparingly.
- **Count the shadow-casting lights** before tuning shadows. Virtual Shadow Map cost comes from
  invalidation: moving lights, moving geometry, LOD changes, WPO.
- **Wrong bounds defeat every culling stage at once.** `FreezeRendering`, then flying the camera out,
  finds most culling problems in two minutes.
- **Nanite meshes need no authored LODs; everything else still does.** Nanite is a per-category
  measurement, not a project-wide policy.
- **Handhelds:** measure at thermal steady state (ten minutes in, unplugged), or the number is
  fiction. Scalability tiers may change resolution, post, GI and shadows - never gameplay visibility
  or fairness. Dynamic resolution is the answer to throttling.

### 13.8 Server performance

- **Server cost scales with actors x connections.** Four players is a different program from 64.
  Profile a headless dedicated server at the **target player count, with bots**, from pre-production.
- **A replicated property costs a comparison per connection per tick** whether or not it changed -
  server CPU before bandwidth.
- **Run `dumpticks` on the server separately**, and wire significance up server-side. Nothing is
  off-screen to a server, so AI, animation for authoritative hits and physics never cull themselves.
- **Work through the levers in 11.5 before any architecture change**, and record the deferral with its
  number.

### 13.9 Regression gates

- **Performance is defended per commit or not at all.** A deterministic perf test - fixed level,
  route, seed, build configuration and device - runs on dedicated hardware in CI (Gauntlet drives
  it), captures CSV, and **fails the build** when a budget line's p99, the hitch count, peak memory,
  peak VRAM or the `UObject` count passes its threshold. A warning is ignored by week three.
- **Measure the noise floor first** - ten runs of the same build - and set the failure threshold well
  above it, or nobody trusts the gate.
- **A failure belongs to whoever caused it, the day it lands.** The gate is never disabled
  "temporarily"; a budget change is a recorded product decision.
- **Trend as well as gate.** A gate catches cliffs; a trend catches 0.3 ms a week.
- **Stop a fix being undone.** Record symptom, measurement, the wrong hypothesis, root cause, fix and
  result, and leave a two-line `DO NOT UNDO` comment on the code naming the capture that justified
  it.

---

## 14. Working style

### 14.1 How we work

- **Plan before implementing.** Full conflict analysis before code. Identify structural mismatches
  before writing a line.
- **Diagnosis before code.** Root cause identified and agreed before a fix is written. A fix applied
  to a symptom you have not explained will come back.
- **Flag conflicts in a `CONFLICT` block, before any code.** If new work genuinely conflicts with a
  pillar, a rule in this document or the existing architecture - or you hit an include-path or
  ordering problem that changes the plan - raise it in this fixed format and wait for a written
  answer:

  ```
  CONFLICT
  Rule:      <pillar or section, e.g. Pillar 2 / 9.4>
  Existing:  <what the code or design does now>
  Requested: <what the change needs>
  Options:   A) <approach> - <trade-off>
             B) <approach> - <trade-off>
  Recommend: <A or B, and why>
  ```

  A fixed format makes a conflict reviewable and hard to skip. People and assistants (14.2) use the
  same block.
- **Present architectural forks as explicit Option A / Option B with trade-offs** - before the
  decision, not after.
- **Explain the why.** When you introduce a pattern, explain the reasoning: in the PR, in the review,
  in the doc. **A pattern nobody else understands is a liability regardless of whether it is
  correct.**
- **Do not assume a concept is understood because it appears in existing code.** Existing code is
  evidence someone wrote it, not evidence the team understands it.

### 14.2 Working with an AI assistant

An assistant can write one file or twenty. **The right amount is set by how well you understand what
it is about to do - not by the size of the task.**

> **Ask for the plan first. If you can restate it and you agree with it, let the assistant do the
> whole thing. If you cannot, make it work one file at a time.**

**When you do not fully understand the plan** - unfamiliar system, unfamiliar engine area, or an
approach you have not seen before - have it go **one file at a time**: write a file, stop, show you,
wait. The point is the stopping. It gives you a place to say "that is not what I meant" while the
change is one file deep instead of twenty, and it lets you redirect mid-way when you realise the
approach is wrong or the requirement has moved. A wrong direction caught at file one costs a
conversation; caught at file twenty it costs the whole change.

**When you do understand the plan and agree with it**, let it run the whole thing in one go.
Stopping it every file at that point is pure overhead - you already know what is coming, and
reviewing twenty small diffs is harder than reviewing one coherent change.

The same calibration applies to anything hard to reverse: a batch rename, a refactor across many
files, anything touching content. Understand it first, or take it a step at a time.

Three things that do not change either way:

- **You own the output.** Code an assistant wrote is code you are committing under your name. Read
  it. "The AI wrote it" explains nothing in a review and nothing in a post-mortem.
- **Every rule in this document applies identically** to code an assistant wrote - naming, comments,
  logging, categories, the checklist in section 17. Give the assistant this document (see section 18)
  so it starts from the same standard rather than being corrected into it.
- **A large diff you did not understand is not speed.** It is debugging deferred to a worse moment,
  usually to whoever opens the file next.

### 14.3 Source control

- **Binary assets go through Git LFS** - `.uasset`, `.umap`, and source art and audio - configured in
  `.gitattributes` before the first asset is committed. Moving them into LFS later rewrites history.
- **Lock a `.uasset` or `.umap` before you edit it** (`git lfs lock`, or the editor's source-control
  integration). Binary assets cannot be merged; without a lock, the second person's work is lost.
- **Fix up redirectors after a move or rename** (right-click the folder > Fix Up Redirectors) and
  commit the fix-up with the move, not later.
- **Never commit** `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/` or `.vs/`.
- **Git + LFS with locking suits a small, engineering-led team; Perforce with exclusive checkout suits
  a team with artists editing daily.** Decide in the README. Either way, keep feature branches short -
  binary assets diverge and cannot be merged back.
- **One File Per Actor** ends level merge conflicts and creates thousands of small files; budget for
  that on Git.
- **Rename a C++ class or property with a Core Redirect in the same commit** (3.8).
- **Commit messages:** an imperative summary under 72 characters, prefixed by the system -
  `Quest: Reset transition phase on map arrival`. A body when the why is not obvious. One logical
  change per commit.

### 14.4 Automated tests

- **Pure logic gets an automation test** - `IMPLEMENT_SIMPLE_AUTOMATION_TEST` or the spec form
  (`BEGIN_DEFINE_SPEC`), named `<Project>.<System>.<Case>`, run from the Session Frontend or the
  `Automation RunTests` command. Parsers, save migration, economy maths and anything with a bug
  history come first.
- **Gameplay flow gets a functional test** - an `AFunctionalTest` actor in a dedicated test map, which
  runs the real systems and calls `FinishTest` with a result.
- **A bug fix adds the test that would have caught it**, wherever the bug is testable.
- **Tests run before a merge to the main branch.** A failing test blocks the merge.
- **Test pure logic first** - damage rules, inventory rules, save migration, state machines.
  Functional tests are slow and brittle; add them for flows that have broken before, not for coverage.

### 14.5 Continuous integration

Every gate fails the build, or it is theatre.

| Tier | Time | Contents |
|---|---|---|
| Every commit | ~10 min | Compile (editor and game), automation tests, asset validators (18), reference budget check |
| Nightly | 1-2 h | Cook and package, dedicated server build, perf and memory against budget (13.9), functional tests |
| Weekly | Longer | Test and Shipping builds on every platform, a full clean cook, loading archived saves from every shipped version (9.14) |

- **Commandlets used in CI return non-zero on failure** and never prompt, open a dialog or wait for
  input - run them with `-unattended -nopause -nosplash`.
- **Archive symbols for every build from day one**, and bake the version and changelist into the
  binary. A crash without symbols is a list of hex addresses.
- **Instrument telemetry before you need it** - frame-time percentiles, crash rate, load times - and
  collect nothing you cannot name a decision for.
- **Pre-ship, every check runs in a packaged Shipping build on the lowest target platform.** The
  editor is not your game.

---

## 15. Debugging playbook

Before you spend an hour on a mystery, work down this list:

1. **Did you do the right kind of build?** Live Coding patches function bodies in a running editor.
   It is for function bodies only: treat **any header change** as needing more - especially new or changed `UPROPERTY` /
   `UFUNCTION` / `USTRUCT` / `UENUM`, delegate declarations, new classes, class layout, or
   constructor defaults (the CDO is already built). Those need **a normal build with the editor
   closed**. A `.Build.cs`, `.uproject` or `.uplugin` module change also needs **regenerated project
   files**. The failure is silent - the thing you just wrote behaves as if it does not exist. **If
   something you just wrote appears to do nothing, do an editor-closed build before you debug
   anything else.** Deleting `Intermediate/` and `Binaries/` is a last resort for a corrupted build,
   not a routine step - it is slow and almost never the fix.
2. **Is the property null because you spawned raw C++?** `SpawnActor<T>(T::StaticClass())` bypasses
   the Blueprint CDO entirely.
3. **Is the delegate the right kind?** Non-dynamic delegates are invisible to Blueprint.
4. **Is the widget in an inactive switcher slot?** Then its geometry is zero, permanently.
5. **Did the PlayerController get destroyed?** Any hard `OpenLevel` recreates it.
6. **Is it a soft pointer you gated on `IsValid()`?** Then it never loaded.
7. **Is the GameplayTag on the branch you think it is?** Matching is strict.
8. **Is the data actually authored?** Check the asset, not the code. Then add a validation pass so
   the next person does not have to.

**If it is intermittent, or it crashes with a stack trace that makes no sense:**

9. **Is a lambda capturing a raw `UObject*` or capturing by reference?** Both are use-after-free.
   It must be `TWeakObjectPtr`, resolved and null-checked inside.
10. **Is a background thread touching a `UObject`?** Including resolving a weak pointer. Marshal to
    the Game Thread first.
11. **Is an async or load callback guarding `IsValid(this)`** before it touches any member, and
    checking `GetWorld()` before anything world-dependent?
12. **Does a timer or delegate outlive its owner?** Every `FTimerHandle` cleared and every delegate
    unbound in teardown.

**If it works for you but not for someone else, on a networked project:**

13. **Is the state change guarded by `HasAuthority()`?**
14. **Is `bReplicates` set, and was it set in the constructor?**
15. **Is the property registered in `GetLifetimeReplicatedProps`?** By default in UE 5.7 an
    unregistered property is auto-registered with no condition - it replicates, but to everyone,
    ignoring the condition you meant. With auto-registration off it never replicates. Neither case
    warns unless the project enabled the ensure (11.3).
16. **Is an `OnRep_` handler expected to run on the server?** It does not - call it explicitly there.
17. **Does the client own the actor** it is calling a `Server` RPC on? For a multicast, is the actor
    replicating and net-relevant to that client?
18. **Was the initial value set in `BeginPlay`?** Move it to the constructor or
    `PostInitializeComponents`.

**If it works in the editor but not in a packaged build:**

19. **Is the asset referenced from anything the cooker can see?** An asset only reached by a string
    path or an unreferenced soft path is not cooked. It exists in the editor and is absent in the
    build. Register its type with the Asset Manager (13.3).
20. **Is it `WITH_EDITOR`-only code, or an editor-only module?** It compiles out, and whatever
    depended on it silently does nothing.
21. **Is logic living inside a `check()`?** Its expression is not evaluated in Shipping, so the side
    effect vanishes. `verify` and `ensure` still evaluate theirs (3.9).
22. **Did you test the actual configuration?** Development and Shipping differ in asserts, logging
    and optimisation. "It worked in Development" is not a packaged-build result.

**Always:**

23. **Check the log.** Filter the Output Log by the system's category before you set a breakpoint.
24. **Suspect a missing `UPROPERTY` or a dangling pointer?** Run with `gc.CollectGarbageEveryFrame 1`
    - the bug surfaces on the next frame instead of an hour later.
25. **Slow, or hitching?** Start from `stat unit` (13.2) and the hitch table (13.5), not from the code
    you suspect.

---

## 16. Known engine traps

Each of these is an engine-level behaviour, not a project quirk, and each one **fails silently** -
that is the bar for being in this list. Read the entry before you touch the system it names.

Entries marked ***Real case*** are incidents this team actually shipped and then had to find; the
detail in them is what the bug genuinely looked like from the outside. The rest are engine behaviours
documented here before they cost us anything. Both are worth the same care, but only the first kind
comes with a war story, and none of them are invented.

### Level transitions and the PlayerController

**`OpenLevel` destroys and recreates the PlayerController.** Any subsystem, runner or manager caching
a PC pointer must **re-acquire it on arrival** - typically in `PostLoadMapWithWorld` or from the new
PC's own `BeginPlay` - before any downstream code runs.

**Never gate transition state on a cosmetic fade callback.** A transition phase reset only inside a
loading widget's `OnFadeOutComplete` will never fire: that callback rides the widget's `NativeTick`,
and a hard map load drops the widget from the viewport so it stops ticking. The phase sticks non-Idle
forever, `IsTransitioning()` returns a permanent false positive, and the *next* transition wedges.
**Transition state must be owned by an event guaranteed to run** - reset it unconditionally on
arrival. The fade is cosmetic only.

**A persistent overlay widget is REMOVED from the viewport by a hard `OpenLevel`.** The object itself
survives if it is GameInstance-owned, and `SetRenderOpacity` still applies, but nothing is drawn -
`IsInViewport()` returns false in the new world. Both halves of the fix are required:
**(1)** re-`AddToViewport` on arrival, before the new world's first frame; **(2)** drive any fade from
a **subsystem `TimerManager` timer**, not the widget's own tick or a UMG animation. The subsystem
persists across the load and the new world's timers tick reliably.

**Clear stale widget references before re-creating them.** A cached pointer to a widget from the
outgoing world will pass a null check and then do nothing. Clear it at the top of your
re-initialisation path, before the "create if absent" call.

**A world timer dies on a hard `OpenLevel`.** Anything armed on a world timer that survives a map load
in *concept* - a ringing call, a countdown - must be resolved explicitly on arrival, or it latches its
state for the rest of the session.

### Movement and animation

**`SetActorLocationAndRotation` breaks CharacterMovementComponent.** Direct location writes bypass
the movement component, so `GetVelocity()` stays at zero and every AnimBP blend space downstream
reads idle. Fix: **move through the movement component** - a root motion source
(`FRootMotionSource_MoveToForce` and its siblings) for scripted moves, or `AddMovementInput` /
setting `movementComp->Velocity` each frame. Do not override `GetVelocity()` to fake it: movement,
network prediction and everything else that reads the component still sees zero.

**A Blend Space Player wired to `Ground Speed` outputs an idle pose under scripted movement**, for the
same reason, and the same fix cures it. If a move genuinely cannot go through the component, drive the
blend from an AnimBP variable set to the intended speed.

**A montage needs `Enable Auto Blend Out = ON` or `Montage_SetEndDelegate` never fires.** Any listener
waiting on that delegate parks forever. If you have a paired `DoThing` / `OnDoThingComplete` contract,
make sure **both** paths always broadcast - the no-montage path synchronously, the montage path on end
- and require callers to bind *before* they call.

### Reflection and data

**`DECLARE_MULTICAST_DELEGATE` is invisible to Blueprint's reflection system.** Use the `DYNAMIC` form
plus `UPROPERTY(BlueprintAssignable)`, and match the binding call. See 9.3.

**GameplayTag hierarchy matching is strict.** Tags on separate branches - `Level.Interior.Apartment`
vs `Level.Portal.Interior.Apartment` - will never satisfy `MatchesTag`. Authored data must use the
exact tag the runtime sends.

**`EditInstanceOnly` on a spawned actor can never be authored.** A dynamically spawned actor has no
level instance, so a property that is only editable per-instance has nowhere to receive a value - it
will always be at its constructor default at runtime. Use `EditDefaultsOnly` and assign in Blueprint
Class Defaults.

To be precise about the three specifiers, because they are routinely confused: `EditDefaultsOnly` is
Class Defaults only, `EditInstanceOnly` is placed-instance only, and `EditAnywhere` is both. Only
`EditInstanceOnly` is unusable on a spawned actor. `EditAnywhere` works, but prefer
`EditDefaultsOnly` where per-instance authoring is meaningless - it keeps the Details panel of every
placed instance honest about what is actually tunable.

**`SpawnActor<T>(T::StaticClass())` bypasses the Blueprint CDO.** It instantiates raw C++, so every
Blueprint-assigned property is null. Spawn from a `TSubclassOf<T>` that points at the Blueprint, or
use `TActorIterator` to find placed instances.

**A `UPROPERTY TMap` keyed on a `UENUM` is corrupted by editing that enum.** Keys serialise as their
**byte value**, not their name, so deleting or reordering an enumerator silently re-points every
stored row. **Nothing warns you** - the details panel re-labels whatever bytes it finds, so the map
still reads as a complete, sensible list.

*Real case:* a background-texture map authored against a six-value enum. Removing one enumerator left
one row null and two rows pointing at the wrong asset. The UI rendered solid white in PIE while the
editor showed all five entries assigned.

**Prefer one named `EditDefaultsOnly` field per case** - properties serialise **by name** and survive
any enum edit. Reserve enum-keyed maps for enums that are genuinely frozen, and never for
designer-authored data.

**`TSoftObjectPtr::IsValid()` means "already loaded", not "assigned".** It returns false for an
assigned-but-unloaded soft reference, which is the state every soft reference is in before something
pulls it into memory. So:

```cpp
// DEAD CODE - never loads on first access
if (ptr.IsValid()) { ptr.LoadSynchronous(); }
```

only ever succeeds when some *other* surface loaded the same asset first.

*Real case:* a contact-photo field. Contacts the player had opened elsewhere showed a photo; contacts
they had not showed the authored blank brush. It surfaced first in a search view - the one place that
lists people you have never visited - and read as missing content rather than a missing load.

Use `!IsNull()` to test "is anything assigned", then load it asynchronously (10.3) - or, in
editor tools and behind loading screens only, call `LoadSynchronous` and null-check the result. Reserve `IsValid()` for "is it already resident", e.g. deciding whether an async load is
needed at all.

**A wire enum whose zero value is a real state makes its own fallback unreachable.** `TryGetField` and
friends leave the output **untouched** on a miss - so the enum's default *is* the "field not present"
value, and it must not also be a meaningful one. Reserve enumerator 0 as `Unknown`. Then pair it with
a derivation that never invents an accusatory state.

### Widgets and layout

**A widget in an inactive `UWidgetSwitcher` slot has permanently zero geometry** - not "not yet
valid". The switcher arranges only its active child, so an inactive child is constructed but never
laid out, and `GetCachedGeometry()` reads zero for as long as the slot stays inactive.

**A bounded retry cannot save you** - the retries expire long before the slot goes active.

*Real case:* a scroll box measured zero from `NativeConstruct`; a 10-attempt resolve gave up roughly
1.1 seconds before the player ever opened the panel, so the row-width clamp it computed was never
applied in any session. The only symptom was a give-up warning nobody connected to the visual.

**Fix: move the resolve to the call that makes the widget visible** - and delete the construct-time
attempt rather than keeping it as a fallback, because it can never succeed there. Applies to every
self-measuring widget: check whether a switcher, a `Collapsed` parent, or a retainer sits above you
before trusting cached geometry.

**`SetColorAndOpacity` vs `SetRenderOpacity` when fading.** `SetColorAndOpacity` pushes a tint *down*
into child brushes, so an opaque-material child (a video surface whose material ignores the incoming
Slate colour) will not fade. `SetRenderOpacity` is a composited alpha multiply on the widget's draw
output and fades ordinary children reliably. If a genuinely opaque-material child must fade, put a
plain-colour `UImage` on top and drive its own `ColorAndOpacity`.

**Never resolve layout by walking an engine widget's children.** Engine widget internals are private
layout and change between versions, and a traversal that guesses wrong **fails silently by design**.

*Real case:* a custom text box walked `GetChildren()` expecting `SBorder -> SScrollBox -> FSlot`, and
silently early-returned for the entire life of the feature. Two reasons it could not work:
`SMultiLineEditableTextBox` **is** an `SBorder` (it calls `SBorder::Construct` on itself), so child 0
is already the content and the walk skipped a level; and its subtree contained no `SScrollBox` at all.
The padding it existed to apply never took effect once.

Use the published `SLATE_ATTRIBUTE` / `SLATE_ARGUMENT` on the widget's `FArguments`, or the style
struct. If neither exposes what you need, subclass and override the virtual.

**`SMultiLineEditableText` runs `OnKeyDownHandler` BEFORE its own layout**, so an outer box's
`OnKeyDown` override is dead code. The inner editable text holds keyboard focus and executes the
handler first, only falling through to its own layout when the handler returns Unhandled. **One owner
per input**, and check whether the engine widget already implements the hook before overriding it.

**A `SizeBox` `MaxDesiredHeight` pins a growable text box to one line, and font size is not line
height.** `SBox` computes its desired size as `Min(child, max)`, and then arranges a `VAlign_Fill`
child at the *allotted* height - so the text wraps and grows, but every line past the first exists
only inside the box's own scroll offset.

Compounding it: deriving padding as `(barHeight - fontSize) / 2` is wrong, because **a line is taller
than its font** (a 15pt face measures around 20px). One line then wants more height than the clamp
allows and an internal scrollbar appears permanently.

Derive both numbers from **one measured line height**
(`GetFontMeasureService()->GetMaxCharacterHeight`): padding is `(barHeight - lineHeight) / 2`, and the
ceiling is `barHeight + (maxLines - 1) * lineHeight` - the same derivation with N substituted, so the
two cannot drift. **Never author a layout constant that depends on a metric the details panel cannot
show.**

### Async and threading

**Resolve a `TWeakObjectPtr` on the Game Thread only.** Weak-pointer resolution reads the engine's
object-validity table, which the garbage collector mutates - so `.Get()` and `.IsValid()` off the
Game Thread race against GC. The window is small, which is the problem: it survives every test pass
and fails in a long session. **Marshal to the Game Thread first, then resolve** (10.1). Treat
"is this object still alive" as a question only the Game Thread may ask.

**An async load callback can fire after PIE has stopped.** A load in flight when the user hits stop
delivers its callback into a world that no longer exists. Guard with `IsValid(this)`, and check
`GetWorld()` before touching anything world-dependent - the object can outlive its world.

**A lambda that captures by reference and outlives the frame reads freed stack memory.** `[&]` in an
async or latent callback is a use-after-free with no null pointer to catch it. Copy what you need
into the capture (10.2).

**Streaming sub-levels load asynchronously.** Code that expects a sub-level's actors to be present
immediately after `LoadLevelInstanceBySoftObjectPtr` finds an empty world. Bind to
`FWorldDelegates::LevelAddedToWorld` or the streaming level's own loaded delegate - never poll, and
never wait a fixed delay and hope.

### Networking

**`ReplicatedUsing` does not fire on the machine that set the value.** The server assigns the
property and its `OnRep_` handler does not run there. On a listen server this reads as "the effect
works for everyone except the host". Call the handler explicitly on the authority side when the
response should happen there too (11.3).

**A `Server` RPC on an actor the client does not own is silently dropped.** No warning, no error -
the function simply never executes on the server. Check ownership, not distance, when an RPC appears
to do nothing. **Multicast is the opposite case and is regularly confused with it:** multicast does
not care about ownership at all, only that the actor replicates and is net-relevant to that client.

**Set `bReplicates` in the constructor.** `SetReplicates()` does work at runtime, but only on the
authority, and only if it happens before anything depends on the actor replicating - miss that
window and the actor simply never replicates, with no warning. The constructor is the one place
where the ordering cannot be wrong, so treat runtime toggling as a deliberate exception rather than
a normal option.

**Set authoritative starting values in the constructor or `PostInitializeComponents`, not
`BeginPlay`.** A replicated property assigned in `BeginPlay` can land after the first replication
packet has already gone out, which shows up as a one-frame flicker or, worse, a client that holds the
pre-assignment value for the rest of the session.

**The CDO trap above has a networked failure mode.** Because
`SpawnActor<T>(T::StaticClass())` skips the Blueprint CDO, it also skips any `bReplicates` or
update-frequency override set in Blueprint Class Defaults - so the actor replicates at the wrong
rate, or not at all. Same cause, different symptom, and harder to spot because the actor otherwise
appears to work.

### Collision and input

**Overlap events need `bGenerateOverlapEvents` on both components.** If either side of the pair has
it off, `OnComponentBeginOverlap` never fires - no warning, and the collision responses can look
perfectly correct. Check both components, and that each responds `Overlap` to the other's object
type, before you debug the handler.

**Enhanced Input `Started` and `Completed` are separate trigger events.** A hold action - sprint, aim,
charge - bound only to `Started` begins and never ends; bound to `Triggered` it fires every frame
while held. Bind a start handler to `Started` and a stop handler to `Completed`, and to `Canceled` if
the action has a trigger that can cancel.

**Overlaps fire per component pair, not per actor.** An actor with two overlapping primitives fires
twice. Filter on the component, or de-duplicate by actor.

**`bTraceComplex` traces can miss in a cooked build** when the mesh's complex collision was not
cooked. Test traces in a packaged build.

**`FHitResult::GetActor()` can be null** - a hit on BSP, landscape or a destroyed actor. `IsValid()`
it. Use `ImpactPoint` / `ImpactNormal` for effects and decals; `Location` / `Normal` belong to the
sweep and are for movement.

**Physics is not deterministic across machines.** Keep simulated physics out of anything
gameplay-critical on a networked project, and read physics results in `TG_PostPhysics`, never
`TG_PrePhysics`.

**There are 18 custom collision channels, and they cannot be renumbered.** Budget them on day one:
an object channel is what a thing *is*; a trace channel is a kind of *question*.

### Formatting and media

**`FDateTime::ToString` and `ToFormattedString` are different functions with different token tables.**
`ToString(Format)` handles only `a A D d m y Y h H M S s` - **there is no month-name token.** Month
names (`%b`, `%B`) and weekday names live exclusively on `ToFormattedString`.

Both end their `switch` with `default: AppendChar(*Format)`, so **an unrecognised token is emitted as
its own literal character** with no warning and no fallback.

*Real case:* `"%d %b %Y"` passed through `ToString` rendered **"27 b 2026"** on screen. It looked like
a data bug, not a format bug.

Use `ToFormattedString` for anything a player reads; reserve `ToString` for ISO and machine strings.
**Verify every format string in PIE** - a wrong token is invisible at compile time.

**`UMediaPlayer` requires a `UMediaSoundComponent`** for audio. Attach it dynamically to the owning
`APlayerController` from the widget context, and **register and activate it before `OpenSource()`**.

---

## 17. Pre-commit checklist

**Build and verify**

- [ ] It compiles, and you did an **editor-closed build** (not Live Coding) if you touched
      reflection, a delegate declaration, a constructor default or a new class - plus **regenerated
      project files** for a `.Build.cs` change (15, item 1)
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

A short checklist for project setup, so the standard is in place before the first feature lands.

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
      project is single-player". Retrofitting it later is a rewrite, and a half-answer produces code
      that is authority-aware in some places and not others - 11.1
- [ ] On a replicated project: push model and Iris decided, and the missing-registration CVars set
      in `DefaultEngine.ini` - 11.3, 11.8
- [ ] Git LFS and `.gitattributes` in place before the first asset commit; locking on for `.uasset`
      and `.umap` - 14.3
- [ ] Data-driven asset types registered as Primary Asset Types - 13.3
- [ ] Frame budget per target written down, with line items and owners - 13.2
- [ ] Version control chosen (Git + LFS or Perforce) - 14.3
- [ ] CI tiers in place: every commit, nightly, weekly - 14.5
- [ ] A project `README.md` that fills in every `<Project>` placeholder in this document, lists every
      project override with its section number and reason, and links back to this document

**Enforcement tooling** - so the mechanical rules are checked by a tool, not by memory

- [ ] `tooling/.clang-format` and `tooling/.editorconfig` from this repository copied to the project
      root (3.10)
- [ ] A `.clang-tidy` with `readability-identifier-naming` for the case rules in 4.1, as far as it
      can express them
- [ ] `tooling/Validators/AssetNamingValidator` installed in the project's editor module (steps in
      `tooling/README.md`). It fails any asset under `Content/_<Project>/` without its 7.1 prefix or
      with a non-PascalCase name, on save and in CI (14.5)
- [ ] **Blueprint lint**, as further validators when the project needs them: `Event Tick` without an
      approval comment (3.12), a node-count budget per graph, `Cast To` a Blueprint class (8.3), hard
      references past the reference budget (13.3)
- [ ] A reference-budget commandlet that fails CI when an asset's hard-dependency size passes its
      budget - set budgets just above today's values and ratchet them down
- [ ] The rules no tool can check - header order, comment content, the pillars - listed in the pull
      request template

**Ongoing**

- [ ] A project-level `CLAUDE.md` or equivalent, so assistants follow the same rules as people.
      Point it at the sections that apply - a single-player project skips 11 - rather than the whole
      document.
- [ ] A **canonical examples** list in the README: for each recurring pattern, the real class that
      implements it well - "countdowns: follow the time-bomb timer on the ball actor". Pointing at
      working code beats describing it, and it stands in for the invented class names used here.
- [ ] A living document of project-specific decisions and traps - the section 16 of *that* project.
      Every trap you hit that is not in this document belongs there, and the genuinely engine-general
      ones belong back in **this** document.

---

*This document is the team standard, not one project's convention. If you find a rule here that is
wrong, or a trap that is missing, change it here - so the next project starts from what we learned on
this one.*

---

## Changelog

**1.2 - 2026-09-10**

- Added material from the *Unreal Architect Track* and *Unreal Performance Track* (UE 5.8), checked
  against engine source where it went in as fact: compile-time gating and plugins (1.4, 1.5); the CDO,
  Details-panel design, pointer choice, Core Redirects, the actor lifecycle and tick (3.2-3.12); native
  gameplay tags (4.10); the Blueprint boundary tests (8.1, 8.3); the pattern catalogue, ownership map,
  subsystem design, input, save versioning, GAS and AI (9.10-9.15); gather-compute-apply and the
  animation thread rule (10.4, 10.6); replication, prediction and server rules (11.3-11.9); UI
  architecture (12.6); performance method, memory, hitches, instrumentation, content, server and
  regression gates (13.2-13.9); CI (14.5); collision traps (16); the reviewer's scan (17).
- Replaced "project overrides" with an explicit order for which document wins.
- Added `tooling/`: `.clang-format`, `.editorconfig` and an asset-naming validator.
- Re-checked the replication, push-model and Iris defaults in 5.8: unchanged from 5.7.

**1.1 - 2026-09-10**

- Checked engine claims against UE 5.7 source. Corrected three: `UE_LOGFMT` tokens match by position,
  not name (6.5); reflected struct fields are not zeroed outside engine allocation (4.6); an
  unregistered replicated property is auto-registered by default, and the missing-registration
  ensure is off by default (11.3).
- Resolved contradictions: comment and logging cleanup both apply to new and modified code only
  (5.4, 6.5); header-initialisation exceptions (3.2); one widget bind-name form (7.4); delegate member
  naming (4.7); underscores in function names (11.6); what replaces a switch (9.2).
- Replaced Hot Reload guidance with Live Coding and editor-closed builds (section 15, item 1).
- Added: ranked architecture pillars; the `CONFLICT` block (14.1); object lifetime and GC (3.8);
  assertions (3.9); formatting (3.10); project settings, interfaces, responsibility chains and input
  adapters (9.6-9.9); push model and Iris (11.8); player-facing text (12.5); cooking (13.3); source
  control (14.3); automated tests (14.4); missing asset prefixes (7.1); `GetNameSafe`, enum and
  `UE_CLOGFMT` logging rules (6.1); Tick approval, clamps and units (3.3, 3.7); collision and input
  traps (16); enforcement tooling and canonical examples (18).
- Added the version, placeholder and project-override rules at the top.

**1.0 - 2026-08-27** - First team standard.
