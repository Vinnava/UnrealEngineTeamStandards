# 24. Save data and versioning

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

**This section applies if anything the game writes outlives a session on the player's device** - a
save game, a settings save, a custom binary cache. Progress kept only on a backend is section 21.
9.14 is the always-loaded summary; this is the procedure behind it.

Every rule here was run, not just read: [`tooling/tests/save-version-harness/`](../tooling/tests/save-version-harness/)
builds one game four times over, loads each build's saves in the next, and builds two of the
mistakes in 24.5 on purpose to show the damage each one does.

---

### 24.1 When the contract starts

> **The version enum is append-only from the first build a player outside the team runs.**

| Phase | What you do |
|---|---|
| **The save system is first built** | Add the 24.3 scaffolding. The enum holds only `BeforeCustomVersionWasAdded` |
| **Internal development** | Change the format freely. Wipe local saves; write no migrations |
| **First external build** - playtest, demo, beta | **The contract starts.** From here the enum is append-only, every format change lands with its migration in the same commit, and a save from the build goes into the fixtures (24.6) |
| **Before launch** | If beta saves carry into launch, keep the enum. If they are wiped, the enum may be reset - **with a new GUID**, never the old one |
| **After launch** | The enum is permanent history. Append only; never reset, never change the GUID |

- **"External" means any build that leaves the team** - a playtest, a publisher drop, a store beta.
  Its saves are on machines you cannot wipe.
- **The team is told the day the contract starts**, in the same message as the build.

### 24.2 When to bump the version

| Change | Bump? | How it loads |
|---|---|---|
| Add a `UPROPERTY` | No | Absent from old saves, so it keeps its constructor default |
| Remove a `UPROPERTY` | No | The old tag is skipped |
| Widen a number, same meaning (`int32` to `int64`) | No | Tagged serialisation converts it |
| Rename a `UPROPERTY` | No | A Core Redirect, in the same commit (3.8) |
| Change to a type the engine cannot convert (`TArray<FName>` to `FGameplayTagContainer`) | **Yes** | Keep the old property, migrate, then clear it |
| Same type, new meaning (0-100 to 0-1) | **Yes** | Transform the value in a migration |
| Split, merge or restructure fields | **Yes** | Rebuild the new fields from the old |
| Any change to a raw `ar << x` - order, count or type | **Yes** | Branch the read on the version |

**The test:** if a save from the previous external build loads correctly with no new code, do not
bump. If it loads wrong or loses data, bump and migrate.

### 24.3 The scaffolding

`Game` stands in for `<Project>` (00-core). The complete, compiled version is in
[`tooling/tests/save-version-harness/Source/SaveCheck/Save/`](../tooling/tests/save-version-harness/Source/SaveCheck/Save/):
copy it from there, then delete the `SAVE_CHECK_` lines and the members marked "Harness only".

**The version.** One stream per save format, in `Save/GameSaveVersion.h`:

```cpp
/** Format history of the saved progress. Append-only from the first external build (24.1) */
struct GAME_API FGameSaveVersion
{
    // A plain enum inside a struct, not an enum class: archives report versions as int32 (4.5)
    enum Type
    {
        /** Before versioning. A save from then reads as -1, never as this value (16.3) */
        BeforeCustomVersionWasAdded = 0,

        // Add new entries above this line - never reorder, remove or insert (24.5)

        /** One past the newest entry. Never compared against */
        VersionPlusOne,

        /** The newest format. Moves by itself when an entry is appended */
        LatestVersion = VersionPlusOne - 1
    };

    /** Keys this version stream in every save header. Never changes once a save has shipped (24.5) */
    static const FGuid GUID;
};
```

```cpp
// GameSaveVersion.cpp - generated once (Visual Studio: Tools > Create GUID), never copied
const FGuid FGameSaveVersion::GUID(0x00000000, 0x00000000, 0x00000000, 0x00000000);

// Registered at module load, so every save header records LatestVersion
const FCustomVersionRegistration GRegisterGameSaveVersion(
    FGameSaveVersion::GUID, FGameSaveVersion::LatestVersion, TEXT("GameSaveVersion"));
```

**The save object** records the version it was read from, and migrates only when asked:

```cpp
UGameProgressSaveGame::UGameProgressSaveGame()
{
    // A fresh save is already current, so nothing migrates it
    loadedSaveVersion = FGameSaveVersion::LatestVersion;
}

void UGameProgressSaveGame::Serialize(FArchive& ar)
{
    // Required before any CustomVer on a save, which otherwise fails a check (16.3)
    ar.UsingCustomVersion(FGameSaveVersion::GUID);

    Super::Serialize(ar);

    if (!ar.IsLoading())
    {
        return;
    }

    // Record only - migrations run from the loader, after it has refused a newer save (24.5)
    loadedSaveVersion = ar.CustomVer(FGameSaveVersion::GUID);
}

void UGameProgressSaveGame::ApplyMigrations()
{
    if (IsFromNewerBuild() || loadedSaveVersion >= FGameSaveVersion::LatestVersion)
    {
        return;
    }

    // Oldest first: each step may assume every step above it has run
    if (loadedSaveVersion < FGameSaveVersion::HealthIsFraction)
    {
        MigrateHealthIsFraction();
    }

    // Current now, so a second call is a no-op
    loadedSaveVersion = FGameSaveVersion::LatestVersion;
}
```

