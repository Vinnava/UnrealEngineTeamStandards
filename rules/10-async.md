# 10. Async and threading

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

---

### 10.1 The rule that has no exceptions

> **All `UObject` access, creation and destruction happens on the Game Thread.**

Results produced on a background thread are marshalled back before they touch a `UObject`:

```cpp
UE::Tasks::Launch(UE_SOURCE_LOCATION,
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

`UE::Tasks::Launch` starts the work because that is what 10.4 says to reach for first; the return leg
is `AsyncTask(ENamedThreads::GameThread, ...)` because the game thread is exactly the named thread
that call is still for.

- **This apply is unconditional, which is only safe if nothing else can write that state while the
  task runs.** If anything can - a player action, a replication update, another system - the apply
  must detect that its result is stale (10.7). Pasting this example into such a system is the bug.
- **Capture the payload by value.** The background lambda never reaches back into the calling frame.
- **State thread affinity in the header comment** whenever it is not the default:
  `Game thread only`, `Any thread`, or `Thread-safe`. The comment is the contract the `check` enforces.
- **Assert the contract** in any function that must only run on the Game Thread:

```cpp
void UInventorySubsystem::ApplyResult(const FInventoryResult& result)
{
    check(IsInGameThread());
    ...
}
```

### 10.2 Lambda captures

**Never capture a raw `UObject*` in a lambda that outlives the current frame.** Capture
`TWeakObjectPtr<T>` and resolve it inside:

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

- **`[this]` only when the lambda finishes before the owner can be destroyed** - a same-frame inline
  call, a sort predicate, a `ForEach` body. Anything crossing a frame, an async load, an HTTP response
  or a background task uses a weak pointer.
- **Never capture by reference (`[&]`) in a lambda that outlives the frame.** Copy what you need.
- **Non-`UObject` shared state uses `TSharedPtr` / `TSharedRef`**; capture a `TWeakPtr` if the lambda
  can outlive the owner.
- **Resolve the weak pointer once at the top and null-check it.** Never call `.Get()` repeatedly.

### 10.3 Async asset loading

Load soft references (3.5) through `UAssetManager::GetStreamableManager()`:

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

- **The callback fires on the Game Thread** - no marshalling needed.
- **Null-check the loaded asset in the callback anyway.**
- **The handle is the ownership.** Store the `TSharedPtr<FStreamableHandle>` in a member; cancel it in
  `EndPlay`.
- **Define the not-yet-loaded window** - an explicit fallback with a Warning log.
- **Every soft reference has a named preload moment** - load one step ahead of need.
- **`LoadSynchronous` in a gameplay path is the bug** (13.5). Allowed in editor tools and behind a
  loading screen - as are `LoadObject` and `StaticLoadObject`.
- **An allowed synchronous load outside an editor module says so**: `// sync-load-ok: <reason>` on the
  same line or the line above - `// sync-load-ok: behind the loading screen`. The marker is what lets
  `tooling/check-project.py` tell an exception from a hitch, so an unmarked one fails CI.
- **Load only what the screen needs** - tag DataAsset fields with `meta = (AssetBundles = "UI")`.

### 10.4 Background work

- **Prefer `UE::Tasks`, `Async` / `AsyncTask` and the TaskGraph over `FRunnable`.** `FRunnable` only
  for a persistent thread with its own lifecycle - an I/O pump, an audio capture loop.
- **Prefer the 10.1 pattern to a `TFuture` `.Then()` chain** - `.Then()` runs on an unspecified thread.

**The only safe shape is gather, compute, apply:**

1. **Gather** on the game thread - copy the world state you need into a plain-value snapshot. The
   snapshot holds values and IDs (`FGameplayTag`, `FName`, `FGuid`, `FSoftObjectPath`), **never a
   `UObject` pointer** - a pointer in the snapshot is a `UObject` access waiting to happen on the
   worker, whether or not anyone dereferences it today.
2. **Compute** on workers - a pure function of the snapshot, writing to disjoint outputs.
3. **Apply** on the game thread - re-validate the owner (a `TWeakObjectPtr`) and write back.

If phase 2 needs a lock, the split is wrong - widen the snapshot. If the gather costs more than the
compute, do not parallelise.

