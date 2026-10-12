# 28. Cross-platform, patches and DLC

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

**How a project ships one game on several platforms and stores, and keeps updating it.** Read it when
a project targets more than one platform, and before a release, a patch or a DLC. The project's own
values - targets, device tiers, budgets, commands, store IDs - go in its `CLAUDE.md`, "Cross-platform
rules" (the project template has the block). Every rule carries where its authority comes from:

- **[engine]** - verified in engine source, and re-checked on every upgrade (22.2).
- **[convention]** - common practice, written without a shipped multi-platform project behind it.
- **[unverified]** - engine or store behaviour no project here has run on a device yet. The first
  project to ship on that platform verifies it, as 26.3's rows are verified.

Save data across platforms and cloud services is 24.8; the platform table is 13.1.

---

### 28.1 One mainline, platform code behind interfaces

- **[convention] One mainline for every platform; never a per-platform branch** (26.2). A release
  branch - `release/<milestone>` - only stabilises a build and merges back.
- **[convention] Platform code sits behind a platform-agnostic interface**, and shared gameplay classes
  never branch on a platform. A short difference is a `PLATFORM_*` block inside the implementation.
- **[engine] A longer one is a file in a folder named for its platform** - `Android/`, `IOS/`,
  `Windows/`, or a platform group such as `Apple/` - beside the interface in its role folder (1.3).
  UnrealBuildTool compiles a platform-named folder only for that platform (`GetExcludedFolderNames`).
- **[convention] Console SDK code lives in the project's restricted platform-extension folder,**
  `Platforms/<Platform>/`, under the platform holder's terms. Shared code never includes a console SDK
  header.

### 28.2 Platform services go through the project

- **[convention] Saves, achievements, identity and online, entitlements and haptics each go through a
  project-owned interface or subsystem** (9.12) - `U<Project>SaveSubsystem`, not
  `UGameplayStatics::SaveGameToSlot` from a pawn. Gameplay never calls a platform API or an online
  subsystem directly; one change of store then touches one class.
- **[convention] Store and product IDs live in one DataAsset** keyed by platform - Steam app IDs,
  Epic offer IDs, Google Play and App Store product IDs - never in gameplay code.
- **[convention] Every store ships the same game content.** Store differences live only in the
  service layer.
- **[convention] Never assume the player is online.** A lost connection pauses or degrades the
  feature that needs it, with a message; it never blocks offline play. Online backends are section 21.

### 28.3 Input and UI on every device

- **[convention] Enhanced Input only** (9.13). **Every action has a mapping on every input device the
  project ships on** - keyboard and mouse, gamepad, touch - or a comment in the mapping context saying
  why not. Remapping is 20.4.
- **[convention] CommonUI for every screen, and every screen is fully usable with a gamepad** - focus,
  back and confirm, with no mouse.
- **[engine] Glyphs and key names come from the input data** - `UCommonActionWidget` (12.5), never a
  hard-coded icon or name.
- **[engine] Critical UI sits inside a `USafeZone`.** Nothing a player must read or press sits at a
  screen edge, where a notch, a rounded corner or TV overscan hides it.
- **Player-facing text is `FText`** from `LOCTEXT` or a string table (12.5, 20.8).

### 28.4 Budgets: the lowest tier is the floor

- **[convention] Budgets are written per device-profile tier** in the project's `CLAUDE.md` - frame
  time, memory, draw calls, triangles, texture pool. A budget nobody wrote down is not one (13.2).
- **The most constrained platform is the binding one** (13.1): a change is judged on the lowest tier.
- **No per-frame tick without its one-line reason** (3.7, 3.12); **no synchronous load in gameplay**
  (10.3, 13.5); **no hard reference from a core class to a heavy asset** (3.5) - each one costs most
  on the lowest tier.

### 28.5 One asset, scaled per platform

- **[engine] One source asset per item; the platform difference is a setting on it:** texture LOD
  groups set per device profile (23.1), a per-platform `MinLOD` on the mesh (`FPerPlatformInt`,
  23.2), `Quality Switch` and `Feature Level Switch` nodes in the material, Niagara scalability on
  the effect type, and per-platform audio compression (19.10).
- **[convention] A separate platform asset only when scaling cannot do it,** chosen through a DataAsset
  or a soft reference keyed by platform - never a duplicated folder.
