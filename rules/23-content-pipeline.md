# 23. Content pipeline

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

**How content gets from a DCC tool into the game, for artists, designers and the programmers who
support them.** Every rule carries where its authority comes from:

- **[engine]** - verified in engine source, and re-checked on every upgrade (22.2).
- **[tool]** - fails the build through `AssetContentValidator` (18.2).
- **[convention]** - common practice in production studios, written without an art or design lead.
  These are the defaults until a project has leads, who review them in a pilot ([PILOT.md](../PILOT.md)).
  A convention a lead overrules is changed here, not quietly ignored.

Naming is 7.1; performance budgets are 13.4 and 13.7; audio import is 19.10.

---

### 23.1 Textures

- **[tool] Powers of two, or padded.** A non-power-of-two texture never streams: `UTexture::IsPossibleToStream`
  refuses it at runtime, so it sits in memory at full resolution the whole time it is loaded (16.8).
  Author power-of-two sizes, or set **Power Of Two Mode** to pad. UI textures are exempt - the UI
  texture group never streams anyway - as is a texture deliberately marked **Never Stream**.
- **[tool] Stay under the size budget.** A texture without virtual texturing is at most the project's
  `maxTextureSize` on its longest side - 4096 unless the project's `DefaultEditor.ini` says otherwise.
  Going over needs virtual texturing, or a budget change recorded in the project README (13.2).
- **[convention] A texture that feeds a material ends in its map type**, and the map type fixes its
  compression and colour space:

  | Suffix | Map | Compression | sRGB |
  |---|---|---|---|
  | `_D` | Base colour | Default | On |
  | `_N` | Normal | Normalmap (BC5) | Off |
  | `_ORM` | Packed: occlusion in R, roughness in G, metallic in B | Masks | Off |
  | `_M` | Any other mask, single or packed | Masks | Off |
  | `_E` | Emissive | Default, or HDR when values exceed 1 | On |
  | `_H` | Height or displacement | Grayscale | Off |

  `T_Rock_D`, `T_Rock_N`, `T_Rock_ORM`. UI textures and HDRIs carry no suffix. **[tool]** The validator
  fails an `_N` that is not Normalmap, a `_D` with sRGB off, and an `_ORM` or `_M` with sRGB on - a mask
  read as sRGB is subtly wrong on every surface that samples it, and nothing else reports it.
- **Set the texture group** (`LODGroup`) for the texture's category. The group is how streaming,
  mip bias and per-platform limits apply to a whole category at once; a texture left in the default
  group escapes every one of them. UI textures use the UI group (13.4).
- **[convention] Import at the largest resolution the asset will ever need.** Reduce per platform with
  the texture group or LOD bias, never by importing a smaller copy - a smaller source cannot be undone.
- **Nothing player-readable is baked into a texture** (20.5).

### 23.2 Meshes

- **Author at real-world scale: one Unreal unit is one centimetre.** Physics assumes it - the engine's
  default gravity is `-980` (`BaseEngine.ini`), which is Earth's in centimetres per second squared.
  A mesh at the wrong scale falls, collides and sounds wrong at once.
- **The pivot is where the mesh is placed or turned** - the base of a prop, the hinge of a door - so
  it snaps and rotates without an offset.
- **[convention] Export clean:** transforms applied (zero rotation, unit scale), one asset per export
  file except a modular kit, and one project-wide choice of whether the DCC or the engine computes
  normals and tangents. The export file carries the asset's name (23.4).
- **[tool] A non-Nanite mesh above the triangle threshold carries LODs.** The threshold is the
  project's `lodTriangleThreshold`, 1000 unless configured. A reduction **LOD Group** on the mesh is
  enough; hand-authored LODs are better where silhouette matters. Nanite meshes build their own and
  need none (13.7).
- **Anything a player or physics touches has simple collision** - authored hulls or generated
  shapes. **Complex-as-simple** is a per-asset decision for static geometry that genuinely needs exact
  collision, never a default; and a trace against complex collision can miss in a cooked build where
  it was not cooked (16.7).
- **[engine] An authored collision hull is named for its render mesh:** `UCX_` (convex), `UBX_` (box),
  `USP_` (sphere) or `UCP_` (capsule), then the render mesh's exact name in the source file, optionally
  numbered - `UCX_Crate`, `UCX_Crate_01`. The importer pairs hulls by that name; a hull matching no
  render mesh is reported and not attached.
- **[engine] A static mesh's socket is authored as an empty node named `SOCKET_<Name>`**, which the
  importer turns into a socket - so attach points live in the source file and survive re-import.
- **[convention] Material slots are named for what they are** (`Body`, `Glass`, `Trim`), and their count
  is budgeted per category (23.8) - each slot is a separate draw.
- **[convention] Lighting is decided per project, before the first mesh:** if any lighting is baked,
  every static mesh has a non-overlapping lightmap UV channel, generated or authored.

### 23.3 Levels

- **Code finds a placed actor by tag, GameplayTag or soft reference - never by its label or name.**
  An actor's label is editor-only data and does not exist in a cooked build (16.3).
- **Large and open levels use World Partition.** Converting a level to World Partition turns on One
  File Per Actor - each actor saved to its own file - which ends level merge conflicts and multiplies
  file count (26.2).
