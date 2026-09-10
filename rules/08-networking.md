# 11. Networking and replication

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

**This section applies if the project replicates.** If it does not, read 11.1 and skip the rest.

---

### 11.1 Decide before the first feature

- **Decide replication before the first feature** and write it in the README - "this project
  replicates" or "this project is single-player".
- **Any realistic chance of multiplayer: write authority-aware code from the start**, even in a
  single-player build.
- **Definitively single-player: skip this section** rather than half-applying it.

### 11.2 Authority model

> **The server is the truth. The client is a guess.**

Every mutation of game state - spawning, destroying, state machine advances, inventory changes - runs
on the server and replicates down. The client handles input, local prediction and cosmetics.

| Check | Method | When to use |
|---|---|---|
| Running on the server | `HasAuthority()` | Before any authoritative write |
| This is our own pawn | `IsLocallyControlled()` | Input, and local cosmetic feedback |
| Dedicated vs listen vs client | `GetNetMode()` | When the three genuinely differ |

**Authority-gate every mutation.** A function that writes replicated state returns early when
`!HasAuthority()`, or is only reachable through a `Server` RPC:

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

**Where `HasAuthority()` lives** - it is an `AActor` method:

- **In an `AActor`** - call it directly.
- **In a `UActorComponent`** - `GetOwner()->HasAuthority()`, null-checked.
- **In a `UObject` or a subsystem** - there is no authority to ask. Route the decision through the
  owning actor, or check `GetWorld()->GetNetMode() != NM_Client` if you only need "am I not a client".
- **A subsystem that drives authoritative state does so through an actor with authority** - usually
  the GameMode, GameState or a PlayerController.

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

- **Register every replicated property in `GetLifetimeReplicatedProps`.** Both engine defaults are
  silent in UE 5.7 and 5.8 (`NetCVars.cpp`):
  - `Net.AutoRegisterReplicatedProperties` (default **on**) registers a forgotten property with no
    condition - it replicates to everyone.
  - With auto-registration off, it never replicates. `Net.EnsureOnMissingReplicatedPropertiesRegister`
    (default **off**) makes that an `ensure`.

  **On a replicated project, set auto-registration to `0` and the ensure to `1`** under
  `[ConsoleVariables]` in `DefaultEngine.ini`, and fix everything the ensure reports - plugin classes
  included - before committing the setting. Mark a property deliberately not replicated in a subclass
  with `DISABLE_REPLICATED_PROPERTY`.
- **Call `Super::GetLifetimeReplicatedProps` first.**
- **Name the `OnRep_` after its property**, not after what it does - `OnRep_ActiveQuestTag`, not
  `OnRep_QuestChanged`.
- **The `OnRep_` parameter holds the previous value**; the member already holds the new one.
- **`OnRep_` does not fire on the server.** Logic for both sides goes in a separate function, called
  from the mutation site on the server **and** from the `OnRep_` on clients.
- **`OnRep_` also fires on initial replication and on re-entering relevancy, and is skipped when the
  value returns to what the client already had.** Use `REPNOTIFY_Always` for values that can
  oscillate (health, ammo).
- **Replicate state, not events.** `currentHealth` is state; "took damage" is an RPC, or a local
  response to the state change.
- **The test for property versus RPC:** *would a player joining right now need to know this?* Yes - a
  replicated property. No - an RPC.
- **Do not replicate what a client can derive. Never replicate UI state.**
- **Never count events by diffing a replicated value** - clients never see intermediate values.
- **Replicated means readable** by that client. `COND_OwnerOnly` is the only defence against another
  player reading it.
- **Collections that change more than rarely use `FFastArraySerializer`**, mutated only through the
  list's own methods with `MarkItemDirty` / `MarkArrayDirty`.
- **Quantise vectors** (`FVector_NetQuantize`, `_10`, `_100`, `_Normal`) wherever full precision is not
  needed.
- **Replicated subobjects use the registered list** - `bReplicateUsingRegisteredSubObjectList = true`,
  with matched `AddReplicatedSubObject` / `RemoveReplicatedSubObject` calls.

**Choose the replication condition deliberately - the default sends to everyone:**

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

- **The initialisation race.** The controller, the PlayerState and replicated properties arrive in any
  order, possibly after `BeginPlay`. Write one idempotent `TryInitialise()` that checks its own
  preconditions, called from `BeginPlay`, `PossessedBy`, `OnRep_Controller` and `OnRep_PlayerState`.
- **Cutting bandwidth, in this order:** replicate less, conditions, lower frequencies, fast arrays,
  quantisation, a property instead of a frequent multicast, dormancy, custom `NetSerialize`, push model.

### 11.4 RPCs

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

- **`Reliable` for any game-state change. `Unreliable` for cosmetics** and for streaming data that is
  superseded shortly after. **Never send a state change unreliably.**
- **No per-frame call on a reliable RPC** - the reliable buffer can overflow and disconnect the client.
- **Every `Server` RPC has `WithValidation`.**
- **`_Validate` rejects only the impossible or malformed** - failing it disconnects the player.
  Gameplay rules are re-checked in `_Implementation`, assuming the client checked nothing.
