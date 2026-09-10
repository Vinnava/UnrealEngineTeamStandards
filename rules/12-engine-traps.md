# 16. Known engine traps

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

Engine-level behaviours that **fail silently**. Read the entry before you touch the system it names.
Entries marked *(real case)* are incidents this team shipped; the incident is told in why.md.

---

### Level transitions and the PlayerController

- **`OpenLevel` destroys and recreates the PlayerController.** Anything caching a PC pointer
  re-acquires it on arrival - in `PostLoadMapWithWorld` or from the new PC's `BeginPlay` - before any
  downstream code runs.
- **Never gate transition state on a cosmetic fade callback.** A fade callback riding a widget's
  `NativeTick` never fires once a hard map load drops the widget. Reset transition state
  unconditionally on arrival; the fade is cosmetic only.
- **A hard `OpenLevel` removes persistent overlay widgets from the viewport** - the object survives,
  nothing is drawn. Fix both halves: re-`AddToViewport` on arrival, before the new world's first
  frame; drive any fade from a **subsystem `TimerManager` timer**, not the widget's tick or a UMG
  animation.
- **Clear stale widget references before re-creating them** - at the top of the re-initialisation
  path, before the "create if absent" call.
- **A world timer dies on a hard `OpenLevel`.** Anything armed on one that conceptually survives the
  load - a ringing call, a countdown - is resolved explicitly on arrival.

### Movement and animation

- **`SetActorLocationAndRotation` breaks CharacterMovementComponent** - `GetVelocity()` stays zero and
  every AnimBP blend space reads idle. **Move through the movement component**: a root motion source
  (`FRootMotionSource_MoveToForce` and its siblings) for scripted moves, or `AddMovementInput` /
  setting `movementComp->Velocity` each frame. Never override `GetVelocity()` to fake it.
- **A Blend Space Player wired to `Ground Speed` outputs idle under scripted movement** - same cause,
  same fix. If a move cannot go through the component, drive the blend from an AnimBP variable set to
  the intended speed.
- **A montage needs `Enable Auto Blend Out = ON` or `Montage_SetEndDelegate` never fires.** In a
  paired `DoThing` / `OnDoThingComplete` contract, both paths always broadcast - the no-montage path
  synchronously, the montage path on end - and callers bind *before* they call.

### Reflection and data

- **`DECLARE_MULTICAST_DELEGATE` is invisible to Blueprint.** Use the `DYNAMIC` form plus
  `UPROPERTY(BlueprintAssignable)` (9.3).
- **GameplayTag hierarchy matching is strict** - `Level.Interior.Apartment` never satisfies
  `Level.Portal.Interior.Apartment`. Authored data uses the exact tag the runtime sends.
- **`EditInstanceOnly` on a spawned actor can never be authored** - it stays at its constructor
  default. Use `EditDefaultsOnly` and assign in Class Defaults. (`EditDefaultsOnly` is Class Defaults
  only, `EditInstanceOnly` placed-instance only, `EditAnywhere` both; prefer `EditDefaultsOnly` where
  per-instance authoring is meaningless.)
- **`SpawnActor<T>(T::StaticClass())` bypasses the Blueprint CDO** - every Blueprint-assigned property
  is null. Spawn from a `TSubclassOf<T>` pointing at the Blueprint, or use `TActorIterator` to find
  placed instances.
- **A `UPROPERTY TMap` keyed on a `UENUM` is corrupted by editing that enum** - keys serialise as byte
  values, so deleting or reordering an enumerator silently re-points stored rows. Use one named
  `EditDefaultsOnly` field per case; reserve enum-keyed maps for genuinely frozen enums, never for
  designer-authored data. *(real case)*
- **`TSoftObjectPtr::IsValid()` means "already loaded", not "assigned".** This is dead code:

  ```cpp
  // DEAD CODE - never loads on first access
  if (ptr.IsValid()) { ptr.LoadSynchronous(); }
  ```

  Test "is anything assigned" with `!IsNull()`, then load asynchronously (10.3) - or, in editor tools
  and behind loading screens only, `LoadSynchronous` and null-check. Reserve `IsValid()` for "is it
  already resident". *(real case)*
- **A wire enum whose zero value is a real state makes its own fallback unreachable** - `TryGetField`
  and friends leave the output untouched on a miss. Reserve enumerator 0 as `Unknown`, with a
  derivation that never invents an accusatory state.

