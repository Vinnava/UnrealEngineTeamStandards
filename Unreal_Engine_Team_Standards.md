# Unreal Engine Team Standards

The rules, conventions and best practices every developer on this team follows, on every Unreal
project.

This document is **project-agnostic**. Nothing in it depends on a particular game, module or
feature - it is the standard we carry from one project to the next. Where a project needs to pin
something down (its module name, its content root, its short prefix), those are marked as
`<Project>` placeholders for that project's own README to fill in.

Written against **Unreal Engine 5.x** conventions.

**Sections 1 and 2 tell you where things go. Sections 3 through 8 are the core standard - read them
before you write your first line of code. Sections 9 onward are reference; come back to them.**

---

## Contents

| # | Section | |
|---|---|---|
| 1 | Project and module structure | Layout |
| 2 | Content folder structure | Layout |
| 3 | **C++ coding standards** | Core |
| 4 | **C++ naming conventions** | Core |
| 5 | **Comment standard** | Core |
| 6 | **Logging standard** | Core |
| 7 | **Blueprint and content naming conventions** | Core |
| 8 | **Blueprint discipline** | Core |
| 9 | Architecture rules | Reference |
| 10 | UMG and Slate rules | Reference |
| 11 | Performance and platform | Reference |
| 12 | Working style | Reference |
| 13 | Debugging playbook | Reference |
| 14 | Known engine traps | Reference |
| 15 | Pre-commit checklist | Reference |
| 16 | Adopting this on a new project | Reference |

---

## 1. Project and module structure

### 1.1 Modules

Split runtime code from anything that talks to a backend or an external service:

| Module | Contains |
|---|---|
| `<Project>` | Main game module - gameplay, characters, UI, subsystems |
| `<Project>Online` | HTTP, JSON, auth, backend service classes, wire types |
| `<Project>Editor` | Editor-only tooling, if any |

The split is not ceremony. It keeps `HTTP`/`Json` dependencies out of the gameplay module, makes the
wire contract reviewable in isolation, and means a backend change cannot force a gameplay recompile.

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
- **Any `.Build.cs` change requires a clean rebuild.** Hot Reload does not propagate it - close the
  editor, delete `Binaries/` and `Intermediate/`, regenerate project files, rebuild.

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

Before your first soft-pointer load, read the `IsValid()` trap in section 14 - it is the single most
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
| **Functions and methods** | `PascalCase` | `AdvanceToNextStep`, `ApplyBackground`, `HydrateCallLogs` |
| **Booleans** | **`b` prefix** + PascalCase remainder | `bIsWalking`, `bSearchActive`, `bSuppressAutoLaunch` |
| **Constants** | `constexpr` / `static const`, `PascalCase` | `MaxRecentSearches`, `DefaultDwellSeconds` |
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
| `Get` | Returns a value, **no side effects** | `GetRecentCalls`, `GetActiveNotification` |
| `Set` | Writes a value | `SetChatPanel`, `SetActiveWidgetIndex` |
| `Is` / `Has` / `Can` | Boolean query | `IsTransitioning`, `HasPendingRequest` |
| `Try` | May fail - returns bool, or validates first | `TryLoadOlderMessages`, `TryGetStringField` |
| `Begin` / `Start` | Opens a stateful operation | `BeginCall`, `StartOutgoingRequest` |
| `End` / `Stop` / `Terminate` | Closes it | `EndTour`, `TerminateCall` |
| `Handle` | **The bound callback body** | `HandleNotificationExpired`, `HandleRunnerFinished` |
| `On` | **The event itself**, or a Blueprint-facing hook | `OnPlayerControllerReady`, `OnPostLoadMapWithWorld` |
| `Apply` | Pushes state onto a visual or component | `ApplyBackground`, `ApplyListVisibility` |
| `Init` | One-time setup with arguments | `InitMessenger`, `InitTile` |
| `Ensure` | **Idempotent** - creates only if absent | `EnsureFadeWidget`, `EnsureGameplayHUD` |
| `Refresh` / `Populate` / `Rebuild` | Recomputes a view from source data | `RefreshBadges`, `PopulateConversationList` |
| `Resolve` / `Find` | Looks up and returns, may load | `ResolveAnchor`, `FindTriggerInWorld` |
| `Notify` / `Request` | Crosses a system boundary | `NotifyDestinationReady`, `RequestTransition` |
| `Mark` | Records a state transition into save data | `MarkConversationRead`, `MarkMissedCallsSeen` |
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
| DataAsset | `U<Thing>Asset` / `Catalogue` / `Registry` / `Definition` | `UClothingItemAsset`, `UWallpaperCatalogue`, `UQuestRegistry` |
| Polymorphic family member | `U<Family>_<Verb><Noun>` | `UQuestStep_SpawnNPC`, `UQuestStep_WaitForProximity` |
| SaveGame | `U<Project><Domain>SaveGame` | `UGameEchoSaveGame`, `UGameChatSaveGame` |
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
    section 14.
  - For a **behaviour** enum, make 0 the safe, inert case, so a half-authored data row can never
    accidentally latch active state.
  - For a **player-facing outcome** enum, never let 0 be the accusatory or failure state - a default
    should not blame the player for something they did not do.
