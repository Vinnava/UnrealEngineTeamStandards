#pragma once

#include "CoreMinimal.h"
#include "EditorValidatorBase.h"
#include "ProjectValidatorBase.generated.h"

/**
 * Shared base for this standard's asset validators: owns the one content root they all check.
 * Abstract, so the validation subsystem never runs it on its own.
 */
UCLASS(Abstract, Config = Editor)
class UProjectValidatorBase : public UEditorValidatorBase
{
	GENERATED_BODY()

private:   // Variables
	/** Content root to check, e.g. /Game/_MyProject. GlobalConfig, so every subclass reads this one value */
	UPROPERTY(GlobalConfig)
	FString contentRoot;

protected: // Functions
	/** True when the asset sits under contentRoot; third-party folders are left alone (2.2) */
	bool IsUnderContentRoot(const FAssetData& assetData) const;

public:    // Functions
	/** Sets the default content root; each project overrides it in DefaultEditor.ini */
	UProjectValidatorBase();
};
