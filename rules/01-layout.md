# 1-2. Layout

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

---

## 1. Project and module structure

### 1.1 Modules

| Module | Contains |
|---|---|
| `<Project>` | Main game module - gameplay, characters, UI, subsystems |
| `<Project>Online` | HTTP, JSON, auth, backend service classes, wire types |
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
