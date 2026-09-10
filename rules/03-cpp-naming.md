# 4. C++ naming conventions

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

---

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

> **One deliberate deviation from Epic: Epic uses PascalCase for member variables; we use
> camelCase.** Follow ours, not the engine's. Everything else follows Epic.

### 4.2 Booleans

- **The `b` prefix is mandatory everywhere a boolean appears** - member, local, parameter, and
  Blueprint variable.

```cpp
bool bIsWalking;                        // member
bool bSuppressAutoLaunchOnNextLoad;     // member, a latch
bool bFreshOpen;                        // parameter
const bool bHadPendingOpen = ...;       // local
```

- **Accessors that return a bool do not carry the `b`.** They are PascalCase functions starting with
  `Is` / `Has` / `Can`:

```cpp
bool IsTransitioning() const;
bool HasCompletedOnboarding() const;
bool CanAffordPurchase(int32 cost) const;
```

- **Name a boolean for the true state, never the negative.** `bIsVisible`, not `bIsNotHidden`.

### 4.3 Function verb vocabulary

Function names are `PascalCase` and **start with a verb from this vocabulary** - never an invented
synonym.

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

- **`On` vs `Handle`.** `On*` is the event or virtual hook that fires; `Handle*` is the bound callback
  that does the work. Never interchange them.
- **`Get` has no side effects.** If it lazily loads, caches or hydrates, it is a `Resolve` or an
  `Ensure`.
- **`Do*` holds no logic.** It lives only on the player-facing class and forwards to a component (9.9).

### 4.4 Class name composition

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

- **A project short-name infix marks a class as project-core** (`U<Project>SaveGame`), not
  feature-local (`UInventorySubsystem`). Use it consistently or not at all.
- **An underscore in a class name is reserved for a polymorphic family** (`UQuestStep_*`).

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

- **`E` prefix, PascalCase name, always `enum class`, always `: uint8`.**
- **Enumerators are PascalCase with no prefix and no redundant type name** - `Answered`, not
  `ECallOutcome_Answered` or `ECO_Answered`.
- **Every enumerator gets a Doxygen comment** (section 5).
- **Enumerator 0:**
  - **Wire or parsed enum** - 0 is `Unknown`, so "field absent" stays representable (section 16).
  - **Behaviour enum** - 0 is the safe, inert case.
  - **Player-facing outcome enum** - 0 is never the accusatory or failure state.
- **Never use a `UENUM` as a `UPROPERTY TMap` key** (section 16).

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
- **Struct fields are `camelCase`**, like class members.
- A DataTable row struct inherits `FTableRowBase` and is named `F<Domain>Data` or `F<Domain>Row`.
- Pure data only. A struct with behaviour usually wants to be a `UObject` or a DataAsset.

**Struct defaults follow 3.2:** declare a default constructor and assign in its body, never with
inline member initialisers.

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

- **A types-only header with no `.cpp`** may define the constructor inline in the header - still
  inside the constructor body, never as member initialisers.
- **Any struct with a number, bool, enum or raw pointer field needs a constructor that sets it.**
  Reflected fields are zeroed only when the engine allocates the struct; a local `FAppEntry entry;`
  holds garbage, and the engine's uninitialised-struct check (`Class.cpp`) flags the type. A struct
  whose fields all have their own constructors (`FName`, `FString`, `TArray`, `FGameplayTag`,
  `TObjectPtr`) may omit it.

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
- **Dynamic delegate parameter names are PascalCase** - they become Blueprint pin labels. The one
  place a parameter is not camelCase.
- **The member that holds the delegate is camelCase** (4.1): `onTransitionReady`. PascalCase `On*`
  (4.3) names functions and virtual hooks, not members.
- **More than two parameters? Pass one context struct** - `FOnHitReceived` carrying a
  `const FHitContext&`. New fields go into the struct; no listener or signature changes. For a dynamic
  delegate the struct is a `USTRUCT(BlueprintType)`.
- Choosing the right kind: 9.3.

### 4.8 Approved short names

These are the **only** abbreviations accepted:

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

**Readable beats short.** `gameGI` is good; `gi` and `ggi` are not. **If a name is not in this table,
write it out in full.**

### 4.9 File naming

- **One class per file pair.**
- **File name is the class name without the type prefix.** `UQuestDirectorSubsystem` lives in
  `QuestDirectorSubsystem.h` / `.cpp`.
- Folder path mirrors the class's role (1.3).
- **Shared type-only headers are named for their contents** - `AnchorTypes.h`, `DialogueTypes.h`,
  `ChatTypes.h`, `TimeUtils.h`. Structs and enums only, no behaviour.

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

- Establish the **root namespaces** early on a project and keep the list short.
- **Always fill in `DevComment`.**
- **Tag matching is strict.** `Level.Interior.Apartment` and `Level.Portal.Interior.Apartment` are
  separate branches and never satisfy `MatchesTag`. Authored data uses the exact tag the runtime
  sends (section 16).
- **Prefer tags over strings and enums** for level destinations, spawn points and identity.
- **Tags used in C++ are declared natively** - `UE_DECLARE_GAMEPLAY_TAG_EXTERN` in a header,
  `UE_DEFINE_GAMEPLAY_TAG` in the `.cpp` (the macro refuses to compile in a header). Never
  `RequestGameplayTag("Literal")` in gameplay code.
- **`MatchesTag` is hierarchical** (`Damage.Type.Fire` matches `Damage.Type`); `MatchesTagExact` is
  not. Choose deliberately.

### 4.11 Console commands

- **Any system with non-trivial internal state registers console commands** for driving it - launch,
  skip, reset, list, abort.
- **Naming: `<Project>.<system>.<verb>`** - lowercase project and system segments, camelCase verb
  when it is more than one word.

```
game.quest.launch
game.quest.skipSection
game.quest.clearProgress
game.quest.listSections
game.quest.abort
```

- Register them in the owning subsystem's `Initialize`, and **release the handles in
  `Deinitialize`** - a leaked `IConsoleCommand` fires into a dead object.