`IsFromNewerBuild()` is `loadedSaveVersion > FGameSaveVersion::LatestVersion`. `loadedSaveVersion` is
a plain member, not a `UPROPERTY` - it describes the file, so it is never written into one.

**The loader** is one `UGameInstanceSubsystem`, the only code that calls the `SaveGame` functions in
`UGameplayStatics`. It loads with `AsyncLoadGameFromSlot` and saves with `AsyncSaveGameToSlot` (9.14),
and on every load:

1. **Casts, and hands back null** for a missing or unreadable slot.
2. **Refuses a save from a newer build** - hands back null, and remembers the slot so a later save
   from this build cannot overwrite it. A rolled-back build that overwrites a newer save destroys the
   player's progress.
3. **Calls `ApplyMigrations`**, then hands the save out. Nothing else ever sees an unmigrated save -
   a copy taken before this point claims to be current and is never migrated (16.3).

**A raw `Serialize`** - a struct or a custom binary format - branches every read on the version:

```cpp
void FGameExampleData::Serialize(FArchive& ar)
{
    ar.UsingCustomVersion(FGameSaveVersion::GUID);

    ar << existingField;

    // Written from AddedNewField on; older data keeps the constructor default
    if (ar.CustomVer(FGameSaveVersion::GUID) >= FGameSaveVersion::AddedNewField)
    {
        ar << newField;
    }
}
```

### 24.4 Adding a version

1. **Confirm the change needs one** (24.2).
2. **Append one entry** directly above the marker line. Its doc comment is the changelog: the build
   it ships in, and what changed - `/** 1.3: health is a 0-1 fraction; it was 0-100 */`.
3. **Keep the old data readable.** A tagged property keeps its **original name**, commented as
   legacy - a renamed legacy property no longer matches the tag in the file, and loads as its
   default. A raw read keeps its old branch behind `if (version < NewEntry)`.
4. **Write one private migration function** per entry - `MigrateHealthIsFraction()` - and call it
   from `ApplyMigrations` in enum order.
5. **Log every recoverable oddity as `Warning` and every item it cannot map as `Error`** (6.3), and
   keep the unmapped data rather than deleting it.
6. **Load every fixture** (24.6) before the commit.

### 24.5 Always and never

**Always:**

- **`UsingCustomVersion` before `CustomVer`** in every `Serialize` that reads the version.
- **Migrations oldest to newest**, each safe to run twice or guarded so it cannot.
- **Named constants for every conversion factor** (3.1's no-magic-numbers rule).
- **A newer build's save is refused and never overwritten.**
- **Keep data a migration could not map.** A later build may be able to.

**Never:**

- **Reorder, remove or insert an entry.** The number *is* the format; moving one re-labels every save.
- **Change the GUID once a supported save exists.** Every existing save then reads as -1, so every
  migration runs again on data that was already migrated - the harness shows 0.5 becoming 0.005.
- **Share a GUID** between projects, between branches that version independently, or between
  unrelated formats.
- **Migrate inside `Serialize`.** Migrations run in one place, the loader, after it has refused a
  newer build's save - so each can be tested on its own, and none runs on a save this build must not
  touch.
- **Remove a legacy property** while any supported save can still hold it.
- **Bump for a change tagged serialisation already handles** (24.2).

**Branches:** only one branch at a time appends to a version enum, or each independently versioned
branch has its own GUID. An enum merge conflict keeps the shipped order and renumbers only entries
that have not shipped.

### 24.6 Fixtures and tests

- **`SaveFixtures/` holds one save from every external build**, committed, named for the build.
- **An automation test loads every fixture, migrates it, and asserts the values that matter** - run
  in the every-commit tier (14.5). A migration never run against a real old save is a hypothesis.
- **The test also asserts** that `ApplyMigrations` twice equals once, and that a fresh save reports
  `LatestVersion` and is never migrated.
- **A test that drives the async loader ticks `FTSTicker::GetCoreTicker()`.** The save system
  delivers its completions through that ticker, so a test without an engine loop - a commandlet, a
  bare automation test - otherwise waits forever.
- **Before each external build, by hand:** a save from it loads in the *previous* build and is
  refused, not overwritten. On mobile, run the update-then-roll-back path on one device per platform.

### 24.7 When a save loads wrong

| Symptom | Likely cause |
|---|---|
| Assert in `CustomVer` while saving | `UsingCustomVersion` not called first (16.3) |
| Values halved, doubled or otherwise re-transformed | A migration ran twice - the GUID changed (24.5), or a non-idempotent step was called from two places |
| A copy of a save never migrates | It was duplicated before the loader migrated it (16.3) |
| A migration runs on a fresh save | The constructor does not set the loaded version to `LatestVersion` |
| An old field loads as its default instead of migrating | The legacy property was renamed, so the tag in the file no longer matches |
| A field that should not persist comes back after a load | It is a `UPROPERTY` without `Transient` - `SaveGameToSlot` ignores the `SaveGame` flag (16.3) |
| The new build is fine; the old build corrupts the save | The loader does not refuse, or later overwrites, a newer build's save |
| Data misaligned after a raw binary change | The read order no longer matches the write order for that version |
