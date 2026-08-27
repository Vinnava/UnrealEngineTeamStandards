# Unreal Engine Team Standards

The rules, conventions and best practices every developer on this team follows, on every Unreal
project.

This document is **project-agnostic**. Nothing in it depends on a particular game, module or
feature - it is the standard we carry from one project to the next. Where a project needs to pin
something down (its module name, its content root, its short prefix), those are marked as
`<Project>` placeholders for that project's own README to fill in.

Written against **Unreal Engine 5.x** conventions.

**Sections 1 and 2 tell you where things go. Sections 3 through 8 are the core standard - read them
before you write your first line of code. Sections 9 through 13 are per-system rules; read the one
you are about to work in. Sections 14 through 18 are practice - the playbook, the traps, and the
checklist you run before every commit.**

Nothing here is aspirational. If a rule in this document is wrong, or you cannot follow it, that is
a defect in the document - fix it (see the closing note) rather than quietly working around it.

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
- **Any `.Build.cs` change requires a clean rebuild** - Hot Reload does not propagate it. Full
  trigger list and procedure: section 15, item 1.

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

**What is not `Initialize`:**

| Kind | Category |
|---|---|
| Runtime state (`VisibleAnywhere`, `BlueprintReadOnly`) | `"Runtime\|..."` |
| Transient pointers cached at `BeginPlay` | No Category needed - they are not designer-facing |

The distinction is authored versus observed. **Anything you set is `Initialize`** - including debug
switches. **Anything you only watch at runtime is `Runtime`.**

### 3.4 Pointers and includes

- **`TObjectPtr<T>` for all `UPROPERTY` object references.** Raw pointers only for non-`UPROPERTY`
  locals and parameters.
- **Forward declare in headers, include in the `.cpp`.**
- **No implicit includes** - every file includes exactly what it directly uses, and nothing it does
  not. Relying on a transitive include is a build break waiting for someone else's refactor.
- **Validate before use. Early return on null.** Every guard-clause return logs (section 6.6).

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

Note the log form: **`UE_LOGFMT` with named `{Tokens}`**, values passed directly with no `TEXT()`
wrapper and no `*` dereference. That is the standard for all new code - see section 6.

### 3.7 General quality bar

- **`const` correctness throughout** - parameters, methods, locals.
- **Avoid Tick.** If you must tick, self-disable the moment the work is done. A component ticking
  for the life of the game to check a bool is a real cost at scale.
- **No magic numbers.** Named `static const` or `constexpr`, declared next to what they govern.
- **No switch statements on identity.** See section 9.2.
- Prefer composition over deep inheritance chains. A five-level actor hierarchy is a refactor you
  will not be able to afford later.

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

Two distinctions that matter:

- **`On` vs `Handle`.** `On*` is the event or virtual hook that fires; `Handle*` is the bound
  callback that does the work. They are not interchangeable, and mixing them makes a delegate graph
  unreadable.
- **`Get` must have no side effects.** If it lazily loads, caches, or hydrates, it is not a `Get` -
  it is a `Resolve` or an `Ensure`.

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
  `U<Proj>SaveGame` is core; a `UInventorySubsystem` is a feature's service. Use it consistently or
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
- **A struct with no meaningful defaults does not need a constructor.** Do not add an empty one for
  symmetry - UHT zero-initialises reflected fields, and an empty constructor is a line of noise
  that implies a decision nobody made.

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
- The **member that holds the delegate** drops the `F` and returns to camelCase:
  `onTransitionReady`.
- Choosing the wrong kind is the most common new-developer bug in Unreal. See section 9.3.

### 4.8 Approved short names

These are the **only** abbreviations accepted. Use them consistently.

| Full name | Short name |
|---|---|
| GameInstance | `gi`, or `<proj>GI` |
| PlayerController | `pc`, or `<proj>PC` |
| CharacterMovementComponent | `movementComp` |
| SkeletalMeshComponent | `skeletalMeshComp` |
| StaticMeshComponent | `staticMeshComp` |
| WidgetComponent | `widgetComp` |
| AnimationInstance | `animInstance` |
| EnhancedInputLocalPlayerSubsystem | `inputSubsystem` |

**The rule behind the table: readable beats short.** A project-prefixed `gameGI` is good; `ggi` is
not. **If a name is not in this table, write it out in full.**

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

### 4.11 Console commands

