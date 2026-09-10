# 7-8. Content naming and Blueprint discipline

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

---

## 7. Blueprint and content naming conventions

### 7.1 Asset prefixes

**Every asset carries a type prefix.** No exceptions, including temporary and test assets.

| Prefix | Asset type | Example |
|---|---|---|
| `BP_` | Blueprint class | `BP_AvatarCharacter`, `BP_PressurePlate` |
| `WBP_` | Widget Blueprint | `WBP_InventoryGrid`, `WBP_MainMenu` |
| `ABP_` | Animation Blueprint | `ABP_PlayerCharacter` |
| `DA_` | Data Asset | `DA_TutorialSequence`, `DA_Hair_1_Female` |
| `DT_` | Data Table | `DT_NPCDialogue`, `DT_ItemDefinitions` |
| `L_` | Level / map | `L_MainHub`, `L_SplashMap` |
| `SM_` | Static Mesh | `SM_TeaTable` |
| `SKM_` | Skeletal Mesh | `SKM_PlayerBody` |
| `SK_` | Skeleton | `SK_PlayerSkeleton` |
| `PHYS_` | Physics Asset | `PHYS_PlayerBody` |
| `M_` | Material | `M_Wood` |
| `MI_` | Material Instance | `MI_Wood_Dark` |
| `MF_` | Material Function | `MF_WorldAlignedUV` |
| `MPC_` | Material Parameter Collection | `MPC_TimeOfDay` |
| `T_` | Texture | `T_UIIcon_Home` |
| `RT_` | Render Target | `RT_MirrorCapture` |
| `AS_` | Anim Sequence | `AS_PickupHandover` |
| `AM_` | Anim Montage | `AM_Player_SitToStand` |
| `BS_` | Blend Space | `BS_Idle_Walk_Run` |
| `AO_` | Aim Offset | `AO_RifleAim` |
| `IA_` | Input Action | `IA_Interact`, `IA_Move` |
| `IMC_` | Input Mapping Context | `IMC_Default`, `IMC_Vehicle` |
| `NS_` | Niagara System | `NS_Sparks` |
| `NE_` | Niagara Emitter | `NE_Embers` |
| `SC_` | Sound Cue | `SC_FootstepStone` |
| `SW_` | Sound Wave | `SW_Ambience_Forest` |
| `LS_` | Level Sequence | `LS_OpeningCinematic` |
| `HDRI_` | HDRI backdrop | `HDRI_Overcast` |
| `E_` | Blueprint Enum | `E_ContactTab` |
| `F_` | Blueprint Struct | `F_LoadoutData` |
| `BB_` | Blackboard | `BB_Guard` |
| `BT_` | Behavior Tree | `BT_Guard` |
| `ST_` | State Tree | `ST_GuardPatrol` |
| `BPI_` | Blueprint Interface | `BPI_Interactable` |
| `BFL_` | Blueprint Function Library | `BFL_InventoryUtils` |
| `BPC_` | Blueprint Actor Component | `BPC_Inventory`, `BPC_Health` |
| `PM_` | Physical Material | `PM_Metal`, `PM_Grass` |
| `ATT_` | Sound Attenuation | `ATT_Footsteps` |
| `SCL_` | Sound Class | `SCL_Music`, `SCL_SFX` |
| `MSS_` | MetaSound Source | `MSS_Explosion` |
| `MSP_` | MetaSound Patch | `MSP_RandomPitch` |
| `CR_` | Control Rig | `CR_Mannequin` |
| `IK_` | IK Rig | `IK_Mannequin` |
| `RTG_` | IK Retargeter | `RTG_MannyToPlayer` |
| `CF_` | Curve Float | `CF_DamageFalloff` |
| `CV_` | Curve Vector | `CV_CameraShake` |
| `CLC_` | Curve Linear Color | `CLC_SkyTint` |
| `CT_` | Curve Table | `CT_XPPerLevel` |
| `GE_` | Gameplay Effect (GAS) | `GE_Damage_Fire` |
| `GA_` | Gameplay Ability (GAS) | `GA_Dash` |

