# 23. Content pipeline

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

**This is the engine-grounded, checkable core of the content rules, not the whole of them.** Every
rule here is either verified in engine source or enforced by `AssetContentValidator`. The art lead and
the design lead own extending it from their own workflows during the pilot ([PILOT.md](../PILOT.md)) -
a programmer's guess at an artist's pipeline is exactly the gap this section is meant to close, not
fill. Naming is 7.1; performance budgets are 13.4 and 13.7.

Rules marked **[tool]** fail the build through `AssetContentValidator` (18.2).

---

### 23.1 Textures

- **[tool] Powers of two, or padded.** A non-power-of-two texture never streams: `UTexture::IsPossibleToStream`
  refuses it at runtime, so it sits in memory at full resolution the whole time it is loaded (16.8).
  Author power-of-two sizes, or set **Power Of Two Mode** to pad. UI textures are exempt - the UI
  texture group never streams anyway - as is a texture deliberately marked **Never Stream**.
- **[tool] Stay under the size budget.** A texture without virtual texturing is at most the project's
  `maxTextureSize` on its longest side - 4096 unless the project's `DefaultEditor.ini` says otherwise.
  Going over needs virtual texturing, or a budget change recorded in the project README (13.2).
- **Set the texture group** (`LODGroup`) for the texture's category. The group is how streaming,
  mip bias and per-platform limits apply to a whole category at once; a texture left in the default
  group escapes every one of them. UI textures use the UI group (13.4).
- **Compression follows the content.** Normal maps use **Normalmap** (BC5). Packed masks - an ORM,
  a roughness or metal mask - use **Masks**, which is the no-sRGB setting. Colour stays **Default**,
  with sRGB on. A mask read as sRGB is subtly wrong on every surface that samples it, and nothing
  reports it.
- **Nothing player-readable is baked into a texture** (20.5).

### 23.2 Meshes

- **Author at real-world scale: one Unreal unit is one centimetre.** Physics assumes it - the engine's
  default gravity is `-980` (`BaseEngine.ini`), which is Earth's in centimetres per second squared.
  A mesh at the wrong scale falls, collides and sounds wrong at once.
- **The pivot is where the mesh is placed or turned** - the base of a prop, the hinge of a door - so
  it snaps and rotates without an offset.
- **[tool] A non-Nanite mesh above the triangle threshold carries LODs.** The threshold is the
  project's `lodTriangleThreshold`, 1000 unless configured. A reduction **LOD Group** on the mesh is
  enough; hand-authored LODs are better where silhouette matters. Nanite meshes build their own and
  need none (13.7).
- **Anything a player or physics touches has simple collision** - authored `UCX_` hulls or generated
  shapes. **Complex-as-simple** is a per-asset decision for static geometry that genuinely needs exact
  collision, never a default; and a trace against complex collision can miss in a cooked build where
  it was not cooked (16.7).

### 23.3 Levels

- **Code finds a placed actor by tag, GameplayTag or soft reference - never by its label or name.**
  An actor's label is editor-only data and does not exist in a cooked build (16.3).
- **Large and open levels use World Partition.** Converting a level to World Partition turns on One
  File Per Actor - each actor saved to its own file - which ends level merge conflicts and multiplies
  file count (14.3).
- **Content that switches on and off - a quest stage, a time of day - is a Data Layer** in a World
  Partition level, not a second copy of the map. A duplicated map is two maps that drift.
- **Streaming is asynchronous** (16.5): code that depends on a streamed region binds to its loaded
  event and never waits a fixed time.