- **Never use a `UENUM` as a `UPROPERTY TMap` key.** Section 14 explains why in full: keys serialise
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
- **Dynamic delegate parameter names are PascalCase** - that is a UnrealHeaderTool requirement, not
  our choice. Everywhere else, parameters stay camelCase.
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
NPCMontage.ItemHandover
SpawnMarker.Hub.Intro
Quest.Chapter1.Intro
```

- Establish the **root namespaces** early on a project and keep the list short. A flat sprawl of
  unrelated roots is as bad as no tags.
- **Always fill in `DevComment`.** A tag with an empty comment is a tag nobody else can safely reuse,
  and you will end up with three tags meaning the same thing.
- **Tag matching is strict.** `Level.Interior.Apartment` and `Level.Portal.Interior.Apartment` are
  separate branches and will *never* satisfy `MatchesTag`. Authored data must use the exact tag the
  runtime sends. See section 14.
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
// Applied BEFORE step->Begin so a subtitle step finds the HUD already built to suppress.
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
| `BP_` | Blueprint class | `BP_AvatarCharacter`, `BP_TeaTime` |
| `WBP_` | Widget Blueprint | `WBP_InventoryGrid`, `WBP_MainMenu` |
| `ABP_` | Animation Blueprint | `ABP_PlayerCharacter` |
| `DA_` | Data Asset | `DA_MainOnboarding`, `DA_Hair_1_Female` |
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
| `AS_` | Anim Sequence | `AS_MemoryOrbHandover` |
| `AM_` | Anim Montage | `AM_Player_SitToStand` |
| `BS_` | Blend Space | `BS_Idle_Walk_Run` |
| `AO_` | Aim Offset | `AO_RifleAim` |
| `IA_` | Input Action | `IA_Interact`, `IA_Move` |
| `IMC_` | Input Mapping Context | `IMC_Default`, `IMC_Vehicle` |
| `NS_` | Niagara System | `NS_Sparks` |
| `NE_` | Niagara Emitter | `NE_Embers` |
| `SC_` | Sound Cue | `SC_FootstepStone` |
| `SW_` | Sound Wave | `SW_Ambience_Market` |
| `LS_` | Level Sequence | `LS_OpeningCinematic` |
| `HDRI_` | HDRI backdrop | `HDRI_Overcast` |
| `E_` | Blueprint Enum | `E_ContactTab` |
| `F_` / `S_` | Blueprint Struct | `F_LoadoutData` |
| `BB_` / `BT_` | Blackboard / Behavior Tree | `BB_Guard`, `BT_Guard` |
| `ST_` | State Tree | `ST_GuardPatrol` |

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
See section 10.1.

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

- **Desktop/Mobile split.** Any UI system that touches player interaction gets separate
  `*DesktopWidget` and `*MobileWidget` subclasses from the start. Retrofitting this later is far more
  expensive than doing it up front - the layout, the input model and the hit targets all differ.

- **GameplayTags over enums and strings** for level destinations, identity and spawn points. A tag is
  a content-side addition; an enum is a code change.

- **DataAssets over DataTables** for new game data. Typed `UDataAsset` subclasses give you
  polymorphism, inline authoring (`EditInlineNew` + `Instanced`), and per-asset validation. DataTables
  are for flat, uniform rows - dialogue lines, localisation, tuning tables.

- **Subsystems for services.** Game-wide services are **GameInstance subsystems**. Do not put service
  logic directly in GameMode or GameInstance - both die on map load, and anything caching them dies
  with them.

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
content-only, and it carries the serialisation hazard in section 14 for nothing. Prefer one named
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
- **A new delegate declaration requires a clean rebuild.** Hot Reload does not reliably propagate new
  `DECLARE_DYNAMIC_MULTICAST_DELEGATE` declarations or constructor default changes - the editor keeps
  running with stale reflection data and the delegate simply never fires. Close the editor, delete
  `Binaries/` and `Intermediate/`, regenerate, rebuild.

### 9.4 Ownership

> **Every transition, every state machine, every timer has exactly one owner.**

Two paths that can both advance the same state produce restart loops that are extremely hard to
reproduce. When you add a second caller to something that completes a phase, you are almost certainly
introducing a bug - **find the existing owner instead.**

Corollaries:

- **State must be owned by an event guaranteed to run.** Never by a cosmetic callback, a UMG tick, or
  an animation notify that a map load or a blend-out can interrupt. See section 14.
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

Section 14 covers each of these as a concrete trap.

---

## 10. UMG and Slate rules

### 10.1 BindWidget

`meta = (BindWidget)` matches on **object name**, case-insensitively, and is a **hard compile
requirement** - the Blueprint will not compile if the widget is missing.
`meta = (BindWidgetOptional)` is the soft form.

A widget may move anywhere in the tree as long as its **name survives**. A rename breaks the bind.

### 10.2 Widget structure

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

### 10.3 T3D pastes

When exchanging widget trees as T3D text between developers:

- Apply everything in 10.2 before sending - a paste-ready tree, not a dump.
- **Preserve every `BindWidget` name exactly.**
- **State that the old root must be deleted before pasting.** UMG suffixes duplicates (`Back_Btn_1`)
  and silently breaks every bind.
- **Flag layout bugs you find on the way** rather than quietly fixing them - the other developer
  needs to know.

### 10.4 Slate

If you drop to Slate, two hard rules from section 14 apply:

- **Never resolve layout by walking an engine widget's `GetChildren()`.** Engine internals are private
  layout and change between versions. Use the published `SLATE_ATTRIBUTE` / `SLATE_ARGUMENT`, or the
  style struct, or subclass and override the virtual.
- **Check whether the engine widget already implements the input hook** before you override it. One
  owner per input.

---

## 11. Performance and platform

### 11.1 Platform constraints

| Platform | Constraints |
|---|---|
| **Mobile** (Android/iOS) | Aggressive LOD. Texture streaming. Strict draw-call and material-complexity budgets. **Never multiple high-fidelity characters in the same view.** |
| **Remote / Pixel Streaming** | Minimise per-frame RPC calls. Batch state updates. Latency is the budget, not framerate. |
| **PC** | No artificial constraints, **but must not break the mobile build.** |

**If the project targets mobile, the mobile constraint is the binding one.** "It runs fine on my
4090" is not a result. Everything you build has a Desktop and a Mobile path, and the Mobile path is
the one under pressure.

### 11.2 Habits that pay

- **Avoid Tick.** Where you cannot, self-disable the moment the work is done, and consider a lower
  tick interval.
- **Soft-reference by default** (section 3.5). Async-load on demand.
- **Profile before optimising**, with `stat unit`, `stat game`, Unreal Insights, and the GPU
  visualizer. A guess costs more than a measurement.
- **Check the Size Map** on any Blueprint or widget that references content.
- **Build a packaged mobile build early and often.** Problems that only appear in a cook are the
  expensive kind, and they compound the longer you wait to find them.

---

## 12. Working style

- **Plan before implementing.** Full conflict analysis before code. Identify structural mismatches
  before writing a line.
- **Diagnosis before code.** Root cause identified and agreed before a fix is written. A fix applied
  to a symptom you have not explained will come back.
- **One file at a time.** Write one file, stop, get sign-off, move on.
- **Flag conflicts explicitly.** If new work genuinely conflicts with existing architecture, say so
  before you write around it.
- **Present architectural forks as explicit Option A / Option B with trade-offs** - before the
  decision, not after.
- **Explain the why.** When you introduce a pattern, explain the reasoning: in the PR, in the review,
  in the doc. **A pattern nobody else understands is a liability regardless of whether it is
  correct.**
- **Do not assume a concept is understood because it appears in existing code.** Existing code is
  evidence someone wrote it, not evidence the team understands it.

---

## 13. Debugging playbook

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
9. **Check the log.** Filter the Output Log by the system's category before you set a breakpoint.

---

## 14. Known engine traps

Each of these is an engine-level behaviour, not a project quirk. Each was paid for once. Read the
entry before you touch the system it names.

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

**`EditDefaultsOnly` for anything on a spawned actor.** A dynamically spawned actor has no level
instance, so an `EditInstanceOnly` or `EditAnywhere` property has nowhere to be authored. Use
`EditDefaultsOnly` and assign in Blueprint Class Defaults.

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
height.** `SBox::ComputeDesiredHeight` returns `Min(child, max)`, and `OnArrangeChildren` gives a
`VAlign_Fill` child the *allotted* height - so the text wraps and grows, but every line past the first
exists only inside the box's own scroll offset.

Compounding it: deriving padding as `(barHeight - fontSize) / 2` is wrong, because **a line is taller
than its font** (a 15pt face measures around 20px). One line then wants more height than the clamp
allows and an internal scrollbar appears permanently.

Derive both numbers from **one measured line height**
(`GetFontMeasureService()->GetMaxCharacterHeight`): padding is `(barHeight - lineHeight) / 2`, and the
ceiling is `barHeight + (maxLines - 1) * lineHeight` - the same derivation with N substituted, so the
two cannot drift. **Never author a layout constant that depends on a metric the details panel cannot
show.**

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

## 15. Pre-commit checklist

**Build and verify**

- [ ] It compiles, and you **clean rebuilt** if you touched a delegate declaration, a constructor
      default, a `UPROPERTY`/`UFUNCTION`, a new class, or a `.Build.cs`
- [ ] You **played it in PIE** - not just compiled it
- [ ] No new warnings in the Output Log from your code

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

## 16. Adopting this on a new project

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
- [ ] A project `README.md` that fills in every `<Project>` placeholder in this document and links
      back to it

**Ongoing**

- [ ] A project-level `CLAUDE.md` or equivalent, so assistants follow the same rules as people
- [ ] A living document of project-specific decisions and traps - the section 14 of *that* project.
      Every trap you hit that is not in this document belongs there, and the genuinely engine-general
      ones belong back in **this** document.

---

*This document is the team standard, not one project's convention. If you find a rule here that is
wrong, or a trap that is missing, change it here - so the next project starts from what we learned on
this one.*