- **Write heavy logic as pure functions from the start, threaded or not** - a namespace or `static`
  function that takes `const` inputs, returns by value, and never calls `GetWorld()`, spawns, touches
  UMG or reads a `UObject`. Such a function moves to a worker unchanged later, and is unit-testable now
  (14.4). This is the cheap half of being ready to thread; the expensive half waits for evidence (10.9).
- **The result depends only on the inputs** - never on call order or which frame it ran in.
- **While the system is still synchronous, compute may take a `const` view** (`const TMap&`,
  `TConstArrayView`) instead of a copied snapshot. Copy at the moment compute actually moves to a
  worker, not before.
- **Async logs name the phase** - `[Dispatch]`, `[Worker]` or `[Apply]` after the function name
  (6.1). A threaded bug is otherwise three interleaved log lines nobody can order.

- **Launch new work with `UE::Tasks::Launch`**, many independent items with `ParallelFor`, `AsyncTask`
  where you need a named thread. Prefer a `UE::Tasks::FPipe` to a mutex.
- **A task continuation does not run on the game thread by default.** A continuation launched with
  prerequisites runs on a worker, so an apply written as a continuation writes `UObject`s off the game
  thread. To apply from a continuation, launch it with
  `UE::Tasks::EExtendedTaskPriority::GameThreadNormalPri`; otherwise return through
  `AsyncTask(ENamedThreads::GameThread, ...)` as in 10.1.
- **`ParallelFor` only when each item's work is substantial and independent.** Pre-size the output and
  write to `[Index]` - never `Add` to a shared container, never lock inside the body. Measure both ways
  (`EParallelForFlags::ForceSingleThread`).
- **No `Wait()` right after `Launch()`.**
- **Capture by value, `MoveTemp` large payloads, cross threads with a `TQueue`.**

If you do need an `FRunnable`:

- Implement a real `Stop()` and `Exit()`; the run loop checks the stop flag.
- **Call `Stop()` and join the thread from the owner's `Deinitialize` or `BeginDestroy`.**
- **Never let a thread outlive the object that owns it.**

### 10.5 Timers, delegates and other deferred callbacks

- **Store every `FTimerHandle` and clear it in teardown** - `EndPlay`, `Deinitialize`,
  `NativeDestruct`.
- **Unbind every delegate in the matching teardown** (9.3).
- **A world timer does not survive a hard `OpenLevel`** (9.5). Anything that must survive a map load
  uses a GameInstance subsystem's timer manager.

### 10.6 Animation Blueprints

**Gather on the game thread, derive on a worker.**

- **`NativeUpdateAnimation`** (game thread): copy what the graph needs - velocity, flags, aim - out of
  the pawn and its components into member variables. Nothing else.
- **`NativeThreadSafeUpdateAnimation`** (worker, before the graph updates): compute everything derived
  from those copies - blend weights, speed bands, lean. The engine header gives the same advice
  (`AnimInstance.h`).
- **The thread-safe update never touches another `UObject`.**
- **In Blueprint, mark AnimBP functions Thread Safe and read through property access**, keep
  multi-threaded animation update on, and fix every thread-safety warning the Anim Blueprint compiler
  raises.
- **For crowds, use update rate optimisation (URO) and the animation budget allocator**, tuned by
  screen size, not distance.

### 10.7 Stale results

> **An async result is applied only if the data it was computed from has not changed since.**

A task takes a frame or more. If the player acts, a replication update lands or another system writes
while it runs, an unconditional apply silently overwrites the newer state with the older result. It
never crashes and never logs; the player's action just disappears.

**Give each owned data set a generation counter**, increment it on every write, record it at gather,
and compare at apply:

```cpp
// Header
private:   // Variables
    /** Incremented on every write to affinityMap, so an async apply can tell it is stale (10.7) */
    uint32 affinityGeneration;

public:    // Functions
    /** Recalculates all affinity on a worker. Game thread only */
    void RecalculateAllAffinityAsync();
```

