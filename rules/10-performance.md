# 13. Performance and platform

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

---

### 13.1 Platform constraints

| Platform | Constraints |
|---|---|
| **Mobile** (Android/iOS) | Aggressive LOD. Texture streaming. Strict draw-call and material-complexity budgets. **Never multiple high-fidelity characters in the same view.** |
| **Remote / Pixel Streaming** | Minimise per-frame messages over the streaming data channel, and batch state updates. Latency is the budget, not framerate. (The browser-to-engine channel, unrelated to replication RPCs.) |
| **PC** | No artificial constraints, **but never break the lowest target platform's build.** |

- **The most constrained platform is the binding one.**
- **Desktop and mobile:** every interactive UI system has two paths (9.1); the mobile one is under
  pressure. **Desktop-only:** do not build the second path.

### 13.2 Measure, then decide

Six principles:

1. **The bottleneck is singular.** One stage - game thread, render thread, RHI thread or GPU - sets
   the frame time. Work anywhere else returns nothing.
2. **Measure on the target, in the build you ship.** Profile a **Test** build (Shipping-like, with
   stats and the console) on the lowest target device - never a Development editor build or PIE.
3. **Optimise the distribution, not the mean.** A change that lowers the average and raises p99 is a
   regression.
4. **Deletion beats optimisation.** Ask whether it should run at all (3.12).
5. **Instrument once, benefit forever** (13.6).
6. **A fix without an after-capture did not happen.** Capture, hypothesise, change, capture again -
   keep both numbers.

- **Milliseconds are the only unit.** State the target in fps once, then work in ms.
- **Start every investigation with `stat unit`:**

  | Highest line | You are | Look at |
  |---|---|---|
  | Game | Game-thread bound | Tick count, gameplay code, AI, animation, replication |
  | Draw | Render-thread bound | Primitive count, culling, draw submission |
  | GPU | GPU bound | Shading, overdraw, resolution, shadows, Lumen, Nanite |
  | RHIT | RHI-thread bound | Submission count, driver cost |
  | Numbers fine, feels bad | Variance | Hitches and frame pacing (13.5) - `stat unitgraph` |

- Then one stat group for that stage, then a trace. `r.ScreenPercentage 50` halves the GPU time? You
  are pixel-bound.
- **Read the count before the time** - `dumpticks` and `obj list` come first.
- **A budget has line items and owners.** The project README writes the frame budget per target:
  ceiling minus a reserve, divided into lines (game thread, animation, UI, GPU passes, memory, VRAM),
  **each with a named owner**, judged on p99 and hitches per minute.
- **Check the Size Map** on any Blueprint or widget that references content.
- **Build a packaged build for the lowest target platform early and often** (section 15 has the
  editor-versus-packaged symptom list).

### 13.3 Getting assets into the cook

The cooker includes what it can reach from the cooked maps and from the Asset Manager. Nothing else
ships.

- **Register every data-driven asset type as a Primary Asset Type** - Project Settings > Asset
  Manager, with its directory and cook rule (section 15, item 19).
- **Derive those DataAssets from `UPrimaryDataAsset`.**
- **Load them by `FPrimaryAssetId` through `UAssetManager`**, not by path.
- **After adding a new asset type, check a packaged build's contents** with the Asset Audit window.
- **Set a cook rule per type** (`AlwaysCook`, `DevelopmentCook`, `NeverCook`), and **decide chunk
  assignments when you decide asset types.**
- **Default every asset reference in a DataAsset to soft.** Hard references come from `TObjectPtr` and
  `TSubclassOf` properties, `Cast To BP_X` nodes, Blueprint-typed variables, Details-panel default
  values, child actor components and DataTable rows pointing at assets. Soft pointers,
  `FPrimaryAssetId`, interfaces and tags create none.
- **Find reference debt with a loop:** Size Map (what it costs), Reference Viewer with the depth raised
  (which edge pulled it in), fix that one node, repeat.
- **Cook nightly from the first week.** Validate incremental cooks against a clean cook before every
  milestone.
- **Exclude `Developers/` and `TEMP/` from the cook** (Project Settings > Packaging > Directories to
  never cook) - 8.2.

### 13.4 Memory, GC and pooling

- **Budget four memories:** physical memory, VRAM, address space, and **object count** - GC cost
  scales with `UObject`s and references, not bytes.
