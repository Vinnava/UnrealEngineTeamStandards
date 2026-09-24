# 1-2. Layout

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

---

## 1. Project and module structure

### 1.1 Modules

| Module | Contains |
|---|---|
| `<Project>` | Main game module - gameplay, characters, UI, subsystems |
| `<Project>Online` | HTTP, JSON, auth, backend service classes, wire types - rules in section 21 |
| `<Project>Editor` | Editor-only tooling, if any |

- Keep `HTTP` / `Json` dependencies out of the game module.
- Keep the online module's public headers small - a change to them recompiles the game module.

### 1.2 Build.cs discipline

- **Every dependency gets a one-line comment naming the feature that needs it.**

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
- **A `.Build.cs` change needs regenerated project files and a full build with the editor closed.**
  Live Coding cannot apply it (section 15, item 1).

### 1.3 Source folder layout

Folder path mirrors the class's **role**, not its feature:

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

**If you cannot tell which folder a new class belongs in, the class is doing two jobs.** Split it.

### 1.4 Compile-time gating

| Code that exists only for | Gate |
|---|---|
| Editor-only member variables | `#if WITH_EDITORONLY_DATA` |
| Editor-only functions and logic | `#if WITH_EDITOR` |
| Development tooling stripped from Shipping | `#if !UE_BUILD_SHIPPING` |
| Dedicated-server-only code | `#if UE_SERVER` |

- **Editor tooling goes in an editor module** (`"Type": "Editor"` in the `.uproject` or `.uplugin`),
  which the cook strips - not in the game module behind `#if WITH_EDITOR`.
- **Every `StartupModule` registration has a matching `ShutdownModule` release.** An unbalanced pair
  crashes on exit and on Live Coding.

### 1.5 Plugins and engine changes

- **A plugin is a product.** It never references game code, talks outward only through interfaces
  and delegates, is configured by data, versions its serialised data - and **works in an empty
  project**. Automate that last test.
- **Before changing engine behaviour, stop at the first of these that works:** design around it, an
  engine extension point, a plugin, a patch, a fork.
- **If you patch the engine,** do it on a branch, wrap every change in `// <PROJECT>-BEGIN` /
  `// <PROJECT>-END` markers, record it in a written patch register, and upstream what you can.

### 1.6 Prototype code

> **Prototype code lives in its own module, is held only to the safety rules, and is rewritten - never
> moved - when it graduates.**

Planning first, `CONFLICT` blocks, naming, logging format and review discipline are right for
production and heavy for finding out whether an idea is fun. This is where that overhead is waived, and
the fence that stops the waiver spreading.

- **One `<Project>Prototype` module, type `DeveloperTool`.** A `DeveloperTool` module is built for the
  editor and for Debug and Development game builds, and left out of Test and Shipping - it is built
  only where the target's `bBuildDeveloperTools` is true, which defaults to false for Test and Shipping
  game targets. The Shipping binary cannot contain prototype code, because it is never compiled into it.
- **The dependency points one way.** The prototype module may depend on the game module; nothing in
  the game module ever depends on the prototype module, includes its headers or loads its classes.
- **Prototype content lives in `TEMP/`** (8.2), which the cook already excludes (13.3).
- **What still applies in the prototype module - the safety rules, because a crash in a prototype
  still costs a day:** `UObject` lifetime and `UPROPERTY` pointers (3.8), `IsValid` (3.4), the game
  thread (10.1), weak captures in lambdas (10.2), no `TAtomic` (10.8), no secrets in source (21.4),
  and the encoding rules (5.5). From the 17.1 gate: build, PIE, reading assistant-written code,
  `UObject` pointers, teardown, the game thread and authority.
- **What is waived:** plan-first and `CONFLICT` blocks (14.1), naming (4), comments (5), logging format
  and `LogTemp` (6), header order (3.1), Tick approval (3.7), tests (14.4), and the rest of the gate.
  `tooling/check-project.py` applies the same split automatically.
- **Graduating is a rewrite.** When a prototype earns a place in the game, it is written again in the
  game module to the full standard, with the prototype as a reference, not a starting point. Code
  copied out of the prototype module carries its waivers with it, and that is how they spread.
- **A prototype older than a milestone is either graduated or deleted.** The module is for finding
  out, not for keeping.

---

## 2. Content folder structure

### 2.1 One root for everything you author

All project content lives under one underscore-prefixed root, `Content/_<Project>/`. Inside it,
mirror the source layout where it makes sense:

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

- Marketplace, Fab, Quixel and MetaHuman content **stays where it landed**. Never reorganise it and
  never edit it in place.
- **To modify a third-party asset, duplicate it into `_<Project>/` first.**

### 2.3 No content outside the root

- Never save an asset directly to `Content/` or into a marketplace folder.
- Move a stray one deliberately, in its own change - the move creates a redirector.
