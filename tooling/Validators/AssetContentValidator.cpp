#include "AssetContentValidator.h"

#include "Engine/StaticMesh.h"
#include "Engine/Texture.h"
#include "Engine/TextureDefines.h"
#include "Misc/DataValidation.h"

#define LOCTEXT_NAMESPACE "AssetContentValidator"

UAssetContentValidator::UAssetContentValidator()
{
	maxTextureSize = 4096;
	lodTriangleThreshold = 1000;
}

bool UAssetContentValidator::CanValidateAsset_Implementation(
	const FAssetData& assetData, UObject* object, FDataValidationContext& context) const
{
	if (!IsValid(object) || !IsUnderContentRoot(assetData))
	{
		return false;
	}

	// Decided here, never by returning NotValidated later - that fires an engine ensure (16.9).
	// Render targets and textures created at runtime have no source to measure
	if (const UTexture* texture = Cast<UTexture>(object))
	{
		return texture->Source.IsValid();
	}

	return object->IsA<UStaticMesh>();
}

EDataValidationResult UAssetContentValidator::ValidateLoadedAsset_Implementation(
	const FAssetData& assetData, UObject* asset, FDataValidationContext& context)
{
	if (const UTexture* texture = Cast<UTexture>(asset))
	{
		return ValidateTexture(*texture);
	}

	// CanValidateAsset admits only textures and static meshes
	return ValidateStaticMesh(*CastChecked<UStaticMesh>(asset));
}

EDataValidationResult UAssetContentValidator::ValidateTexture(const UTexture& texture)
{
	const int64 sizeX = texture.Source.GetSizeX();
	const int64 sizeY = texture.Source.GetSizeY();
	const FText dimensions = FText::AsCultureInvariant(FString::Printf(TEXT("%lldx%lld"), sizeX, sizeY));

	// UTexture::IsPossibleToStream refuses non-power-of-two data at runtime, so such a texture sits in
	// memory at full size. UI textures never stream anyway, and padding makes the built data pow2 (23.1)
	const bool bPowerOfTwo = FMath::IsPowerOfTwo(sizeX) && FMath::IsPowerOfTwo(sizeY);
	const bool bPadded = texture.PowerOfTwoMode != ETexturePowerOfTwoSetting::None;
	const bool bMeantToStream = !texture.NeverStream && texture.LODGroup != TEXTUREGROUP_UI;
	if (bMeantToStream && !bPowerOfTwo && !bPadded)
	{
		const FText message = FText::Format(
			LOCTEXT("CannotStream", "'{0}' is {1}, which can never stream. Resize it to powers of two, set Power Of "
									"Two Mode, or set Never Stream if it is meant to stay resident (standard 23.1)."),
			FText::AsCultureInvariant(GetNameSafe(&texture)), dimensions);
		AssetFails(&texture, message);
		return EDataValidationResult::Invalid;
	}

	if (!texture.VirtualTextureStreaming && FMath::Max(sizeX, sizeY) > maxTextureSize)
	{
		const FText message = FText::Format(
			LOCTEXT("TooLarge", "'{0}' is {1}, over the {2} budget for a texture without virtual "
								"texturing. Reduce it, or make the case for raising the budget (standard 23.1)."),
			FText::AsCultureInvariant(GetNameSafe(&texture)), dimensions, FText::AsNumber(maxTextureSize));
		AssetFails(&texture, message);
		return EDataValidationResult::Invalid;
	}

	AssetPasses(&texture);
	return EDataValidationResult::Valid;
}

EDataValidationResult UAssetContentValidator::ValidateStaticMesh(const UStaticMesh& mesh)
{
	// A Nanite mesh builds its own continuous LOD, so authored LODs would be ignored (13.7)
	if (mesh.IsNaniteEnabled())
	{
		AssetPasses(&mesh);
		return EDataValidationResult::Valid;
	}

	const int32 triangles = mesh.GetNumTriangles(0);
	if (triangles > lodTriangleThreshold && mesh.GetNumSourceModels() <= 1)
	{
		const FText message =
			FText::Format(LOCTEXT("NoLods", "'{0}' has {1} triangles, one LOD, and Nanite off. Give it LODs - a "
											"reduction LOD Group is enough - or enable Nanite (standard 13.7, 23.2)."),
				FText::AsCultureInvariant(GetNameSafe(&mesh)), FText::AsNumber(triangles));
		AssetFails(&mesh, message);
		return EDataValidationResult::Invalid;
	}

	AssetPasses(&mesh);
	return EDataValidationResult::Valid;
}

#undef LOCTEXT_NAMESPACE
