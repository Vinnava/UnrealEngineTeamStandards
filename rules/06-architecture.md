# 9. Architecture rules

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

---

### 9.1 The five key conventions

- **Desktop/Mobile split - if the project ships on both.** Any UI system that touches player
  interaction gets separate `*DesktopWidget` and `*MobileWidget` subclasses **from the start**. A
  single-platform project does not build the second path speculatively.
- **GameplayTags over enums and strings** for level destinations, identity and spawn points.
- **DataAssets over DataTables** for new game data - typed `UDataAsset` subclasses, with inline
  authoring (`EditInlineNew` + `Instanced`) and per-asset validation. Choose the container by shape:

  | Shape | Container |
  |---|---|
  | Many flat, uniform rows (dialogue lines, localisation, tuning tables) | `UDataTable` - one binary file, one editor at a time |
  | One entity | `UPrimaryDataAsset` |
  | A value over a curve | A curve asset or `UCurveTable` |
  | Project-wide or per-platform | `UDeveloperSettings` (text `.ini`, mergeable) |
  | A shared vocabulary | `FGameplayTag` |

- **Subsystems for services.** Services that must outlive a map are **GameInstance subsystems**;
  services scoped to one level - spawning, level-local registries - are **World subsystems**. No
  service logic directly in GameMode or GameInstance. **GameMode owns the match rules** - win and
  lose conditions, player spawning, round flow. On a replicated project, **a subsystem has no network
  authority of its own** (11.2).
- **One owner per piece of state** (9.4).

### 9.2 Scalability rules

- **No switch statements on identity** (slot, item type, state). Use one of:
  - **A map keyed by `FGameplayTag`**, authored in a DataAsset -
    `TMap<FGameplayTag, TObjectPtr<UItemBehaviourAsset>>`. A new case is a new tag and a new row.
  - **Strategy via polymorphic DataAssets** - the data carries an `Instanced` behaviour object (the
    `UQuestStep_*` family in 4.4) and the caller invokes its virtual.
- **No enum-keyed `TMap` for content that grows.** An enum key is already a code change and carries
  the serialisation hazard in section 16. For a set of cases genuinely fixed in code, use one named
  `EditDefaultsOnly` field per case.
- **No progression state in domain enums.** An enum describes what a thing *is*, never how far the
  player has got.
- **No implicit contracts in comments.** If two things must agree, enforce it with a validation pass
  that logs an Error (6.7).
- **No single-point assumptions.** `TArray<FAttachmentPoint>`, even when today's design needs one.
- **Every new slot, item type or unlock is a content or config change - zero code change.** If adding
  the *second* one of something touches C++, the first was built wrong.

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
  `[this]` capture (10.2). A template deduction error from `AddUObject` almost always means the
  handler's signature does not match the delegate's.
- **Binding matches the declaration.**
- **Always unbind in the matching teardown** - `EndPlay`, `Deinitialize`, `NativeDestruct`.
- **A new delegate declaration needs a full build with the editor closed** (section 15, item 1).

### 9.4 Ownership

> **Every transition, every state machine, every timer has exactly one owner.**

- **Adding a second caller to something that completes a phase is almost always a bug** - find the
  existing owner instead.
- **State is owned by an event guaranteed to run** - never a cosmetic callback, a UMG tick, or an
  animation notify that a map load or blend-out can interrupt (section 16).
- **A completion signal fires exactly once**, from the code that owns the operation.
- **An invariant re-established rather than enforced logs a Warning** (6.3).
- **Capture before you transition.** Copy what a transition will clear into a local *before* calling
  it:

  ```cpp
  AActor* const instigator = lastInstigator;   // Idle clears lastInstigator
  TransitionToState(EPickupState::Idle);
  NotifyPickupReleased(instigator);
  ```

### 9.5 Persistence across level transitions

Anything that must outlive a map load lives on the **GameInstance** or a GameInstance subsystem.
Everything else is destroyed and recreated - the PlayerController, the HUD, every widget, every world
timer.

- Re-acquire the PlayerController on arrival; do not cache it across the load.
- Re-add persistent widgets to the viewport; they are dropped even though the object survives.
- Drive anything time-based from a **subsystem** timer, not a widget tick.
- **What survives travel:** the GameInstance and its subsystems, and each LocalPlayer and its
  subsystems, always. Seamless travel also keeps the PlayerController and PlayerState - the
  PlayerState carries across only what `CopyProperties` copies. The world, its subsystems, the
  GameMode, the GameState and every other actor are always destroyed.
- **Under World Partition, any actor can unload at any time** (`EndPlay` with `RemovedFromWorld`).
  Never hold a hard reference to a level actor from anything that outlives it; keep durable state in
  a World subsystem or higher, never on a placed actor.

Section 16 covers each of these as a concrete trap.

### 9.6 Project settings

- **Project-wide tunables live in a `UDeveloperSettings` subclass** -
  `UCLASS(Config = Game, DefaultConfig)`, saved to `DefaultGame.ini`. Read it with
  `GetDefault<U<Project>QuestSettings>()`, and add the `DeveloperSettings` module dependency.
- Not a hard-coded constant, not a property on the GameMode Blueprint, not a hand-parsed ini section.
- Per-level and per-asset values stay in DataAssets.
- **Console variables are namespaced** `<Project>.<system>.<name>`, lowercased (4.11), with every value
  documented in the help text. Anything that grants an advantage is `ECVF_Cheat`.
- **Per-platform differences live in per-platform config**, not `if (platform)` branches in C++.
- **`Saved/Config` is local and beats every other config layer** - suspect it first when a setting
  works on one machine only.

### 9.7 Interfaces

- **Test with `obj->Implements<UInteractInterface>()`** - it sees C++ and Blueprint implementations.
  `Cast<IInteractInterface>(obj)` returns null for a Blueprint implementation.
