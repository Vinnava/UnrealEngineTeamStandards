#pragma once

#include "CoreMinimal.h"
#include "Commandlets/Commandlet.h"

#include "SaveCheckCommandlet.generated.h"

/**
 * Runs one step of run-save-version-test.ps1 against the build it was compiled into. Prints one
 * "SAVECHECK ok|FAIL" line per check and exits non-zero on any failure.
 */
UCLASS()
class USaveCheckCommandlet : public UCommandlet
{
    GENERATED_BODY()

public:    // Functions
    virtual int32 Main(const FString& params) override;
};