### Widgets and layout

- **A widget in an inactive `UWidgetSwitcher` slot has permanently zero geometry**, and a bounded retry
  cannot fix it. Resolve measurements in the call that makes the widget visible, and delete the
  construct-time attempt. Before trusting cached geometry, check for a switcher, a `Collapsed` parent
  or a retainer above you. *(real case)*
- **`SetColorAndOpacity` does not fade an opaque-material child; `SetRenderOpacity` does.** For a
  genuinely opaque-material child, overlay a plain-colour `UImage` and drive its `ColorAndOpacity`.
- **Never resolve layout by walking an engine widget's children** - internals change between versions
  and a wrong guess fails silently. Use `SLATE_ATTRIBUTE` / `SLATE_ARGUMENT` on `FArguments`, the style
  struct, or subclass and override the virtual. *(real case)*
- **`SMultiLineEditableText` runs `OnKeyDownHandler` before its own layout**, so an outer box's
  `OnKeyDown` override is dead code. One owner per input; check whether the engine widget already
  implements the hook.
- **A `SizeBox` `MaxDesiredHeight` pins a growable text box to one line, and font size is not line
  height.** Derive padding and ceiling from one measured line height
  (`GetFontMeasureService()->GetMaxCharacterHeight`): padding `(barHeight - lineHeight) / 2`, ceiling
  `barHeight + (maxLines - 1) * lineHeight`. Never author a layout constant that depends on a metric the
  details panel cannot show.

### Async and threading

- **Resolve a `TWeakObjectPtr` on the Game Thread only** - `.Get()` and `.IsValid()` off it race
  against GC (10.1).
- **An async load callback can fire after PIE has stopped.** Guard with `IsValid(this)`, and check
  `GetWorld()` before anything world-dependent.
- **A lambda that captures by reference and outlives the frame reads freed stack memory.** Copy what
  you need (10.2).
- **Streaming sub-levels load asynchronously.** Bind to `FWorldDelegates::LevelAddedToWorld` or the
  streaming level's loaded delegate - never poll, never wait a fixed delay.

### Networking

- **`ReplicatedUsing` does not fire on the machine that set the value** - on a listen server, the host
  misses the effect. Call the handler explicitly on the authority (11.3).
- **A `Server` RPC on an actor the client does not own is silently dropped.** Multicast is the
  opposite: it ignores ownership and needs replication plus net-relevancy.
- **Set `bReplicates` in the constructor.** Runtime `SetReplicates()` works only on the authority and
  only before anything depends on it; treat runtime toggling as a deliberate exception.
- **Set authoritative starting values in the constructor or `PostInitializeComponents`, not
  `BeginPlay`** - a `BeginPlay` value can miss the first replication packet.
- **`SpawnActor<T>(T::StaticClass())` also skips Blueprint `bReplicates` and update-frequency
  overrides** - the actor replicates at the wrong rate, or not at all.

### Collision and input

- **Overlap events need `bGenerateOverlapEvents` on both components**, and each must respond `Overlap`
  to the other's object type.
- **Enhanced Input `Started` and `Completed` are separate trigger events.** A hold action binds a start
  handler to `Started` and a stop handler to `Completed` (and `Canceled` if its trigger can cancel).
- **Overlaps fire per component pair, not per actor.** Filter on the component, or de-duplicate by
  actor.
- **`bTraceComplex` traces can miss in a cooked build** when complex collision was not cooked. Test
  traces in a packaged build.
- **`FHitResult::GetActor()` can be null** - `IsValid()` it. `ImpactPoint` / `ImpactNormal` for effects
  and decals; `Location` / `Normal` for movement.
- **Physics is not deterministic across machines.** Keep simulated physics out of anything
  gameplay-critical on a networked project; read physics results in `TG_PostPhysics`.
- **There are 18 custom collision channels and they cannot be renumbered.** Budget them on day one: an
  object channel is what a thing *is*; a trace channel is a kind of *question*.

### Formatting and media

- **`FDateTime::ToString` has no month-name token** and emits unrecognised tokens as literal
  characters. Use `ToFormattedString` for anything a player reads; `ToString` for ISO and machine
  strings. Verify every format string in PIE. *(real case)*
- **`UMediaPlayer` needs a `UMediaSoundComponent` for audio** - attached to the owning
  `APlayerController` from the widget context, registered and activated **before `OpenSource()`**.