- **[convention] Every material is an instance of a technical-art-owned master material** (23.5), and
  **every master material has a mobile path,** checked in the mobile preview before it is used.
- **[convention] Each content folder has an owner**, recorded in `CLAUDE.md` - technical art owns
  `Art/` and `VFX/` (2.1); programmers own `Core/` and the gameplay Blueprints and data. Prefixes are
  section 7.
- **[engine] Levels two people edit use World Partition with One File Per Actor** (23.3), so each
  person locks only the actors they change.

### 28.6 Config, not code

- **[engine] A platform difference in a value or setting lives in `Config/<Platform>/` files and
  `DefaultDeviceProfiles.ini`** (9.6), never in an `#if` in gameplay code. A difference in behaviour is
  28.1.
- **[convention] The device-profile tiers are listed in `CLAUDE.md`**, and **every change to a device
  profile or a scalability CVar is logged there** with its date and reason - a quiet change moves
  every budget measured against it.
- **[engine] Platform-only content is excluded from other platforms' cooks** through the Asset
  Manager's cook rules and Primary Asset Labels (13.3), never by deleting it on a branch.

### 28.7 Platform lifecycle

- **[engine] Pause on `FCoreDelegates::ApplicationWillDeactivateDelegate`** - a phone call, the sleep
  button - and resume on `ApplicationHasReactivatedDelegate`.
- **[engine] Save on `ApplicationWillEnterBackgroundDelegate`.** The OS may terminate a backgrounded
  app without warning; `GetApplicationWillTerminateDelegate` is not guaranteed on mobile (24.8).
- **[engine] A controller disconnect pauses the game** - bind
  `IPlatformInputDeviceMapper::Get().GetOnInputDeviceConnectionChange()`. In UE 5.7 and 5.8 this is
  not on `FCoreDelegates`.
- **[engine] Free caches on `ApplicationShouldUnloadResourcesDelegate`**, the OS's low-memory warning.
  `GetMemoryTrimDelegate` is not one: it fires during map loads.

### 28.8 Build and verify

- **[convention] The commands that build and cook each active platform are in `CLAUDE.md`**,
  with the project's names and paths, and run as written.
- **[convention] A change to rendering, materials, loading or input is done only when a build of the
  lowest-tier platform runs it.** The editor runs the desktop renderer; it hides mobile failures.
- **[convention] The nightly tier (14.5) cooks every active platform. A broken cook blocks new work**
  until it is fixed - a cook left broken hides the next break.

### 28.9 Versions, patches and DLC

- **[engine] One version, `ProjectVersion` in `DefaultGame.ini`, plus the CI build number** - shown on
  the main menu and written into every save header (24.8) and crash report (14.5). Android's
  `StoreVersion` and iOS's `VersionInfo` move on every store release.
- **[engine] Every shipped build is cooked as a release** - `-createreleaseversion=<version>` - and a
  patch is cooked against it - `-basedonreleaseversion=<version> -generatepatch` - so stores deliver a
  small delta. **The release's cook metadata is kept** in source control or CI storage; without it no
  patch can be made.
- **[engine] Content is chunked through Primary Asset Labels with stable chunk IDs.** A chunk
  reassigned after release moves its content into the next patch.
- **[unverified] The mobile base download fits the store's limit.** Android delivers the rest through
  Play Asset Delivery (`GooglePAD` plugin), any platform through `ChunkDownloader`. `CLAUDE.md` says
  which chunks ship in the base app and which download later.
- **[convention] A minimum-version check forces an update** when online or cloud data needs it, and the
  game refuses incompatible data with a message - never a crash. Mobile releases use staged rollouts.
- **[engine] DLC is a Game Feature plugin cooked into its own chunks.** The base game never
  hard-references DLC content and runs fully with none installed. Ownership is an entitlement check
  through 28.2.
- **[convention] Tunable values are data** - DataAssets, curve tables, config - so a balance fix ships
  as a small data patch, not a code change (9.13, 23.7).
- **[engine] After release, a rename or move keeps the old name working.** 14.3's fix-up removes the
  redirectors, so add a `[CoreRedirects]` `+PackageRedirects=` entry for a moved package and a
  `PrimaryAssetIdRedirects` entry in the Asset Manager settings for a renamed primary asset, with a
  migration note. A save, a patch or a DLC built against the old name otherwise finds nothing.
