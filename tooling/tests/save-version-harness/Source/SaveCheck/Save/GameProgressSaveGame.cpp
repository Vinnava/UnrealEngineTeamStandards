#include "Save/GameProgressSaveGame.h"

#include "HarnessPhase.h"
#include "Logging/StructuredLog.h"
#include "Save/GameSaveVersion.h"
#include "Serialization/Archive.h"

namespace
{
    /** Saves before HealthIsFraction stored health on this scale */
    constexpr float LegacyHealthScale = 100.f;
}

UGameProgressSaveGame::UGameProgressSaveGame()
{
    // A fresh save is already current, so nothing migrates it
    loadedSaveVersion = FGameSaveVersion::LatestVersion;
#if SAVE_CHECK_PHASE >= 2
    health = 1.f;
#else
    health = LegacyHealthScale;
#endif
    unflaggedValue = 0;
    transientValue = 0;
}

void UGameProgressSaveGame::Serialize(FArchive& ar)
{
#if SAVE_CHECK_PHASE >= 1
#if SAVE_CHECK_MUTATION == 2
    // Mutation: the 24.3 raw-archive pattern with UsingCustomVersion forgotten
    const int32 dataVersion = ar.CustomVer(FGameSaveVersion::GUID);
    UE_LOGFMT(LogGameSave, Log, "[{Obj}] [Serialize] Read version {Version} without UsingCustomVersion",
        GetNameSafe(this), dataVersion);
#else
    // Required before any CustomVer on a save, which otherwise fails a check (16.3)
    ar.UsingCustomVersion(FGameSaveVersion::GUID);
#endif
#endif

    Super::Serialize(ar);

#if SAVE_CHECK_PHASE >= 1
    if (!ar.IsLoading())
    {
        return;
    }

    // Record only - migrations run from the loader, after it has refused a newer save (24.5)
    loadedSaveVersion = ar.CustomVer(FGameSaveVersion::GUID);
#endif
}

void UGameProgressSaveGame::ApplyMigrations()
{
    if (IsFromNewerBuild())
    {
        UE_LOGFMT(LogGameSave, Error, "[{Obj}] [ApplyMigrations] Save format {Loaded} is newer than this build's {Latest}, refused",
            GetNameSafe(this), loadedSaveVersion, static_cast<int32>(FGameSaveVersion::LatestVersion));
        return;
    }

    if (loadedSaveVersion >= FGameSaveVersion::LatestVersion)
    {
        return;
    }

    const int32 fromVersion = loadedSaveVersion;

    // Oldest first: each step may assume every step above it has run
#if SAVE_CHECK_PHASE >= 2
    if (loadedSaveVersion < FGameSaveVersion::HealthIsFraction)
    {
        MigrateHealthIsFraction();
    }
#endif

    // Current now, so a second call is a no-op
    loadedSaveVersion = FGameSaveVersion::LatestVersion;

    UE_LOGFMT(LogGameSave, Log, "[{Obj}] [ApplyMigrations] Migrated save from format {From} to {To}",
        GetNameSafe(this), fromVersion, loadedSaveVersion);
}

void UGameProgressSaveGame::MigrateHealthIsFraction()
{
    health = health / LegacyHealthScale;

    UE_CLOGFMT(health < 0.f || health > 1.f, LogGameSave, Warning,
        "[{Obj}] [MigrateHealthIsFraction] Health {Health} is outside 0-1 after migration, kept as read",
        GetNameSafe(this), health);
}

bool UGameProgressSaveGame::IsFromNewerBuild() const
{
    return loadedSaveVersion > FGameSaveVersion::LatestVersion;
}

int32 UGameProgressSaveGame::GetLoadedSaveVersion() const
{
    return loadedSaveVersion;
}