- **Content that switches on and off - a quest stage, a time of day - is a Data Layer** in a World
  Partition level, not a second copy of the map. A duplicated map is two maps that drift.
- **Streaming is asynchronous** (16.5): code that depends on a streamed region binds to its loaded
  event and never waits a fixed time.
- **[convention] A level that is not partitioned is split by discipline** - a persistent `L_Hub` with
  `L_Hub_Art`, `L_Hub_Lighting`, `L_Hub_Audio` and `L_Hub_Gameplay` sub-levels - so people lock
  different files and work at the same time.
- **[convention] No gameplay logic in a Level Blueprint.** It cannot be reused, referenced or tested,
  and it hides game rules in a map (8.1). A level's moment is an actor or a data-driven step; the Level
  Blueprint stays empty or wires one-off presentation.
- **[convention] Blockout before art.** Grey-box geometry in `Maps/Blockouts/` (2.1) is played and
  signed off before anyone dresses it - dressing a layout that then moves is the most expensive rework
  in level production.
- **[convention] Outliner folders by discipline** - Art, Lighting, Gameplay, Audio - in every level.

### 23.4 Source art

- **[convention] Source files live outside `Content/`**, in `SourceArt/` at the project root, in a
  folder path mirroring the asset's: `SourceArt/Characters/Guard/` beside
  `Content/_<Project>/Characters/Guard/`. Layered PSDs, Substance files and DCC scenes are source.
- **[convention] The export carries the asset name** - `SKM_Guard.fbx` imports as `SKM_Guard`, so the
  name is right on import (7.6) and the asset can be traced back to its file.
- **[convention] Source art is under source control** with a binary store and locks (26.1). An asset
  whose source is on one person's machine cannot be fixed when they are away.
- **[convention] Update an asset by re-importing it from its recorded source**, never by deleting it
  and importing again - that drops the asset's settings and breaks every reference to it.

### 23.5 Materials

- **[convention] Master materials are few, and each has an owner.** Day-to-day work is `MI_` instances
  of them; a new master material (`M_`) is reviewed like code. One parent with many instances also
  batches (13.7).
- **[convention] Shared node logic is a Material Function** (`MF_`), never a copied node group.
- **[convention] Parameters are named for what they mean** - PascalCase, `BaseColorTint`,
  `RoughnessScale` - sorted into groups, with slider ranges. A designer must not be able to author a
  value the material does not handle (3.3).
- **[convention] Static switches sparingly** - each one used both ways can double the permutations
  compiled (13.7). Quality Switches carry scalability.
- **[convention] The material model is decided per project** - which shading path, which features -
  and written in the project README before the first master material.
- **[convention] A saved asset is a Material Instance Constant.** A Material Instance Dynamic is
  created in code at runtime and never saved.

### 23.6 Skeletal meshes and animation

- **[convention] One skeleton per rig family**, shared by every mesh and animation on that rig.
  Between families, retarget with an IK Retargeter (`RTG_`) - never duplicate and re-skin animations.
- **[convention] Animations are named rig, action, variant** - `AS_Guard_Walk_Fwd`,
  `AM_Guard_Attack_Heavy` - so a rig's set sorts together.
- **[convention] Root motion is decided per animation set** when it is authored, and is consistent
  within a set - never switched on in the AnimBP to fix a sliding foot.
- **[convention] Notifies are named for the event** - `Footstep`, `WeaponRelease` - and are cosmetic
  triggers only, never state owners (9.4, 19.6).
- **[convention] Compression is set per category and checked in a packaged build.** A hero animation
  is looked at, not left on the default.
- **[convention] One sample rate per project** for exported animation, agreed before the first export.

### 23.7 Design data

- **[convention] Designers tune data, not graphs.** A value a designer changes lives in a DataAsset,
  DataTable, curve or settings class (9.1, 9.6). Opening a Blueprint graph to change a number means a
  data field is missing.
- **[convention] Every table has one source of truth.** Either a spreadsheet exported to a committed
  CSV and imported - the table is never edited in the editor - or the table is edited in the editor
  and there is no spreadsheet. Never both.
- **[convention] Every feature has a test map** - `L_Test_<Feature>` in `Developers/` or `TEMP/` (8.2) -
  that reaches the feature in seconds, not through the game's front door.
- **[convention] A tuning value carries its unit and range** (3.3), and a change to a value players
  have seen says so in its commit message (14.3).

### 23.8 Budgets and review

- **[convention] The project README holds a content budget per category**, beside the frame budget
  (13.2), with a named owner:

  | Category | Triangles (LOD 0) | Largest texture | Material slots | Bones | LODs |
  |---|---|---|---|---|---|
  | Hero character | | | | | |
  | NPC | | | | | |
  | Weapon | | | | | |
  | Small prop | | | | | |
  | Large prop or building | | | | | |

  The numbers belong to the project and its lowest target (13.1); the table exists from the first
  milestone. **[tool]** Texture size and the LOD threshold are enforced already (23.1, 23.2); the rest
  is checked at review.
- **[convention] An asset is reviewed before its first commit:** name and folder (7.1, 2.1),
  Reference Viewer and Size Map (8.3), triangles and textures against the budget, collision and LODs
  (23.2), seen in a level under game lighting - not only in the asset preview.