- **Call Blueprint-facing interface functions through `IInteractInterface::Execute_Interact(obj, ...)`**,
  never directly on a cast pointer.
- **Hold an interface reference as `TScriptInterface<IInteractInterface>`** in a `UPROPERTY` (3.8).
- A C++-only interface (`meta = (CannotImplementInterfaceInBlueprint)`) may be called through `Cast<>`.

### 9.8 Layered responsibility chains

When one event crosses several classes - a hit, an interaction, a pickup - split it into layers:

1. **Detect** - the sensor (projectile, trigger, trace) notices contact and broadcasts it with a
   context struct (4.7). It never decides the outcome.
2. **Resolve** - the target decides what the contact means *for it*, using only its own components,
   and returns a result enum.
3. **Act** - the authority, usually the GameMode (9.1), applies the consequence.

New modifiers - power-ups, status effects - slot into the resolve step without touching the sensor,
the authority or any delegate signature.

### 9.9 Input adapters and shared abilities

- **Abilities live in components on the shared base class** (`A<Project>CharacterBase`), so the player
  and the AI have the same capabilities.
- **The player class only adapts input.** Its `Do*` handlers (4.3) forward to those components and
  hold no logic. The AI drives the same components from behaviour-tree or State Tree tasks.
- A behaviour that exists only in a `Do*` handler moves into the component.

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

Choosing between the decoupling patterns:

- **Delegate** when the listener may know the source.
- **Interface** (9.7) when you call *into* objects of varying type.
- **Message bus** when neither side may know the other. `UGameplayMessageSubsystem` ships with Epic's
  Lyra sample, not the engine - copy it or write the equivalent. It is local only and carries
  notifications, never requests.

**Do not force a pattern.** One not in this table needs a `CONFLICT` block (14.1) naming the problem it
solves. Pool only what is numerous and short-lived.

### 9.11 Where state lives

Place every piece of state by **who owns it** and **how long it lives**. If the answers disagree, it
is two pieces of state - split it.

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
  clients; what the client needs belongs on the GameState.
- **Never `GetPlayerController(World, 0)` in gameplay code** - wrong player on a dedicated server and
  in split-screen. Walk up the chain: component, owner, controller, PlayerState.
- **Cross-machine time** is `GameState->GetServerWorldTimeSeconds()`, never
  `GetWorld()->GetTimeSeconds()`.
- **Smells:** "a manager actor" - a World subsystem. "A singleton" - a subsystem. "It resets on
  respawn" - it belongs on the PlayerState.

### 9.12 Subsystem design

| Type | Lifetime | For |
|---|---|---|
| `UEngineSubsystem` | Process | Engine-level services; rare in game code |
| `UGameInstanceSubsystem` | Survives level loads | Save, session, settings, cross-level services |
| `UWorldSubsystem` | One world | Managers, spawners, level-scoped registries |
| `ULocalPlayerSubsystem` | One local human | Input, UI layers, local preferences |

Every subsystem:

- **Filters where it exists in `ShouldCreateSubsystem`** - a World subsystem checks the world type, or
  it spawns into editor previews and thumbnail worlds.
- **Declares initialisation order with `Collection.InitializeDependency<T>()`.**
- **Mirrors `Initialize` exactly in `Deinitialize`** - every bind, timer and console command released
  (4.11).
- **Guards `IsTickable`** if it ticks.

**A subsystem is a service, not a bag.** If you cannot state its job in one sentence, split it.

### 9.13 Input

- **An input action names the intent, never the key** - `IA_Interact`, not `IA_PressE`.
- **Continuous input binds to `Triggered`.** Movement bound to `Started` moves for one frame. Hold
  actions pair `Started` with `Completed` (section 16).
- **Bind on the pawn what should die with the body** (move, fire, abilities); **on the
  PlayerController what survives death** (pause, scoreboard, spectate).
- **Mapping contexts:** add one on top at a higher priority for an overlay (menu, aim); remove and
  replace for a mode change (vehicle).
- **Never `if (bIsGamepad)`** in gameplay code. Device differences are mapping-context and platform
  data.
- **Input sets intent; the movement component decides.** Never call `SetMovementMode` from an input
  handler.
- **Movement tuning is data** - `MaxWalkSpeed`, `JumpZVelocity`, `AirControl` in a DataAsset or
  settings.

### 9.14 Save data and versioning

- **Mark saved fields `UPROPERTY(SaveGame)`** and serialise with `ArIsSaveGame = true`.
- **A version field from day one**; the migration for a format change lands **in the same commit** as
  the change.
- **Migrations are sequential** (v1 to v2 to v3), never per-version branches. Keep every migration
  forever.
- **Save identity and data** - a GameplayTag, an `FPrimaryAssetId`, a GUID - never a pointer.
- **Save asynchronously.**
- **Archive a save from every shipped version and load them all in CI** (14.5).

### 9.15 GAS and AI

- **GAS is a large commitment.** Skip it for a few fixed actions, no status effects, a single-player
  prototype, or a team that does not know it. The middle path - gameplay tags plus a damage pipeline
  built like 9.8 - transfers to GAS later.
- **If you use GAS:**
  - The ability system component lives on the PlayerState for respawning players (raise its
    `NetUpdateFrequency`), on the pawn for AI and one-life enemies.
  - Initialise it from one idempotent function called from both `PossessedBy` and
    `OnRep_PlayerState`.
  - Activate abilities by tag, never by class.
  - Health loss happens in exactly one place - a meta attribute resolved in
    `PostGameplayEffectExecute`.
  - Cues are cosmetic only; they do not run on a dedicated server.
- **AI:** StateTree for new work; Behavior Trees are fine - do not migrate on principle. Perception is
  event-driven; never poll for targets.