```cpp
UAffinitySubsystem::UAffinitySubsystem()
{
    affinityGeneration = 0;
}

void UAffinitySubsystem::RecalculateAllAffinityAsync()
{
    check(IsInGameThread());

    // Gather - copy what the worker needs, and remember which version of the data it saw
    TArray<FAffinityData> snapshot;
    affinityMap.GenerateValueArray(snapshot);
    const FAffinityRules rules = affinityRules;
    const uint32 gatheredGeneration = affinityGeneration;

    UE::Tasks::Launch(UE_SOURCE_LOCATION,
        [weakSelf = TWeakObjectPtr<UAffinitySubsystem>(this), snapshot = MoveTemp(snapshot), rules,
            gatheredGeneration]()
    {
        // Worker - copies only; weakSelf is carried through, never resolved here
        TArray<FAffinityData> results = AffinityMath::DecayAll(snapshot, rules);

        AsyncTask(ENamedThreads::GameThread,
            [weakSelf, results = MoveTemp(results), gatheredGeneration]() mutable
        {
            UAffinitySubsystem* self = weakSelf.Get();
            if (!IsValid(self))
            {
                return;
            }

            self->ApplyAffinityResults(MoveTemp(results), gatheredGeneration);
        });
    });
}

void UAffinitySubsystem::ApplyAffinityResults(TArray<FAffinityData>&& results, const uint32 gatheredGeneration)
{
    check(IsInGameThread());

    if (gatheredGeneration != affinityGeneration)
    {
        UE_LOGFMT(LogGameAffinity, Verbose,
            "[{Obj}] [ApplyAffinityResults] [Apply] Stale result discarded, gathered {Gathered} current {Current}",
            GetNameSafe(this), gatheredGeneration, affinityGeneration);
        return;
    }

    for (FAffinityData& result : results)
    {
        affinityMap.Add(result.targetTag, MoveTemp(result));
    }

    ++affinityGeneration;
}
```

- **Every write path increments the counter** - the apply above, and every other one
  (`ApplyPlayerAction` and the rest). One path that forgets makes the check meaningless. This is what
  9.4's single write path is for: the counter is incremented in one place because writes happen in
  one place.
- **Equality, not ordering.** Compare with `!=`, so wrap-around after four billion writes is harmless.
- **Discard is the default; re-dispatch when the result must eventually land.** Discarding is the
  simplest safe policy. If the computation is rare or expensive and the latest state must always be
  processed, re-dispatch from the apply instead of dropping.
- **The owner being destroyed is not staleness** - that is the `IsValid` return above (10.2), and it
  is silent because it is expected on every level transition (6.6).

### 10.8 Shared state

**Gather, compute, apply (10.4) exists so that workers share nothing.** When sharing really is
unavoidable, use the first rung of this ladder that fits:

| Need | Use |
|---|---|
| Hand results from workers to the game thread | A `TQueue`, or a `UE::Tasks::FPipe` (10.4) - no lock of your own |
| One value - a flag, a counter, a cancel request | `std::atomic<T>` |
| Several values that must change together | `UE::FMutex` with `UE::TUniqueLock` |

```cpp
// Header
private:   // Variables
    /** Guards pendingResults. Held only to swap the array, never across a call out */
    UE::FMutex pendingResultsMutex;

    /** Written by workers, drained on the game thread. Thread-safe via pendingResultsMutex */
    TArray<FScanResult> pendingResults;
```

```cpp
void UScanSubsystem::DrainPendingResults()
{
    check(IsInGameThread());

    TArray<FScanResult> drained;
    {
        UE::TUniqueLock lock(pendingResultsMutex);
        Swap(drained, pendingResults);
    }

    for (const FScanResult& result : drained)
    {
        ApplyScanResult(result);
    }
}
```

- **`UE::FMutex` for new code.** It is one byte and does not support recursive locking, so re-entering
  a lock you already hold deadlocks in testing instead of passing unnoticed. `FCriticalSection` with
  `FScopeLock` is fine in existing code; in 5.7 it is a recursive platform mutex
  (`UE::FPlatformRecursiveMutex`), and needing recursion usually means the locked region is too big.
- **Never `TAtomic`.** It is deprecated, but only in a comment (`Atomic.h`) - there is no
  `UE_DEPRECATED`, so the compiler never warns. Use `std::atomic`; the check is a grep (17.4).
