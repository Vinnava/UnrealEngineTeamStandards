# 22. Engine upgrades

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

This standard's authority rests on its engine claims being true (precedence rule 1). Engine claims
decay. This section is how they get re-checked.

---

### 22.1 Who and when

- **An upgrade has a named owner and a branch** (1.5). It is never done on the main branch and never
  by whoever happened to notice.
- **Decide the cadence once and write it in the project README** - which engine version the project
  targets, and whether it tracks minor releases.
- **Never upgrade inside a milestone.** The first week after one is the cheapest moment.
- **Read the release notes and the upgrade notes before touching anything**, and list what they say
  about the systems this project actually uses.

### 22.2 The re-verification list

**These sections contain version-pinned engine facts.** Each one is re-checked against the new
engine's source or defaults before the upgrade is called done. This list is the deliverable of an
upgrade, not a suggestion.

| Claim | Section | How to re-check |
|---|---|---|
| `AActor` defaults tick off; tick-group defaults | 3.12 | `AActor::AActor` in `Actor.cpp`; verify a live actor with `dumpticks` |
| `check` / `ensure` behaviour in Shipping; `DO_CHECK`, `DO_ENSURE` | 3.9 | `Build.h`, `AssertionMacros.h` |
| `UE_LOGFMT` token matching is positional | 6.5 | `StructuredLog.h` |
| Uninitialised reflected struct fields | 4.6 | The uninitialised-property check in `Class.cpp` |
| `Net.AutoRegisterReplicatedProperties` and the missing-registration ensure defaults | 11.3 | `NetCVars.cpp`; confirm with `cvarlist Net.` in a build |
| `NetUpdateFrequency` default, and whether the accessors exist | 11.5 | `AActor.h` - the member may be private with accessors |
| `Net.IsPushModelEnabled`, `net.Iris.UseIrisReplication` defaults and Iris status | 11.8 | `NetCVars.cpp`, `IrisCore`, the release notes |
| `ENABLE_DRAW_DEBUG` in Test and Shipping | 3.7 | `EngineDefines.h`, where it is the alias `UE_ENABLE_DEBUG_DRAWING`; `ENABLE_DRAW_DEBUG` itself is defined in `DrawDebugHelpers.h` |
| The thread-safe animation update contract | 10.6 | `AnimInstance.h` |
| A task continuation can target the game thread via `EExtendedTaskPriority::GameThreadNormalPri` | 10.4 | `Tasks/TaskPrivate.h` - the enum, and the `Launch` overload with prerequisites in `Tasks/Task.h` |
| `TAtomic` deprecated in a comment only, with no `UE_DEPRECATED` | 10.8 | `Templates/Atomic.h`. If Epic adds the macro, the compiler takes over and the 17.4 grep can go |
| `UE::FMutex` is one byte and non-recursive; `FCriticalSection` is a recursive platform mutex | 10.8 | `Async/Mutex.h`, `HAL/CriticalSection.h` |
| A `DeveloperTool` module is left out of Test and Shipping game builds | 1.6 | `bBuildDeveloperTools` in UBT's `TargetRules.cs`, and `ModuleDescriptor.cs` |
| A non-power-of-two texture never streams | 16.8, 23.1 | `UTexture::IsPossibleToStream` in `Texture.cpp` |
| `AActor::GetActorLabel` is editor-only | 16.3, 23.3 | The `#if WITH_EDITOR` block around it in `Actor.h` |
| A validator returning `NotValidated` after accepting an asset fires an ensure | 16.9, tooling | `UEditorValidatorBase::ValidateLoadedAsset` in `EditorValidatorBase.cpp` |
| `Interchange.FeatureFlags.Import.SyncToBrowser` overrides an import task's `bSyncToBrowser` | 16.9 | `ImportAssetsInternal` in `AssetTools.cpp` |
| `GlobalConfig` loads from the declaring base class's section | tooling | `CPF_GlobalConfig` in `ObjectMacros.h` - then re-run the validator test in `tooling/README.md` |
| Editor validator API shape | 18, tooling | `EditorValidatorBase.h` - the virtual signatures move between versions |
| Every trap in section 16 | 16 | Re-test the ones the project relies on; a fixed trap is worth deleting |

- **A claim that changed is fixed in this standard in the same commit as the upgrade**, with the new
  version recorded in the README's "verified against" line and a changelog entry.
- **A claim you could not verify is marked as unverified**, not left implying it was checked.
- **A trap the engine has fixed gets deleted**, with the version that fixed it noted in the changelog
  - carrying dead workarounds is how a standard becomes folklore.

### 22.3 The procedure

1. **Branch, and record the starting state** - a performance capture (13.2), a memory report (13.4),
   and the current cook time and package size. Without a before, nothing after it means anything.
2. **Rebase engine patches** (1.5) from the patch register. Each one is re-justified: an upstreamed
   or obsolete patch is deleted, not carried.
3. **Audit plugins first.** Third-party and marketplace plugins are the usual blocker; check each
   one's engine support before any other work.
4. **Build, then fix deprecations properly.** A deprecation warning is the engine telling you the
   next version will break it. Suppressing warnings to get green is how two upgrades become one
   impossible one.
5. **Run the full CI tier set** (14.5), including a clean cook and a packaged build on the lowest
   target platform.
6. **Load an archived save from every shipped version** (9.14).
7. **Re-run the re-verification list** (22.2) and fix this standard where it is now wrong.
8. **Capture performance again** and compare against step 1, line by line against the budget (13.2).
   An engine upgrade that costs 2 ms is a product decision, not a footnote.
9. **Soak it.** Play it, on hardware, before it reaches everyone.

### 22.4 What blocks an upgrade

Any of these stops the merge, and the reason is written down rather than argued:

- A budget line (13.2) regressed past its threshold with no agreed plan.
- A save from a shipped version fails to load.
- A platform's build or cert requirement is not met.
- A blocking plugin has no supported version and no replacement.
- An engine patch cannot be rebased and its behaviour has no alternative.

### 22.5 After

- **Update the README's engine version line** and the changelog.
- **Delete the workarounds the upgrade made unnecessary** - and the `DO NOT UNDO` comments (13.9)
  whose captures no longer apply.
- **Write down what hurt.** The next upgrade is done by someone who was not here.
