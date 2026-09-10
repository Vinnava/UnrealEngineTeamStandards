# 10. Async and threading

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

---

### 10.1 The rule that has no exceptions

> **All `UObject` access, creation and destruction happens on the Game Thread.**

Results produced on a background thread are marshalled back before they touch a `UObject`:

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

- **Capture the payload by value.** The background lambda never reaches back into the calling frame.
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
- **Load only what the screen needs** - tag DataAsset fields with `meta = (AssetBundles = "UI")`.

### 10.4 Background work

- **Prefer `UE::Tasks`, `Async` / `AsyncTask` and the TaskGraph over `FRunnable`.** `FRunnable` only
  for a persistent thread with its own lifecycle - an I/O pump, an audio capture loop.
- **Prefer the 10.1 pattern to a `TFuture` `.Then()` chain** - `.Then()` runs on an unspecified thread.

**The only safe shape is gather, compute, apply:**

1. **Gather** on the game thread - copy the world state you need into a plain-value snapshot.
2. **Compute** on workers - a pure function of the snapshot, writing to disjoint outputs.
3. **Apply** on the game thread - re-validate the owner (a `TWeakObjectPtr`) and write back.

If phase 2 needs a lock, the split is wrong - widen the snapshot. If the gather costs more than the
compute, do not parallelise.

- **Launch new work with `UE::Tasks::Launch`**, many independent items with `ParallelFor`, `AsyncTask`
  where you need a named thread. Prefer a `UE::Tasks::FPipe` to a mutex.
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
