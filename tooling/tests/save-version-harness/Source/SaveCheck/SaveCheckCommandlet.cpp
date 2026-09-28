#include "SaveCheckCommandlet.h"

#include "Async/TaskGraphInterfaces.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "HAL/PlatformProcess.h"
#include "HAL/PlatformTime.h"
#include "HarnessPhase.h"
#include "Kismet/GameplayStatics.h"
#include "Containers/Ticker.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"
#include "Save/GameProgressSaveGame.h"
#include "Save/GameSaveSubsystem.h"
#include "Save/GameSaveVersion.h"
#include "UObject/Package.h"
#include "UObject/UObjectGlobals.h"

namespace
{
    int32 failureCount = 0;

    void Check(bool bOk, const FString& what)
    {
        failureCount += bOk ? 0 : 1;
        UE_LOG(LogGameSave, Display, TEXT("SAVECHECK %s %s"), bOk ? TEXT("ok  ") : TEXT("FAIL"), *what);
    }

    bool IsNear(float value, float expected)
    {
        return FMath::IsNearlyEqual(value, expected, 1.e-4f);
    }

    /** A commandlet has no engine loop. The save system delivers async completions through the core
        ticker (ISaveGameSystem::OnAsyncComplete), so nothing arrives unless it is ticked */
    template <typename FDone>
    bool PumpUntil(FDone done)
    {
        const double deadline = FPlatformTime::Seconds() + 10.0;
        while (!done())
        {
            if (FPlatformTime::Seconds() > deadline)
            {
                return false;
            }
            FTaskGraphInterface::Get().ProcessThreadUntilIdle(ENamedThreads::GameThread);
            FTSTicker::GetCoreTicker().Tick(0.005f);
            FPlatformProcess::Sleep(0.005f);
        }
        return true;
    }

    UGameProgressSaveGame* Load(UGameSaveSubsystem* saves, const FString& slot)
    {
        bool bDone = false;
        UGameProgressSaveGame* result = nullptr;
        saves->LoadProgressAsync(slot, 0, FOnGameProgressLoaded::CreateLambda([&](UGameProgressSaveGame* progress)
        {
            result = progress;
            bDone = true;
        }));
        Check(PumpUntil([&] { return bDone; }), FString::Printf(TEXT("load of '%s' completes"), *slot));
        return result;
    }

    bool Save(UGameSaveSubsystem* saves, UGameProgressSaveGame* progress, const FString& slot)
    {
        bool bDone = false;
        bool bWritten = false;
        const bool bAccepted = saves->SaveProgressAsync(progress, slot, 0,
            FAsyncSaveGameToSlotDelegate::CreateLambda([&](const FString&, const int32, bool bSuccess)
            {
                bWritten = bSuccess;
                bDone = true;
            }));
        if (!bAccepted)
        {
            return false;
        }
        Check(PumpUntil([&] { return bDone; }), FString::Printf(TEXT("save of '%s' completes"), *slot));
        return bWritten;
    }

    FString SlotHash(const FString& slot)
    {
        const FString path = FPaths::ProjectSavedDir() / TEXT("SaveGames") / (slot + TEXT(".sav"));
        return LexToString(FMD5Hash::HashFile(*path));
    }

    /** The version Serialize recorded, read before any migration - the loader always migrates */
    int32 RawVersion(const FString& slot)
    {
        const UGameProgressSaveGame* raw = Cast<UGameProgressSaveGame>(UGameplayStatics::LoadGameFromSlot(slot, 0));
        return raw ? raw->GetLoadedSaveVersion() : MIN_int32;
    }

    UGameProgressSaveGame* NewProgress(float health)
    {
        UGameProgressSaveGame* progress = NewObject<UGameProgressSaveGame>(GetTransientPackage());
        progress->health = health;
        return progress;
    }

    // Phase 0: a build from before versioning writes a save, the way a shipped game already has
    void WriteUnversioned()
    {
        UGameProgressSaveGame* progress = NewProgress(75.f);
        progress->unflaggedValue = 7;
        progress->transientValue = 9;
        Check(UGameplayStatics::SaveGameToSlot(progress, TEXT("Unversioned"), 0), "phase 0 writes an unversioned save");

        // Synchronous on purpose: this checks what the engine writes, not the loader
        UGameProgressSaveGame* reread = Cast<UGameProgressSaveGame>(UGameplayStatics::LoadGameFromSlot(TEXT("Unversioned"), 0));
        Check(reread != nullptr, "the unversioned save reads back");
        if (reread)
        {
            Check(reread->unflaggedValue == 7, "SaveGameToSlot writes a property with no SaveGame flag (16.3)");
            Check(reread->transientValue == 0, "SaveGameToSlot never writes a Transient property (16.3)");
        }
    }

    // Phase 1: the scaffolding lands; old saves still load, and new ones carry format 0
    void RunPhase1(UGameSaveSubsystem* saves)
    {
        UGameProgressSaveGame* fresh = NewProgress(75.f);
        Check(fresh->GetLoadedSaveVersion() == 0, "a fresh save reports LatestVersion (0)");
        Check(RawVersion(TEXT("Unversioned")) == -1, "the pre-versioning save reads as -1, not 0 (16.3)");

        UGameProgressSaveGame* old = Load(saves, TEXT("Unversioned"));
        Check(old && IsNear(old->health, 75.f), "the unversioned save loads unchanged in the first versioned build");

        Check(Save(saves, fresh, TEXT("V0")), "phase 1 writes a format-0 save");
    }

