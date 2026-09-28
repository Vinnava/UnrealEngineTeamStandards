#pragma once

#include "CoreMinimal.h"
#include "Kismet/GameplayStatics.h"
#include "Subsystems/GameInstanceSubsystem.h"

#include "GameSaveSubsystem.generated.h"

class UGameProgressSaveGame;
class USaveGame;

/** Receives migrated progress, or null when the slot holds nothing this build can use */
DECLARE_DELEGATE_OneParam(FOnGameProgressLoaded, UGameProgressSaveGame*);

/**
 * The only door to saved progress (24.3). Lives for the GameInstance; holds only the set of slots it
 * has refused to overwrite.
 */
UCLASS()
class SAVECHECK_API UGameSaveSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

private:   // Variables
    /** Slot and user index of every save a newer build wrote. Never written to by this build */
    TSet<TTuple<FString, int32>> newerBuildSlots;

private:   // Functions
    /** Game-thread completion of LoadProgressAsync: refuse a newer save, migrate an older one */
    void HandleSlotLoaded(const FString& slotName, int32 userIndex, USaveGame* loadedSave, FOnGameProgressLoaded onLoaded);

public:    // Functions
    /** Reads a slot off the game thread; onLoaded runs on the game thread with migrated progress or null */
    void LoadProgressAsync(const FString& slotName, int32 userIndex, FOnGameProgressLoaded onLoaded);

    /** Writes progress off the game thread. False, and nothing written, for a slot a newer build owns */
    bool SaveProgressAsync(UGameProgressSaveGame* progress, const FString& slotName, int32 userIndex,
        FAsyncSaveGameToSlotDelegate onSaved);
};
