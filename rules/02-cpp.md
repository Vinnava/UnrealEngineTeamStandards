# 3. C++ coding standards

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md). Enforced on every file.

---

### 3.1 Header section order

```cpp
private:   // Variables
protected: // Variables
public:    // Variables

private:   // Functions
protected: // Functions
public:    // Functions
```

- Variables before functions, within each access level.
- **Access level is the only grouping rule.** Never reorder to keep "related" things together. Never
  merge a variables block and a functions block under one specifier.

### 3.2 Never initialise in the header

All defaults live in the constructor - initializer list or body - in the `.cpp`. Every type:
primitives, pointers, bools, enums, structs.

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

Three things are not per-instance defaults, and stay in the header:

- **`static constexpr` constants** - `static constexpr float MaxSpeed = 600.f;` (3.7 wants it next to
  what it governs).
- **Default arguments** - `void Fire(float spread = 0.f);`
- **Explicit enumerator values** - `Unknown = 0` in a `UENUM`.

**The constructor also builds the class default object** - at editor startup, with no world:

- It sets defaults, creates subobjects and configures tick. It never touches the world, other actors
  or assets.
- No `ConstructorHelpers::FObjectFinder` - it is a blocking load at editor startup. Use a soft
  pointer set in Blueprint defaults.
- Blueprint defaults override the C++ values set here.

### 3.3 UPROPERTY categories

Every designer-facing `UPROPERTY` (`EditDefaultsOnly`, `EditAnywhere`, `EditInstanceOnly`) has a
Category in the hierarchy `"Initialize|<System>|<Subsystem>"`.

- **Set once in Blueprint defaults and drives behaviour: `Initialize`.** Debug toggles included, in
  an `Initialize|Debug` branch - never a top-level `Debug`.
- Common branches: `Initialize|Movement`, `Initialize|WidgetClass|<Feature>`, `Initialize|Socket`,
  `Initialize|Config`, `Initialize|Debug`.
- **Only watched at runtime** (`VisibleAnywhere`, `BlueprintReadOnly`): `"Runtime|..."`.
- **Transient pointers cached at `BeginPlay`:** no Category.

```cpp
UPROPERTY(EditDefaultsOnly, Category = "Initialize|Movement")
float maxWalkSpeed;

UPROPERTY(EditDefaultsOnly, Category = "Initialize|WidgetClass|Inventory")
TSubclassOf<UInventoryDesktopWidget> inventoryDesktopWidgetClass;

UPROPERTY(EditDefaultsOnly, Category = "Initialize|Socket")
FName weaponAttachSocketName;

UPROPERTY(EditDefaultsOnly, Category = "Initialize|Debug|Movement")
bool bLogMovementStateChanges;
```

**Every designer-facing number carries its limits and its unit** - `ClampMin` / `ClampMax` (plus
`UIMin` / `UIMax` where the slider should be narrower than the legal range), and `ForceUnits`
wherever the value has a unit:

```cpp
UPROPERTY(EditDefaultsOnly, Category = "Initialize|Movement",
    meta = (ClampMin = "0.0", ClampMax = "2000.0", ForceUnits = "cm/s"))
float maxWalkSpeed;
```

**Design the Details panel.** Gate dependent properties with `EditCondition` (plus
`EditConditionHides` when the property means nothing otherwise), give struct arrays a
`TitleProperty`, and restrict gameplay-tag pickers with `Categories = "Damage.Type"`. A designer must
not be able to author a combination the code does not handle.

### 3.4 Pointers and includes

- **`TObjectPtr<T>` for all `UPROPERTY` object references.** Raw pointers only for locals and
  parameters - never for a member (3.8).
- **Forward declare in headers, include in the `.cpp`.**
- **No implicit includes.** Every file includes exactly what it directly uses, and nothing it does not.
- **`.generated.h` is the last include in its header.** UHT rejects anything after it.
- **Export only what other modules call.** `<Project>_API` on a class or function another module
  links against, not by reflex (1.1).
- **Validate before use. Early return on null**, logged as 6.6 describes.
- **Test `UObject` pointers with `IsValid(ptr)`, not `ptr != nullptr`.** A destroyed-but-uncollected
  actor is still non-null; `IsValid` also rejects objects marked as garbage. Plain null checks are for
  non-`UObject` pointers.

### 3.5 Soft vs hard references

- **Default to `TSoftObjectPtr` / `TSoftClassPtr` for asset references.**
- A hard reference is deliberate: a small, always-needed asset owned by an object that is only loaded
  when the asset is needed anyway.
- Before your first soft-pointer load, read the `IsValid()` trap in section 16.

### 3.6 Function style

Guard clauses first, log the failure, return early. Happy path unindented at the bottom:

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

Log with `UE_LOGFMT` and descriptive `{Tokens}`, values passed directly in token order, no `TEXT()`
wrapper and no `*` dereference (section 6).

### 3.7 General quality bar

