#pragma once

#include "CoreMinimal.h"

#include "HarnessPhase.h"

SAVECHECK_API DECLARE_LOG_CATEGORY_EXTERN(LogGameSave, Log, All);

/** Format history of the saved progress. Append-only from the first external build (24.1) */
struct SAVECHECK_API FGameSaveVersion
{
    // A plain enum inside a struct, not an enum class: archives report versions as int32 (4.5)
    enum Type
    {
        /** Before versioning. A save from then reads as -1, never as this value (16.3) */
        BeforeCustomVersionWasAdded = 0,

#if SAVE_CHECK_PHASE >= 2
        /** 1.1: health is a 0-1 fraction; it was 0-100 */
        HealthIsFraction,
#endif

        // Add new entries above this line - never reorder, remove or insert (24.5)

        /** One past the newest entry. Never compared against */
        VersionPlusOne,

        /** The newest format. Moves by itself when an entry is appended */
        LatestVersion = VersionPlusOne - 1
    };

    /** Keys this version stream in every save header. Never changes once a save has shipped (24.5) */
    static const FGuid GUID;
};
