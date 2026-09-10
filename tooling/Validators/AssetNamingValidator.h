#pragma once

#include "CoreMinimal.h"
#include "EditorValidatorBase.h"
#include "AssetNamingValidator.generated.h"

class UBlueprint;

/**
 * Fails assets under the project content root that break the naming rules in standard 7.1 and 7.3.
 * Runs on save, from Tools > Validate Data, and in CI. Lives in an editor module that depends on DataValidation.
 */
UCLASS(Config = Editor)
class UAssetNamingValidator : public UEditorValidatorBase
{
	GENERATED_BODY()

private:   // Variables
	/** Content root to check, e.g. /Game/_MyProject. Set per project in DefaultEditor.ini */
	UPROPERTY(Config)
	FString contentRoot;

private:   // Functions
	/** Prefix the asset's type requires under 7.1; empty when the type has no rule */
	FString FindRequiredPrefix(const FAssetData& assetData, const UObject* asset) const;

	/** Prefix for a Blueprint asset, resolved from its Blueprint type and parent class */
	FString FindBlueprintPrefix(const UBlueprint& blueprint) const;

protected: // Functions
	/** Only assets inside contentRoot are checked, so third-party folders are left alone (2.2) */
	virtual bool CanValidateAsset_Implementation(const FAssetData& assetData, UObject* object,
		FDataValidationContext& context) const override;

	/** Fails the asset on a space, a missing or wrong prefix, or a non-PascalCase name after it */
	virtual EDataValidationResult ValidateLoadedAsset_Implementation(const FAssetData& assetData,
		UObject* asset, FDataValidationContext& context) override;

public:    // Functions
	/** Sets the default content root; each project overrides it in DefaultEditor.ini */
	UAssetNamingValidator();
};