- **`const` correctness throughout** - parameters, methods, locals.
- **Event-driven first; Tick needs approval** (pillar 4). Reach for a delegate, an event or a timer
  first. When Tick genuinely is the right tool - continuous per-frame work with no natural event -
  flag it in the plan and get it approved **before** writing it. An approved Tick carries a one-line
  comment saying why, and self-disables the moment it has nothing to do. How to tick: 3.12.
- **Every debug draw sits inside `#if ENABLE_DRAW_DEBUG`** - off in Shipping and Test builds
  (`EngineDefines.h`) - **and behind a runtime bool** under `Initialize|Debug` (3.3).
- **Countdowns run on a timer, not in Tick.** One `FTimerHandle` for the duration, `GetTimerRemaining`
  for display, cleared in teardown (10.5).
- **No magic numbers.** Named `static const` or `constexpr`, declared next to what they govern.
- **No switch statements on identity** (9.2).
- **Prefer composition over deep inheritance chains.**

### 3.8 Object lifetime and garbage collection

- **Every `UObject*` member is a `UPROPERTY` (`TObjectPtr`) or a `TWeakObjectPtr`.** A raw member
  pointer is invisible to GC and dangles.
- **Strong versus weak is an ownership decision.** Cache what you do not own - another system's actor
  or widget - as weak.
- **A non-`UObject` class that holds a `UObject` uses `TStrongObjectPtr`**, or derives from
  `FGCObject` and reports its references in `AddReferencedObjects` when it holds several.
- **Never call `AddToRoot`.** Give the object a real owner instead.
- **Never hold a `UObject` in a `TSharedPtr`.**
- **Data in quantity is a `USTRUCT`, not a `UObject`** (13.4).

**Which pointer:**

| Situation | Type |
|---|---|
| I own it; it loads with me | `UPROPERTY() TObjectPtr<T>` |
| I observe it; someone else owns it | `TWeakObjectPtr<T>` |
| A heavy asset, loaded on demand | `TSoftObjectPtr<T>` |
| A heavy class, loaded on demand | `TSoftClassPtr<T>` |
| A class to spawn, loaded with me | `TSubclassOf<T>` |
| Held by a plain C++ (non-`UObject`) class | `TStrongObjectPtr<T>` |

**Renames are identity changes.** Renaming a C++ class or a `UPROPERTY` needs a Core Redirect
(`[CoreRedirects]` in `DefaultEngine.ini`) in the same commit. Never rename a
`CreateDefaultSubobject` name.

### 3.9 Assertions

| Macro | On failure | In Shipping | Use for |
|---|---|---|---|
| `check(expr)` | Halts | Removed - **`expr` is not evaluated** | Invariants whose failure means continuing would corrupt state |
| `verify(expr)` | Halts | Check removed - **`expr` still evaluated** | The same, when `expr` has a side effect you need |
| `ensure(expr)` | Reports a callstack once, continues | Report removed - **`expr` still evaluated** | Programmer errors the game can survive |

Shipping builds default `DO_CHECK` and `DO_ENSURE` to off (`Build.h`, `AssertionMacros.h`).

- **Never put logic inside `check`.** It is not evaluated in Shipping.
- **`ensureMsgf` is the default assertion.** Prefer a guarded `ensure` to `check` for anything a
  player can survive: `if (!ensure(IsValid(runner))) { return; }`.
- **Keep `check` for true invariants** - `check(IsInGameThread())` (10.1).
- **Expected failures are not assertions.** Bad authored data and network input are logged (6.6,
  6.7), never `ensure`d.

### 3.10 Formatting

- **Opening braces go on their own line** - functions, classes, structs and control flow alike.
- Indentation, spacing and line length come from the repository's `.clang-format`
  (`tooling/.clang-format`: tabs, 120 columns). Run it on the lines you changed.

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

| State | Cost |
|---|---|
| `bCanEverTick = false` | Not registered - zero. **The engine default for `AActor`**; delete the `true` the editor's C++ class template writes unless you need it |
| `bStartWithTickEnabled = false`, or `SetActorTickEnabled(false)` | Registered, dormant |
| `TickInterval = 0.25f` | Dispatched every frame; the body runs periodically |
| `bCanEverTick = true` with an empty or polling body | Full cost for nothing - **the bug** |

- **Prefer, in order:** a delegate, a timer, `SetTimerForNextTick`, tick with an interval, tick.
  Collision and overlap events are delegates, not polls.
- **The door pattern.** Tick on when an episodic behaviour starts, off when it ends - a door ticks
  while *opening*, not while being a door.
- **Stagger intervals and looping timers** with a random first delay.
- **Tick groups:** `TG_PrePhysics` is the default; `TG_DuringPhysics` for work that does not touch
  physics; read physics results in `TG_PostPhysics`; cameras in `TG_PostUpdateWork`. **Order within a
  group is undefined** - declare it with `AddTickPrerequisiteActor` / `AddTickPrerequisiteComponent`,
  or do not rely on it.
- **Many similar things tick as one** - a manager iterating an array, paired with the significance
  manager to spend a fixed budget on the most important N.
- **Blueprint cost is nodes x instances x frames.** Move the loop to C++, keep the decision in
  Blueprint. Deleting the nodes in `Event Tick` may not unregister the tick - verify with `dumpticks`.