- **The client sends intent, never outcome.** Never accept a client's hit result.
- **A `Server` RPC only routes if the calling client owns the actor** - otherwise it is silently
  dropped.
- **A `NetMulticast` RPC depends on the actor replicating and being net-relevant**, not on ownership.
  It never reaches late joiners. Multicast is for cosmetic, fire-and-forget effects only; it is
  throttled - never a state channel.
- **Never fire an RPC from a constructor or from `GetLifetimeReplicatedProps`.**
- **Call an RPC by its plain name**, never `_Implementation`.

### 11.5 Relevancy and update frequency

**`NetUpdateFrequency` defaults to 100 Hz.** Set it in the constructor for every replicating actor:

```cpp
AGameCharacter::AGameCharacter()
{
    bReplicates = true;

    SetNetUpdateFrequency(30.0f);
    SetMinNetUpdateFrequency(10.0f);   // Floor used when the actor is deprioritised
}
```

- **Prefer the `SetNetUpdateFrequency()` / `GetNetUpdateFrequency()` accessors** where your engine
  version has them; direct member assignment may compile, warn or fail depending on the version.

| Actor type | Typical frequency |
|---|---|
| Player-controlled character | 30-60 Hz |
| AI or NPC character | 10-20 Hz |
| Interactive world object | 5-10 Hz |
| Rarely-changing actor | 1-5 Hz |

- **An actor whose state never changes at runtime does not replicate at all.**
- **`bAlwaysRelevant` stays false** except for things that genuinely are always relevant - GameState,
  PlayerState.
- **Fix relevancy before you tune frequency.**
- **Rarely-changing actors - doors, chests, spawners - start `DORM_Initial`.** **Call
  `FlushNetDormancy()` before changing a dormant actor.**
- **`NetPriority` decides what survives when bandwidth saturates.** Raise the PlayerState's low default
  update frequency if you put fast-changing data there.
- **Before any architecture change, in order:** relevancy, dormancy, frequency, priority, then an
  audit that deletes unused properties and makes the rest owner-only where it can. Replication Graph
  and Iris are mutually exclusive; justify either with a server capture (13.8).

### 11.6 Naming

An RPC prefix states **where the function runs**, and is mandatory:

| Kind | Prefix | Example |
|---|---|---|
| `Server` RPC | `Server` | `ServerRequestInteract` |
| `Client` RPC | `Client` | `ClientNotifyPurchaseFailed` |
| `NetMulticast` RPC | `Multicast` | `MulticastPlayHitEffect` |
| RepNotify handler | `OnRep_` | `OnRep_ActiveQuestTag` |

- **Underscores in function names only for engine-required forms** - the `OnRep_` prefix and the
  `_Implementation` / `_Validate` suffixes. The only other underscores in names are the polymorphic
  class family (4.4) and the bind-name member (7.4).
- **RPC prefixes stay PascalCase and unbroken** - `ServerRequestInteract`, not
  `Server_RequestInteract`.

### 11.7 Testing

- **Test in PIE with at least two clients**, and **with Run Under One Process disabled** at least once
  per feature.
- **Test as a dedicated server, not only as a listen server.** Default PIE to a dedicated server.
- **Keep simulated latency and loss on in your normal setup** (`Net PktLag=120`, `Net PktLoss=3`).
- **Package and run a real dedicated server build weekly** from the first month.
- **On a listen server the host has both authority and local control** - code that handles each
  separately fires twice there.
- **Watch the bandwidth** with `stat net` and the Network Profiler.

### 11.8 Push model and Iris

Both are **off by default in UE 5.7 and 5.8** (`Net.IsPushModelEnabled`,
`net.Iris.UseIrisReplication`). Decide on both alongside 11.1, and write the answer in the README.

- **Push model:** enable with `Net.IsPushModelEnabled=1` and a `NetCore` dependency, register properties
  with `DOREPLIFETIME_WITH_PARAMS_FAST` and `bIsPushBased = true`, and call
  `MARK_PROPERTY_DIRTY_FROM_NAME` at every write. **Route every write through a setter** - an unmarked
  write does not replicate. It pays off for many properties that change rarely; it is the last step
  of the bandwidth order in 11.3.
- **Iris** is Epic's replacement replication system - production-ready in 5.8 according to Epic's
  release notes, but still opt-in. Every rule in this section still applies. Never switch a project to
  it mid-development without a spike on a branch first.

### 11.9 Prediction

- **Predict only what passes all three:** the player would feel the latency; the client has all the
  information; being wrong is cleanly reversible. Never predict damage to others, server-only
  information or randomness.
- **Custom movement goes inside the CharacterMovementComponent**, with its own `FSavedMove_Character`:
  every custom field captured in `SetMoveFor` and restored in `PrepMoveFor`, intent packed into the
  four custom compressed flags.
- **A custom movement mode reads only velocity, acceleration, intent flags and the world; uses no
  randomness; and checks its exit condition first.**
- **Aim for zero corrections the player can feel** - watch them with `p.NetShowCorrections 1`.
- **Server-side rewind** for hit registration is a design decision. Cap the rewind window.
