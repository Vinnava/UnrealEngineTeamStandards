#pragma once

#include "CoreMinimal.h"
#include "ProjectValidatorBase.h"
#include "AssetNamingValidator.generated.h"

class UBlueprint;

/**
 * Fails assets under the project content root that break the naming rules in standard 7.1 to 7.3.
 * Runs on save, from Tools > Validate Data, and in CI. Lives in an editor module that depends on DataValidation.
 */
UCLASS(Config = Editor)
class UAssetNamingValidator : public UProjectValidatorBase
{
	GENERATED_BODY()

private:   // Functions
	/** Prefixes the asset's type accepts under 7.1. False when 7.1 has no rule; true and empty when the rule is none */
	bool FindRequiredPrefixes(const FAssetData& assetData, const UObject* asset, TArray<FString>& outPrefixes) const;

	/** Prefix for a Blueprint asset, from its Blueprint type and parent class - includes the 7.2 role infixes */
	FString FindBlueprintPrefix(const UBlueprint& blueprint) const;

protected: // Functions
	/** Only assets inside the content root are checked, so third-party folders are left alone (2.2) */
	virtual bool CanValidateAsset_Implementation(
		const FAssetData& assetData, UObject* object, FDataValidationContext& context) const override;

	/** Fails the asset on a space, a missing or wrong prefix, or a non-PascalCase name after it */
	virtual EDataValidationResult ValidateLoadedAsset_Implementation(
		const FAssetData& assetData, UObject* asset, FDataValidationContext& context) override;
};