- **Track `UObject` count beside bytes** (`obj list`, `stat gc`). Every component is an object.
- **Read `memreport -full` in pairs, from a packaged build.**
- **Tag every system you own with an LLM tag** (`LLM_DEFINE_TAG`, `LLM_SCOPE_BYTAG`) when you write
  it, named like its trace scopes.
- **Find reference leaks with `obj refs name=X`.**
- **Pool what is numerous and short-lived** - projectiles, impacts, damage numbers, one-shot VFX, list
  rows - and nothing else. **`Reset()` clears every member.**
- **Blurry textures are a budget conversation** (`stat streaming`). UI textures are `Never Stream`.

### 13.5 Hitches and loading

Report **hitches per minute** alongside p99. Nearly every hitch is one of five:

| Archetype | Tell | Fix |
|---|---|---|
| Synchronous load | Tied to a gameplay event; `FlushAsyncLoading` in the trace | Async load one step ahead (10.3) |
| PSO / shader compile | **First time only**, never again | PSO precaching plus a bundled PSO cache; test on a cold machine |
| Garbage collection | Regular, no gameplay link | Fewer objects, clustering, incremental GC (13.4) |
| Spawn burst | Exact gameplay-event link | Pool, stagger across frames, or do not make them actors |
| Level streaming | Same place on the map | Smaller cells, fewer actors per cell, an earlier loading range |

- **Ask "does it happen again?" first** - no means PSO. Then look two or three frames *before* the
  spike.
- **Stagger one-off work across frames.**
- **Never fix pop-in by blocking.**
- **Judge loading only in a packaged IO Store build on the slowest target storage.**

### 13.6 Instrumentation

A subsystem is not done until it has all four:

1. **A CPU scope on its update** - `TRACE_CPUPROFILER_EVENT_SCOPE(Quest_Tick)`, named `System_Verb`.
   Never the `_TEXT` form on a hot path.
2. **A counter on every queue, pool and active set** - `TRACE_DECLARE_INT_COUNTER`,
   `TRACE_COUNTER_SET`.
3. **A CSV stat matching its budget line**, with the same name (`CSV_SCOPED_TIMING_STAT`).
4. **An LLM tag** (13.4).

- Scope entry points and phases, not every function - a scope earns its place at about 50
  microseconds.
- **Bookmark the game's state machine** (`TRACE_BOOKMARK` on wave start, level loaded), never per
  frame.
- These macros compile to nothing when disabled - no `#if` needed.

### 13.7 Content costs

- **Chase draw calls only when Draw or RHIT is the highest `stat unit` line.** One parent material with
  many instances batches.
- **Review materials by screen coverage, not instruction count** (cost is instructions x pixels x
  layers). Budget VFX overdraw in screen multiples; test effects together.
- **Static switches sparingly** - they multiply permutations. Quality Switches for scalability.
- **Count the shadow-casting lights** before tuning shadows. Virtual Shadow Map cost comes from
  invalidation: moving lights, moving geometry, LOD changes, WPO.
- **Check bounds** with `FreezeRendering` and a fly-out - wrong bounds defeat every culling stage.
- **Nanite meshes need no authored LODs; everything else still does.** Decide Nanite per asset
  category, by measurement.
- **Handhelds:** measure at thermal steady state (ten minutes in, unplugged). Scalability tiers may
  change resolution, post, GI and shadows - never gameplay visibility or fairness. Answer throttling
  with dynamic resolution.

### 13.8 Server performance

- **Profile a headless dedicated server at the target player count, with bots**, from pre-production.
- **Server CPU before bandwidth** - every replicated property costs a comparison per connection per
  tick.
- **Run `dumpticks` on the server separately**, and wire significance up server-side.
- **Work through the levers in 11.5 before any architecture change**, and record the deferral with its
  number.

### 13.9 Regression gates

- **A deterministic perf test runs in CI** - fixed level, route, seed, build configuration and device,
  on dedicated hardware (Gauntlet drives it) - captures CSV, and **fails the build** when a budget
  line's p99, the hitch count, peak memory, peak VRAM or the `UObject` count passes its threshold.
- **Measure the noise floor first** - ten runs of the same build - and set the threshold well above it.
- **A failure belongs to whoever caused it, the day it lands.** The gate is never disabled
  "temporarily"; a budget change is a recorded product decision.
- **Trend as well as gate.**
- **Stop a fix being undone.** Record symptom, measurement, wrong hypothesis, root cause, fix and
  result; leave a two-line `DO NOT UNDO` comment naming the capture that justified it.
