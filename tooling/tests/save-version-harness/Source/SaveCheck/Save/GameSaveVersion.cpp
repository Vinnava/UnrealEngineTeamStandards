#include "Save/GameSaveVersion.h"

#include "Serialization/CustomVersion.h"

DEFINE_LOG_CATEGORY(LogGameSave);

#if SAVE_CHECK_MUTATION == 1
// Mutation: regenerated after saves shipped
const FGuid FGameSaveVersion::GUID(0xF55A4078, 0xC8014254, 0xB399425E, 0x39281004);
#else
// Generated once for this project. Never copied from another project, never regenerated (24.5)
const FGuid FGameSaveVersion::GUID(0x706BED99, 0xC0394DC8, 0x9BB52099, 0x18E19786);
#endif

#if SAVE_CHECK_PHASE >= 1
// Registered at module load, so every save header records LatestVersion. Kept beside the GUID so the
// translation unit that every Serialize references is the one that registers
const FCustomVersionRegistration GRegisterGameSaveVersion(
    FGameSaveVersion::GUID, FGameSaveVersion::LatestVersion, TEXT("GameSaveVersion"));
#endif
