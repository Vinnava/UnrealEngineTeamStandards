#include "ProjectValidatorBase.h"

UProjectValidatorBase::UProjectValidatorBase()
{
	contentRoot = TEXT("/Game/_Game");
}

bool UProjectValidatorBase::IsUnderContentRoot(const FAssetData& assetData) const
{
	if (contentRoot.IsEmpty())
	{
		return false;
	}

	// Trailing slash on both sides, so /Game/_Game does not also match /Game/_GameOld
	FString root = contentRoot;
	root.RemoveFromEnd(TEXT("/"));
	const FString packagePath = assetData.PackagePath.ToString() + TEXT("/");
	return packagePath.StartsWith(root + TEXT("/"));
}