    // Phase 2: one version appended; every older save migrates exactly once
    void RunPhase2(UGameSaveSubsystem* saves)
    {
        UGameProgressSaveGame* fresh = NewProgress(0.5f);
        Check(fresh->GetLoadedSaveVersion() == 1, "a fresh save reports the new LatestVersion (1)");
        Check(RawVersion(TEXT("Unversioned")) == -1, "the unversioned save still reads as -1");
        Check(RawVersion(TEXT("V0")) == 0, "the phase 1 save reads as format 0");
        fresh->ApplyMigrations();
        Check(IsNear(fresh->health, 0.5f), "a fresh save is never migrated");

        UGameProgressSaveGame* unversioned = Load(saves, TEXT("Unversioned"));
        Check(unversioned && IsNear(unversioned->health, 0.75f), "the unversioned save (-1) migrates 75 to 0.75");

        UGameProgressSaveGame* v0 = Load(saves, TEXT("V0"));
        Check(v0 && IsNear(v0->health, 0.75f), "the format-0 save migrates 75 to 0.75");
        if (v0)
        {
            v0->ApplyMigrations();
            Check(IsNear(v0->health, 0.75f), "a second ApplyMigrations changes nothing");

            UGameProgressSaveGame* copy = DuplicateObject(v0, GetTransientPackage());
            Check(copy->GetLoadedSaveVersion() == 1, "a duplicate reads as LatestVersion (16.3)");
            copy->ApplyMigrations();
            Check(IsNear(copy->health, 0.75f), "so migrating a duplicate of a migrated save changes nothing");
        }

        // The trap: a copy taken before the loader migrates claims to be current, and never migrates
        UGameProgressSaveGame* raw = Cast<UGameProgressSaveGame>(UGameplayStatics::LoadGameFromSlot(TEXT("V0"), 0));
        if (raw)
        {
            UGameProgressSaveGame* early = DuplicateObject(raw, GetTransientPackage());
            Check(early->GetLoadedSaveVersion() == 1, "a duplicate of an unmigrated format-0 save also claims format 1 (16.3)");
            early->ApplyMigrations();
            Check(IsNear(early->health, 75.f), "so it is never migrated: health stays 75 on a 0-1 scale (16.3)");
        }

        Check(Save(saves, fresh, TEXT("V1")), "phase 2 writes a format-1 save");
        UGameProgressSaveGame* v1 = Load(saves, TEXT("V1"));
        Check(v1 && IsNear(v1->health, 0.5f), "a format-1 save loads unmigrated");
    }

    // Phase 1 again: the build is rolled back, and must not touch the newer save
    void RunRollback(UGameSaveSubsystem* saves)
    {
        const FString before = SlotHash(TEXT("V1"));
        Check(Load(saves, TEXT("V1")) == nullptr, "a rolled-back build refuses the newer save");
        Check(!Save(saves, NewProgress(75.f), TEXT("V1")), "a rolled-back build refuses to overwrite it");
        Check(SlotHash(TEXT("V1")) == before, "the newer save's bytes are unchanged");
    }

    // Mutation 1: the GUID regenerated. The harness expects the damage; seeing it proves the rule
    void RunNewGuid(UGameSaveSubsystem* saves)
    {
        UGameProgressSaveGame* v1 = Load(saves, TEXT("V1"));
        Check(v1 && IsNear(v1->health, 0.005f),
            "with a new GUID a migrated save reads as -1 and migrates again: 0.5 became 0.005 (24.5)");
    }

}

int32 USaveCheckCommandlet::Main(const FString& params)
{
    FString step;
    FParse::Value(*params, TEXT("step="), step);
    UE_LOG(LogGameSave, Display, TEXT("SAVECHECK step '%s', phase %d, mutation %d, LatestVersion %d"), *step,
        SAVE_CHECK_PHASE, SAVE_CHECK_MUTATION, static_cast<int32>(FGameSaveVersion::LatestVersion));

    // A commandlet has no running GameInstance. The subsystem must be created inside one, but none of
    // its functions use it, so an uninitialised instance is enough
    UGameInstance* gameInstance = NewObject<UGameInstance>(GEngine);
    UGameSaveSubsystem* saves = NewObject<UGameSaveSubsystem>(gameInstance);

    if (step == TEXT("unversioned"))
    {
        WriteUnversioned();
    }
    else if (step == TEXT("phase1"))
    {
        RunPhase1(saves);
    }
    else if (step == TEXT("phase2"))
    {
        RunPhase2(saves);
    }
    else if (step == TEXT("rollback"))
    {
        RunRollback(saves);
    }
    else if (step == TEXT("newguid"))
    {
        RunNewGuid(saves);
    }
    else if (step == TEXT("skipusing"))
    {
        // Expected to die in the engine's check before this returns
        Save(saves, NewProgress(0.5f), TEXT("SkipUsing"));
    }
    else
    {
        Check(false, FString::Printf(TEXT("known step '%s'"), *step));
    }

    UE_LOG(LogGameSave, Display, TEXT("SAVECHECK done, %d failure(s)"), failureCount);
    return failureCount == 0 ? 0 : 1;
}