**One prefix per type, never a choice of two.** Blueprint structs are `F_`, matching the C++ `F`
prefix - not `S_`.

### 7.2 Blueprint role infixes

Core-framework Blueprints carry a second segment naming their role:

| Infix | Role | Examples |
|---|---|---|
| `BP_GM_` | GameMode | `BP_GM_Main`, `BP_GM_Onboarding` |
| `BP_GS_` | GameState | `BP_GS_Main` |
| `BP_PC_` | PlayerController | `BP_PC_Player` |
| `BP_PS_` | PlayerState | `BP_PS_Player` |
| `BP_GI_` | GameInstance | `BP_GI_Main` |
| `BP_CH_` | Character | `BP_CH_Player`, `BP_CH_NPCGuard` |
| `BP_AIC_` | AI Controller | `BP_AIC_Guard` |

Everything else is simply `BP_<Thing>`: `BP_PortalTrigger`, `BP_Wardrobe`, `BP_ApartmentDoor`.

### 7.3 Naming the rest of the name

- **PascalCase after the prefix.** `SM_TeaTable`, not `SM_teatable` or `SM_tea_table`.
- **Underscores separate meaningful segments only** - variant, gender, index, LOD:
  `DA_Hair_1_Female`, `MI_Wood_Dark`, `BS_Idle_Walk_Run_Guard`.
- **No spaces, ever.**
- **No trailing duplication numbers.** `_1` and `_2` mean a chosen variant, never a duplicate.
- **Spell it correctly, and the same way every time.**
- **Never ship a vendor, tool or scratch name.** Rename on import - `ChatGPT_image_3`, `Icosphere`,
  `Retopo_final`, `test_`, `yy_`, `Wood058` do not belong in a shipping tree.
- **Suffix by variant, not by history.** No `_Final`, `_v2`, `_New`, `_Old`, `_Fixed`, `_Copy`,
  `_Backup`.

### 7.4 Naming inside a Blueprint

**Blueprint follows the C++ conventions.**

| Concept | Convention | Example |
|---|---|---|
| Variables | `camelCase` | `currentSpeed`, `activeContact` |
| Booleans | `b` prefix | `bIsOpen`, `bHasPlayed` |
| Functions and custom events | `PascalCase`, verb-first (4.3) | `OpenPanel`, `HandleCallEnded` |
| Function parameters | `camelCase` | `contactId`, `newIndex` |
| Local variables | `camelCase` | `tempIndex` |
| Macros | `PascalCase` | `IsValidTarget` |
| Event Dispatchers | `On` + PascalCase | `OnPanelChanged`, `OnInventoryUpdated` |
| Components in a Blueprint | `camelCase` + role suffix | `movementComp`, `widgetComp`, `collisionBox` |
| Timelines | `PascalCase` + `Timeline` | `FadeInTimeline` |
| Widget bind names | `<role>_<Type>` | `back_Btn`, `chat_ScrollBox`, `title_Text`, `background_Img` |
| Categories | Mirror the C++ hierarchy | `Initialize\|Movement` |

- **Widget bind names are load-bearing.** `meta = (BindWidget)` matches on **object name**,
  case-insensitively, and is a hard compile requirement (12.1).
- **The bind name is also the C++ member name** - a deliberate exception to 4.1:
  `TObjectPtr<UButton> back_Btn;`. The only member-variable name with an underscore. One form
  everywhere: camelCase role, PascalCase type.
- Common widget type suffixes: `_Btn`, `_Text`, `_Img`, `_ScrollBox`, `_Switcher`, `_SizeBox`,
  `_Panel`, `_Bar`, `_Box`, `_Slot`.

### 7.5 Folder naming

- **PascalCase folder names.** `Characters`, `LevelPrototyping`, `SubLevels`.
- **No spaces, no abbreviations you would not use in code.**
- Folder depth mirrors ownership (1.3).
- **Do not create a folder for one asset.** Create it at three.

### 7.6 Existing content

