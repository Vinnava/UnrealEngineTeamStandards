#pragma once

#include "CoreMinimal.h"
#include "ProjectValidatorBase.h"
#include "AssetContentValidator.generated.h"

class UStaticMesh;
class UTexture;

/**
 * Fails content under the project content root that breaks the checkable rules in standard 23:
 * textures that cannot stream or exceed the size budget, and heavy non-Nanite meshes with no LODs.
 */
UCLASS(Config = Editor)
class UAssetContentValidator : public UProjectValidatorBase
{
	GENERATED_BODY()

private:   // Variables
	/** Largest texture dimension allowed without virtual texturing (23.1). A project budget, not an engine limit */
	UPROPERTY(Config)
	int32 maxTextureSize;

	/** A non-Nanite static mesh with more triangles than this in LOD 0 must carry LODs (23.2) */
	UPROPERTY(Config)
	int32 lodTriangleThreshold;

private:   // Functions
	/** Fails a streamable texture that cannot stream, or a non-virtual one over maxTextureSize */
	EDataValidationResult ValidateTexture(const UTexture& texture);

	/** Fails a non-Nanite static mesh over lodTriangleThreshold that has a single LOD */
	EDataValidationResult ValidateStaticMesh(const UStaticMesh& mesh);

protected: // Functions
	/** Textures and static meshes under the content root only */
	virtual bool CanValidateAsset_Implementation(
		const FAssetData& assetData, UObject* object, FDataValidationContext& context) const override;

	/** Dispatches to the check for the asset's type */
	virtual EDataValidationResult ValidateLoadedAsset_Implementation(
		const FAssetData& assetData, UObject* asset, FDataValidationContext& context) override;

public:    // Functions
	/** Sets the default budgets; each project overrides them in DefaultEditor.ini */
	UAssetContentValidator();
};