- **`volatile` is not synchronisation.** It neither orders memory nor makes anything atomic.
- **Hold a lock for the shortest possible time and never call out while holding it** - no delegate
  broadcast, no virtual call, no `UObject`, nothing that can re-enter. Copy or swap under the lock,
  then work outside it, as above.
- **Say what each lock guards** in the comment on the mutex member, and say `Thread-safe via` on each
  member it guards (10.1).

### 10.9 Thread on evidence, not in advance

> **Design every system so it could be threaded. Thread one only when a capture proves it has to be.**

Threading early is usually wasted effort. The bottleneck is rarely known early, `UObject`s force
hand-offs back to the game thread, every dispatch has a cost, and race conditions are the most
expensive bugs to reproduce. Unreal already runs rendering, RHI, audio, asset loading, animation
evaluation, Niagara and physics off the game thread; this section is about **your gameplay code**.

**Move a system off the game thread only when all four are true:**

1. **The game thread is the bound line** in `stat unit` (13.2). If GPU, Draw or RHIT is higher,
   threading gameplay code cannot help.
2. **The system consistently costs at least the threading threshold** on the lowest target device, or
   causes a visible hitch. The default estimate is **about 6 per cent of the frame budget** (1 ms at
   60 fps), calibrated against a real capture and written into the project's budget (13.2).
3. **The work is separable** - it runs on a copied snapshot without touching a `UObject` mid-compute
   (10.4).
4. **The result can arrive a frame or more late**, or there is a defined synchronisation point.

If any of the four fails, **optimise on the game thread instead**: do less, cache, or spread the work
across frames (13.5).

- **Check the usual suspects first.** Most frame problems are asset streaming, PSO compilation, GPU
  cost or memory pressure (13.5), and threading gameplay code fixes none of them.
- **Dispatch is not free.** Below roughly 50-100 microseconds of work, scheduling and cache misses can
  cost more than the work saves. Treat that as an order of magnitude and measure it.
- **The pull request that threads a system links the before capture** and shows the after capture on
  the lowest target device (13.2, principle 6). No capture, no threading.
- **Everything cheap is already required, threaded or not:** pure compute functions (10.4), one write
  path (9.4), IDs rather than pointers in snapshots (10.4), and a generation counter wherever async
  results land (10.7). That is what makes threading a system later a local change, not a rewrite.

### 10.10 Threading candidates

**`[team-size]`** - a registry is only worth keeping when someone runs profiling milestones on target
hardware. Without that, apply 10.9 before threading anything and skip the bookkeeping.

A **threading candidate** is a system that meets criterion 1 below, and criterion 2 or 3:

1. It processes a collection that grows with content - entities, data rows, state entries - not a fixed
   small set.
2. It runs during gameplay, outside loading screens, often enough that a spike would be visible.
3. A capture shows it costing at least the registry threshold - **about 3 per cent of the frame budget**
   (0.5 ms at 60 fps) by default - or causing a hitch.

Candidates are listed in the project's `CLAUDE.md`, in its "Threading candidates" table, and the
system's class comment carries the greppable marker `THREADING-CANDIDATE`, so CI can diff the two.

**A candidate is shaped for threading before it is threaded:**

- **Gather, compute and apply are three separate functions** (10.4), even while all three run on the
  game thread.
- **Its API is callback-shaped** - `RequestLookupIndexAsync(onReady)` - even if it completes
  synchronously today. Callers assume neither that the callback has fired when the call returns, nor
  that it has not; review checks every caller for code that reads state straight after the request.
- **It tolerates a result arriving one or more frames late**, where the design allows.

**A system that is not a candidate stays synchronous** - return by value, no callback, no `Async`
suffix (4.3). Shaping an unregistered system for threading is speculative complexity, and a review
defect just as skipping it on a registered one is.

- **Registering is a pull request** that adds the row and states which criteria it meets.
- **Re-check every entry at each profiling milestone.** A system that no longer costs anything on the
  lowest target is removed, and may be simplified back to synchronous.
- **A registry longer than a handful of entries means the criteria are being misread.**