Any system with non-trivial internal state should register console commands for driving it - launch,
skip, reset, list, abort. They cost an hour to write and save days of clicking through content to
reach the state you need to test.

**Naming: `<proj>.<system>.<verb>`** - lowercase project and system segments, camelCase verb when it
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
- **Every variable and every function in a header** - including private and non-reflected ones
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

### 5.4 Comment maintenance (enforced on every read and edit)

- **When you read or edit a file, if a code element that needs a comment has none, add one.**
- **Any existing comment three lines or longer must be rewritten down to two**, preserving its
  meaning.

This is not optional cleanup - it is part of touching the file. Documentation decays unless every
pass through the code repairs it.

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
UE_LOGFMT(LogGameQuestRunner, Error, "[LaunchQuest] Quest definition is null");

UE_LOGFMT(LogGameQuestRunner, Warning,
    "[LaunchQuest] Section '{Section}' not found in quest '{Quest}' - starting from beginning",
    resumeFromSectionId, quest->GetQuestId());

UE_LOGFMT(LogGameQuestRunner, Log,
    "[LaunchQuest] Quest '{Quest}' starting at section index {Index}",
    quest->GetQuestId(), currentSectionIndex);
```

### 6.5 UE_LOGFMT vs UE_LOG

| | `UE_LOGFMT` | `UE_LOG` |
|---|---|---|
| Arguments | Named `{Tokens}` | Positional `%s`, `%d` |
| FString | Pass directly | Needs `*` dereference |
| Literals | Plain string | Needs `TEXT()` |
| Refactor safety | High - names cannot silently swap | Low - reordering args compiles and lies |

- **`UE_LOGFMT` is the standard for all new code.**
- **Match the file you are working in.** Do not convert an existing file's logging as a side effect
  of an unrelated change - that is diff noise hiding a real edit.

### 6.6 What to log

- **Every early return from a guard clause.** A silent `return` is a bug that costs an hour to find.
- **Every state transition** in a subsystem or runner - entered, completed, aborted.
- **Every DataAsset validation failure**, naming the asset and the row that failed. Authored-data
  errors otherwise surface at runtime as "a thing that never appears", which reads as a missing
  feature rather than bad data.
- **Never log at `Log` level inside Tick or a per-frame loop.** Use `Verbose`.
- **No emojis in log strings.**

### 6.7 Validation passes

Any system driven by authored data should have a `Validate*` function that runs **once on load** and
logs an `Error` for every unresolvable reference, duplicate id, or miscategorised row.

This is the highest-value logging you will write. Bad authored data fails silently by default; a
validation pass converts a mystery into a line in the log.

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

If you find yourself writing gameplay flow in C++, or system architecture in Blueprint, stop.

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
- **Avoid `Get All Actors Of Class`** in anything that runs more than once at startup.
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
  are for flat, uniform rows - dialogue lines, localisation, tuning tables.

- **Subsystems for services.** Game-wide services are **GameInstance subsystems**. Do not put service
  logic directly in GameMode or GameInstance - GameMode is destroyed on map load, and anything caching
  it dies with it. On a replicated project, note that **a subsystem has no network authority of its
  own** - see 11.2 before you put authoritative state in one.

- **One owner per piece of state.** See 9.4.

### 9.2 Scalability rules

These exist because content always grows faster than code:

- **No switch statements on identity.** Use a handler map. A `switch` on slot, item type or state
  means every new case is a code change in a file that has nothing to do with the new content.
- **No progression state in domain enums.** An enum describes what a thing *is*, never how far the
  player has got.
- **No implicit contracts in comments.** If two things must agree, enforce it in the data - a
  validation pass that logs an Error (section 6.7).
- **No single-point assumptions.** `TArray<FAttachmentPoint>` always, even when today's design only
  needs one. The second one always arrives.
- **Every new slot, item type or unlock should be a content or config change - zero code change.** If
  adding the *second* one of something requires touching C++, the first one was built wrong.

**A counter-example worth internalising:** the scalability argument for an enum-keyed `TMap` is
usually false. If the key is a C++ enum, adding a case is already a code change - so the map was never
content-only, and it carries the serialisation hazard in section 16 for nothing. Prefer one named
`EditDefaultsOnly` field per case.

### 9.3 Delegates - choosing the right kind

| | Non-dynamic | Dynamic |
|---|---|---|
| Declaration | `DECLARE_MULTICAST_DELEGATE*` | `DECLARE_DYNAMIC_MULTICAST_DELEGATE*` |
| Blueprint-visible | **No** | Yes, with `UPROPERTY(BlueprintAssignable)` |
| Bind | `AddUObject`, `AddLambda` | `AddDynamic` |
| Unbind | `RemoveAll(this)` | `RemoveDynamic` |
| Performance | Faster | Slower (reflection) |

- **Default to non-dynamic** unless Blueprint genuinely needs to bind.
- **Binding must match the declaration.** Mixing them does not compile, which is the one merciful
  part of this.
- **Always unbind in the matching teardown** - `EndPlay`, `Deinitialize`, `NativeDestruct`. A dangling
  bind on a destroyed object is a crash you will reproduce once a week.
- **A new delegate declaration requires a clean rebuild** - Hot Reload leaves stale reflection data
  and the delegate simply never fires. Full trigger list and procedure: section 15, item 1.

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

### 9.5 Persistence across level transitions

Anything that must outlive a map load lives on the **GameInstance** or a GameInstance subsystem.
Everything else is destroyed and recreated - including the PlayerController, the HUD, every widget,
and every world timer.

Design the handoff explicitly:

- Re-acquire the PlayerController on arrival, do not cache it across the load.
- Re-add persistent widgets to the viewport; they are dropped even though the object survives.
- Drive anything time-based from a **subsystem** timer, not a widget tick.

Section 16 covers each of these as a concrete trap.

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
        FStreamableDelegate::CreateUObject(this, &UInventorySubsystem::OnIconLoaded));
}

void UInventorySubsystem::OnIconLoaded()
{
    UTexture2D* loaded = iconAsset.Get();
    if (!IsValid(loaded))
    {
        UE_LOGFMT(LogGameInventory, Warning,
            "[{Obj}] [OnIconLoaded] Icon was collected before the callback fired: {Path}",
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
- **Store the `TSharedPtr<FStreamableHandle>`** if you need to cancel or to keep the load alive.
  Dropping the handle releases your reference; if you were the only holder, the load is cancelled.
- **Never assume a load is fast.** Profile before you decide a synchronous load is acceptable.

### 10.4 Background work

**Prefer `Async` / `AsyncTask` and the TaskGraph over `FRunnable`.** Reach for `FRunnable` only when
you genuinely need a persistent thread with its own lifecycle - a long-lived I/O pump, an audio
capture loop - not for a one-off computation.

The pattern in 10.1 covers almost every case: do the work on a background thread, marshal the result
back to the Game Thread, resolve a weak pointer there. Prefer it to a `TFuture` continuation chain,
because `.Then()` runs on an unspecified thread and you end up hand-writing the same marshalling step
with an extra layer of indirection around it.

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

- **Register every replicated property in `GetLifetimeReplicatedProps`.** A `Replicated` `UPROPERTY`
  that is not registered simply never replicates, and it is easy to ship that way - the property
  exists, the code compiles, and the client silently holds its constructor default forever.
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

### 11.6 Naming

Extending the verb vocabulary in section 4.3 - an RPC prefix states **where the function runs**, and
is mandatory because nothing else at the call site tells you:

| Kind | Prefix | Example |
|---|---|---|
| `Server` RPC | `Server` | `ServerRequestInteract` |
| `Client` RPC | `Client` | `ClientNotifyPurchaseFailed` |
| `NetMulticast` RPC | `Multicast` | `MulticastPlayHitEffect` |
| RepNotify handler | `OnRep_` | `OnRep_ActiveQuestTag` |

**`OnRep_` is the one underscore we accept in a function name**, because the engine requires that
exact form. RPC prefixes stay PascalCase and unbroken - `ServerRequestInteract`, not
`Server_RequestInteract` - consistent with the verb-first rule in 4.3. Pick one form and hold it;
a codebase with both is one where nobody can grep for either.

### 11.7 Testing

- **Test in PIE with at least two clients**, and **with Run Under One Process disabled** at least once
  per feature. Single-process PIE shares statics and hides a whole category of bug.
- **Test as a dedicated server, not only as a listen server.** A listen server is both authority and
  client, so it silently masks missing `OnRep_` calls and missing authority checks.
- **Test with simulated latency and packet loss** (`Net PktLag`, `Net PktLoss`). Prediction bugs are
  invisible at 0ms.
- **Watch the bandwidth.** `stat net` and the Network Profiler will show you a 100 Hz actor long
  before a player reports it.

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
- **Name by role, never by engine default.** `HeaderTitle_Text`, not `TextBlock_45`. Set both `Name`
  and `DisplayLabel` to the same string.
- **One widget, one job.** A widget that both fetches and displays is two widgets.

### 12.3 T3D pastes

When exchanging widget trees as T3D text between developers:

- Apply everything in 12.2 before sending - a paste-ready tree, not a dump.
- **Preserve every `BindWidget` name exactly.**
- **State that the old root must be deleted before pasting.** UMG suffixes duplicates (`Back_Btn_1`)
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

### 13.2 Habits that pay

- **Avoid Tick** (3.7). Where you cannot, also consider a longer tick interval rather than every
  frame.
- **Profile before optimising**, with `stat unit`, `stat game`, Unreal Insights, and the GPU
  visualizer. A guess costs more than a measurement.
- **Check the Size Map** on any Blueprint or widget that references content.
- **Build a packaged build for the lowest target platform early and often.** Problems that only
  appear in a cook are the expensive kind, and they compound the longer you wait to find them. See
  section 15 for the editor-versus-packaged symptom list.

---

## 14. Working style

### 14.1 How we work

- **Plan before implementing.** Full conflict analysis before code. Identify structural mismatches
  before writing a line.
- **Diagnosis before code.** Root cause identified and agreed before a fix is written. A fix applied
  to a symptom you have not explained will come back.
- **Flag conflicts explicitly.** If new work genuinely conflicts with existing architecture, say so
  before you write around it.
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

---

## 15. Debugging playbook

Before you spend an hour on a mystery, work down this list:

1. **Did you clean rebuild?** Hot Reload does not reliably propagate new delegate declarations,
   constructor default changes, new `UPROPERTY`/`UFUNCTION`, new classes, or `.Build.cs` edits. The
   failure is silent - stale reflection data, so the thing you just wrote behaves as if it does not
   exist. **If something you just wrote appears to do nothing, rebuild before you debug anything
   else.**
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
15. **Is the property registered in `GetLifetimeReplicatedProps`?** An unregistered `Replicated`
    property never replicates and never warns.
16. **Is an `OnRep_` handler expected to run on the server?** It does not - call it explicitly there.
17. **Does the client own the actor** it is calling a `Server` RPC on? For a multicast, is the actor
    replicating and net-relevant to that client?
18. **Was the initial value set in `BeginPlay`?** Move it to the constructor or
    `PostInitializeComponents`.

**If it works in the editor but not in a packaged build:**

19. **Is the asset referenced from anything the cooker can see?** An asset only reached by a string
    path or an unreferenced soft path is not cooked. It exists in the editor and is absent in the
    build.
20. **Is it `WITH_EDITOR`-only code, or an editor-only module?** It compiles out, and whatever
    depended on it silently does nothing.
21. **Is it a `check()` or `ensure()` you are relying on?** `check` is compiled out in Shipping.
    Logic must never live inside one.
22. **Did you test the actual configuration?** Development and Shipping differ in asserts, logging
    and optimisation. "It worked in Development" is not a packaged-build result.

**Always:**

23. **Check the log.** Filter the Output Log by the system's category before you set a breakpoint.

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

**`SetActorLocationAndRotation` breaks CharacterMovementComponent.** Direct location writes leave
`GetVelocity()` returning zero, which breaks every AnimBP blend space downstream. Fix: override
`GetVelocity()` to return your scripted velocity while scripted movement is active.

**A Blend Space Player wired to `Ground Speed` outputs an idle pose under scripted movement**, for the
same reason. Wire it to a variable you set to the intended speed while scripted movement is active.

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

Use `!IsNull()` to test "is anything assigned", or just call `LoadSynchronous` and null-check the
result. Reserve `IsValid()` for "is it already resident", e.g. deciding whether an async load is
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

- [ ] It compiles, and you **clean rebuilt** if you touched a delegate declaration, a constructor
      default, a `UPROPERTY`/`UFUNCTION`, a new class, or a `.Build.cs`
- [ ] You **played it in PIE** - not just compiled it
- [ ] No new warnings in the Output Log from your code
- [ ] If an assistant wrote any of it, **you have read every line** and it meets every rule below
      (14.2)

**C++ structure**

- [ ] Header sections in the mandatory order, variables before functions
- [ ] No inline initialisation in any `.h` - defaults are in the constructor, structs included
- [ ] `TObjectPtr` on every `UPROPERTY` object reference
- [ ] Forward declares in headers, includes in the `.cpp`, nothing implicit
- [ ] Soft references by default; every hard reference is deliberate
- [ ] `const` correct; no new Tick without a self-disable; no magic numbers

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

**Architecture**

- [ ] The new state has exactly one owner - you did not add a second path that completes it (9.4)
- [ ] No `switch` on slot, item type or identity - handler map instead (9.2)
- [ ] Adding the *second* one of this thing is a content change, not a code change (9.2)
- [ ] Service logic is in a GameInstance subsystem, not in GameMode (9.1)
- [ ] Anything that must survive a map load lives on the GameInstance side (9.5)

**Comments**

- [ ] Every new `UPROPERTY` / `UFUNCTION` / enumerator has a Doxygen comment
- [ ] **Every comment is two lines or fewer**
- [ ] Any 3+ line comment you touched has been rewritten down to two
- [ ] Comments explain *why*, not *what*
- [ ] No emojis. No `U+FFFD`. No commented-out code. No anonymous `TODO`.

**Logging**

- [ ] Category declared with `DEFINE_LOG_CATEGORY_STATIC` in the `.cpp`, named `Log<Proj><Domain>`
- [ ] `UE_LOGFMT` with named tokens, not `UE_LOG`, in new code
- [ ] Every line has class, function, description and a context value
- [ ] Every guard-clause early return logs
- [ ] Correct severity; nothing at `Log` level inside a per-frame path

**Async and threading**

- [ ] No `UObject` accessed, created or destroyed off the Game Thread - weak-pointer resolution
      included
- [ ] Every lambda that outlives the frame captures `TWeakObjectPtr`, never a raw `UObject*` and
      never by reference
- [ ] Every async and load callback resolves the weak pointer once, null-checks it, and checks
      `GetWorld()` before touching anything world-dependent
- [ ] Every `FTimerHandle` stored and cleared in teardown; every delegate unbound
- [ ] Any new `FRunnable` is stopped and joined from its owner's teardown

**Networking** (if the project replicates)

- [ ] Every replicated state change guarded by `HasAuthority()`
- [ ] `bReplicates` set in the constructor, not later
- [ ] Every `UPROPERTY(Replicated*)` registered in `GetLifetimeReplicatedProps`
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

**Content**

- [ ] New assets carry the correct type prefix and PascalCase name (7.1-7.3)
- [ ] No vendor, tool, scratch or history names (`_Final`, `_v2`, `_test`)
- [ ] Any prototype or test Blueprint is named `BP_TEMP_` / kept in `TEMP/`, and nothing shipping
      references it
- [ ] Blueprint variables have tooltips and categories; graphs have comment boxes
- [ ] No new hard references to heavy assets in a widely-instanced Blueprint

**Docs**

- [ ] Docs updated in the same commit if you changed a documented system

---

## 18. Adopting this on a new project

A short checklist for project setup, so the standard is in place before the first feature lands.

**Pin these before the first feature**

- [ ] Module split decided (`<Project>` / `<Project>Online`) - 1.1
- [ ] Source folder skeleton in place - 1.3
- [ ] Content root `Content/_<Project>/` created, folder skeleton in place - 2.1
- [ ] Project short name pinned, for class infixes and short variable names - 4.4, 4.8
- [ ] Log category naming pinned: `Log<Proj><Domain>`, declared with `DEFINE_LOG_CATEGORY_STATIC` - 6.2
- [ ] GameplayTag root namespaces agreed - 4.10
- [ ] Console command namespace pinned: `<proj>.<system>.<verb>` - 4.11
- [ ] A `TEMP/` or `Developers/` content folder created, so prototypes have somewhere legitimate to
      live - 8.2
- [ ] **Replication decided and written down in the README** - "this project replicates" or "this
      project is single-player". Retrofitting it later is a rewrite, and a half-answer produces code
      that is authority-aware in some places and not others - 11.1
- [ ] A project `README.md` that fills in every `<Project>` placeholder in this document and links
      back to it

**Ongoing**

- [ ] A project-level `CLAUDE.md` or equivalent, so assistants follow the same rules as people
- [ ] A living document of project-specific decisions and traps - the section 16 of *that* project.
      Every trap you hit that is not in this document belongs there, and the genuinely engine-general
      ones belong back in **this** document.

---

*This document is the team standard, not one project's convention. If you find a rule here that is
wrong, or a trap that is missing, change it here - so the next project starts from what we learned on
this one.*