- **Get the name right on import.** It is the only cheap moment.
- **Inherited non-compliant content:** new assets follow this standard with no exceptions; existing
  assets are **not** renamed opportunistically. Batch renames are a planned task, agreed with whoever
  owns that content, done in one commit.

---

## 8. Blueprint discipline

### 8.1 The C++/Blueprint boundary

> **C++ owns core systems, interfaces and data shape. Blueprint inherits from C++ and owns game
> logic and presentation.**

- **System architecture in Blueprint is never acceptable.**
- The gameplay half is the default split. A C++-first project may keep gameplay flow in C++ and
  record that as a project override (README). No project chooses per feature.

| Belongs in C++ | Belongs in Blueprint |
|---|---|
| Subsystems and services | Per-actor gameplay logic |
| Interfaces and data shape | Visual and audio response |
| Save/load | Animation hookups |
| Networking and HTTP | Widget layout and bindings |
| Anything performance-critical or ticking | Designer-tunable behaviour |
| Anything two systems must agree on | One-off scripted moments |

- Use `BlueprintImplementableEvent` (C++ declares, BP implements) or `BlueprintNativeEvent` (C++
  default, BP may override) when Blueprint responds to a C++ event.
- **The drift diagnostic: a Blueprint branching on a game rule.** Rules are C++. Tuning is data.
  Composition, look and feel are Blueprint.
- **Call a `BlueprintNativeEvent` by its plain name** from C++, never `Foo_Implementation`.
- **`BlueprintPure` only for trivial, side-effect-free functions** - a pure node re-runs for every pin
  that reads it.
- **Shared logic that changes often belongs in C++** - a `.uasset` cannot merge.
- **The test:** a new enemy type is one DataAsset, one Blueprint and zero compiles.

### 8.2 Prototyping, testing and temporary work

Blueprint is the right tool for trying something out. 8.1 governs what *ships*. Use it freely for:

- **Prototyping a mechanic** before you know its final shape.
- **Test harnesses** - a `BP_` actor that spawns the state you need or drives a system directly.
- **Debug and cheat actors** - skip a sequence, grant an item, teleport the player.
- **Blocking out a scripted moment** before it becomes a data-driven step.

Rules:

- **Name it as temporary.** Prefix `BP_TEMP_` / `WBP_TEMP_`, or keep it in `TEMP/` or `Developers/`.
- **Keep it out of shipping paths.** No shipping asset references a temp Blueprint; if one does,
  promote it properly or cut the reference.
- **Port or delete before feature sign-off.** A prototype becomes a C++ implementation or is deleted.
- **No temp Blueprint built on another temp Blueprint.**
- **The naming rules still apply** (section 7).
- **Debug and cheat actors may stay indefinitely** - same naming and hygiene rules, kept out of the
  shipping cook, anything player-visible gated behind a build configuration check.

### 8.3 Graph hygiene

- **Comment boxes on every graph section.**
- **Every variable gets a tooltip and a category**, like a `UPROPERTY`.
- **Reroute nodes over crossing wires.**
- **Collapse to functions** rather than growing the Event Graph. More than a handful of nodes in
  `Event Tick` means the logic belongs in C++.
- **No orphan or disconnected nodes.**
- **No `Cast To` in Tick.** Cache the result once.
- **`Cast To BP_X` is a hard reference** that loads `BP_X` and everything it references. Cast to the
  C++ base class, or call through an interface (9.7).
- **Blueprint is for events, not loops.** A loop over many items per frame belongs in C++.
- **No `Get All Actors Of Class` outside one-time initialisation** - never in Tick, never per event.
  Cache the result, or have the actors register themselves.
- **No hard references to heavy assets** in a widely-instanced Blueprint. Soft-reference and load on
  demand.
- **Check the Reference Viewer and Size Map** before committing a Blueprint that references content.

### 8.4 Blueprint nativization is not a plan

Do not write heavy logic in Blueprint expecting to nativize or port it later. Port it when you write
it, or accept the cost permanently.
