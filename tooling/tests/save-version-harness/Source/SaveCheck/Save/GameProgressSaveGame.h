#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"

#include "GameProgressSaveGame.generated.h"

/**
 * The player's saved progress. Only UGameSaveSubsystem hands one out, and always migrated (24.3).
 */
UCLASS()
class SAVECHECK_API UGameProgressSaveGame : public USaveGame
{
    GENERATED_BODY()

private:   // Variables
    /** Format this object was read from; -1 predates versioning. Not a UPROPERTY, so never saved */
    int32 loadedSaveVersion;

public:    // Variables
    /** Remaining health, a 0-1 fraction since HealthIsFraction - 0-100 in older saves */
    UPROPERTY()
    float health;

    /** Harness only: carries no SaveGame flag, to prove SaveGameToSlot writes it anyway (16.3) */
    UPROPERTY()
    int32 unflaggedValue;

    /** Harness only: proves a Transient property never reaches a slot (16.3) */
    UPROPERTY(Transient)
    int32 transientValue;

private:   // Functions
    /** HealthIsFraction: 0-100 health becomes a 0-1 fraction */
    void MigrateHealthIsFraction();

public:    // Functions
    UGameProgressSaveGame();

    /** Records the format a load came from. Never migrates - the loader does (24.5) */
    virtual void Serialize(FArchive& ar) override;

    /** Brings a loaded save up to LatestVersion. A second call does nothing; a newer save is refused */
    void ApplyMigrations();

    /** True for a save written by a newer build, which this build must never use or overwrite */
    bool IsFromNewerBuild() const;

    int32 GetLoadedSaveVersion() const;
};
