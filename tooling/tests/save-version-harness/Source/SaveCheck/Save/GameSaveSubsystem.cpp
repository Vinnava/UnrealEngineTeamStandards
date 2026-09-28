#include "Save/GameSaveSubsystem.h"

#include "Logging/StructuredLog.h"
#include "Save/GameProgressSaveGame.h"
#include "Save/GameSaveVersion.h"

void UGameSaveSubsystem::LoadProgressAsync(const FString& slotName, int32 userIndex, FOnGameProgressLoaded onLoaded)
{
    UGameplayStatics::AsyncLoadGameFromSlot(slotName, userIndex,
        FAsyncLoadGameFromSlotDelegate::CreateUObject(this, &UGameSaveSubsystem::HandleSlotLoaded, onLoaded));
}

void UGameSaveSubsystem::HandleSlotLoaded(const FString& slotName, int32 userIndex, USaveGame* loadedSave,
    FOnGameProgressLoaded onLoaded)
{
    UGameProgressSaveGame* progress = Cast<UGameProgressSaveGame>(loadedSave);
    if (!progress)
    {
        UE_LOGFMT(LogGameSave, Log, "[{Obj}] [HandleSlotLoaded] Slot '{Slot}' is missing, unreadable or not progress",
            GetNameSafe(this), slotName);
        onLoaded.ExecuteIfBound(nullptr);
        return;
    }

    // A rolled-back build must never use, or later overwrite, progress it cannot read
    if (progress->IsFromNewerBuild())
    {
        newerBuildSlots.Add(MakeTuple(slotName, userIndex));
        UE_LOGFMT(LogGameSave, Error, "[{Obj}] [HandleSlotLoaded] Slot '{Slot}' was saved by a newer build (format {Version}), refused",
            GetNameSafe(this), slotName, progress->GetLoadedSaveVersion());
        onLoaded.ExecuteIfBound(nullptr);
        return;
    }

    progress->ApplyMigrations();
    onLoaded.ExecuteIfBound(progress);
}

bool UGameSaveSubsystem::SaveProgressAsync(UGameProgressSaveGame* progress, const FString& slotName, int32 userIndex,
    FAsyncSaveGameToSlotDelegate onSaved)
{
    if (!IsValid(progress))
    {
        UE_LOGFMT(LogGameSave, Error, "[{Obj}] [SaveProgressAsync] Progress is null, slot '{Slot}' not written",
            GetNameSafe(this), slotName);
        return false;
    }

    if (newerBuildSlots.Contains(MakeTuple(slotName, userIndex)))
    {
        UE_LOGFMT(LogGameSave, Error, "[{Obj}] [SaveProgressAsync] Slot '{Slot}' holds a newer build's save, not overwritten",
            GetNameSafe(this), slotName);
        return false;
    }

    UGameplayStatics::AsyncSaveGameToSlot(progress, slotName, userIndex, onSaved);
    return true;
}
