#include "AssetNamingValidator.h"

#include "Components/ActorComponent.h"
#include "Engine/Blueprint.h"
#include "Engine/DataAsset.h"
#include "Misc/DataValidation.h"

#define LOCTEXT_NAMESPACE "AssetNamingValidator"

namespace AssetNamingValidator
{
	/** Asset class name to required prefix (standard 7.1). Blueprints and DataAssets are resolved in code */
	static const TCHAR* const ClassPrefixes[][2] =
	{
		{ TEXT("World"), TEXT("L_") },
		{ TEXT("StaticMesh"), TEXT("SM_") },
		{ TEXT("SkeletalMesh"), TEXT("SKM_") },
		{ TEXT("Skeleton"), TEXT("SK_") },
		{ TEXT("PhysicsAsset"), TEXT("PHYS_") },
		{ TEXT("Material"), TEXT("M_") },
		{ TEXT("MaterialInstanceConstant"), TEXT("MI_") },
		{ TEXT("MaterialFunction"), TEXT("MF_") },
		{ TEXT("MaterialParameterCollection"), TEXT("MPC_") },
		{ TEXT("Texture2D"), TEXT("T_") },
		{ TEXT("TextureRenderTarget2D"), TEXT("RT_") },
		{ TEXT("AnimSequence"), TEXT("AS_") },
		{ TEXT("AnimMontage"), TEXT("AM_") },
		{ TEXT("BlendSpace"), TEXT("BS_") },
		{ TEXT("BlendSpace1D"), TEXT("BS_") },
		{ TEXT("AimOffsetBlendSpace"), TEXT("AO_") },
		{ TEXT("AimOffsetBlendSpace1D"), TEXT("AO_") },
		{ TEXT("AnimBlueprint"), TEXT("ABP_") },
		{ TEXT("WidgetBlueprint"), TEXT("WBP_") },
		{ TEXT("ControlRigBlueprint"), TEXT("CR_") },
		{ TEXT("IKRigDefinition"), TEXT("IK_") },
		{ TEXT("IKRetargeter"), TEXT("RTG_") },
		{ TEXT("InputAction"), TEXT("IA_") },
		{ TEXT("InputMappingContext"), TEXT("IMC_") },
		{ TEXT("NiagaraSystem"), TEXT("NS_") },
		{ TEXT("NiagaraEmitter"), TEXT("NE_") },
		{ TEXT("SoundCue"), TEXT("SC_") },
		{ TEXT("SoundWave"), TEXT("SW_") },
		{ TEXT("SoundAttenuation"), TEXT("ATT_") },
		{ TEXT("SoundClass"), TEXT("SCL_") },
		{ TEXT("MetaSoundSource"), TEXT("MSS_") },
		{ TEXT("MetaSoundPatch"), TEXT("MSP_") },
		{ TEXT("LevelSequence"), TEXT("LS_") },
		{ TEXT("UserDefinedEnum"), TEXT("E_") },
		{ TEXT("UserDefinedStruct"), TEXT("F_") },
		{ TEXT("DataTable"), TEXT("DT_") },
		{ TEXT("CurveTable"), TEXT("CT_") },
		{ TEXT("CurveFloat"), TEXT("CF_") },
		{ TEXT("CurveVector"), TEXT("CV_") },
		{ TEXT("CurveLinearColor"), TEXT("CLC_") },
		{ TEXT("PhysicalMaterial"), TEXT("PM_") },
		{ TEXT("BlackboardData"), TEXT("BB_") },
		{ TEXT("BehaviorTree"), TEXT("BT_") },
		{ TEXT("StateTree"), TEXT("ST_") },
	};

	/** True when the class or any parent has this name; avoids linking optional modules such as GAS */
	static bool IsChildOfClassNamed(const UClass* classToTest, const FName parentName)
	{
		for (const UClass* current = classToTest; current; current = current->GetSuperClass())
		{
			if (current->GetFName() == parentName)
			{
				return true;
			}
		}

		return false;
	}
}

UAssetNamingValidator::UAssetNamingValidator()
{
	contentRoot = TEXT("/Game/_Game");
}

bool UAssetNamingValidator::CanValidateAsset_Implementation(const FAssetData& assetData, UObject* object,
	FDataValidationContext& context) const
{
	if (!IsValid(object) || contentRoot.IsEmpty())
	{
		return false;
	}

	// Trailing slash on both sides, so /Game/_Game does not also match /Game/_GameOld
	FString root = contentRoot;
	root.RemoveFromEnd(TEXT("/"));
	const FString packagePath = assetData.PackagePath.ToString() + TEXT("/");
	return packagePath.StartsWith(root + TEXT("/"));
}

EDataValidationResult UAssetNamingValidator::ValidateLoadedAsset_Implementation(const FAssetData& assetData,
	UObject* asset, FDataValidationContext& context)
{
	const FString assetName = assetData.AssetName.ToString();

	if (assetName.Contains(TEXT(" ")))
	{
		AssetFails(asset, FText::Format(LOCTEXT("NameHasSpace", "'{0}' contains a space (standard 7.3)."),
			FText::AsCultureInvariant(assetName)));
		return EDataValidationResult::Invalid;
	}

	const FString requiredPrefix = FindRequiredPrefix(assetData, asset);
	if (requiredPrefix.IsEmpty())
	{
		return EDataValidationResult::NotValidated;
	}

	if (!assetName.StartsWith(requiredPrefix, ESearchCase::CaseSensitive))
	{
		AssetFails(asset, FText::Format(LOCTEXT("MissingPrefix", "'{0}' must start with '{1}' (standard 7.1)."),
			FText::AsCultureInvariant(assetName), FText::AsCultureInvariant(requiredPrefix)));
		return EDataValidationResult::Invalid;
	}

	// PascalCase after the prefix (7.3); a leading digit is allowed for indexed variants
	const int32 nameStart = requiredPrefix.Len();
	const bool bHasName = assetName.Len() > nameStart;
	if (!bHasName || !(FChar::IsUpper(assetName[nameStart]) || FChar::IsDigit(assetName[nameStart])))
	{
		AssetFails(asset, FText::Format(LOCTEXT("NotPascalCase", "'{0}' needs a PascalCase name after '{1}' (standard 7.3)."),
			FText::AsCultureInvariant(assetName), FText::AsCultureInvariant(requiredPrefix)));
		return EDataValidationResult::Invalid;
	}

	AssetPasses(asset);
	return EDataValidationResult::Valid;
}

FString UAssetNamingValidator::FindRequiredPrefix(const FAssetData& assetData, const UObject* asset) const
{
	// The table is checked first, so Widget, Anim and Control Rig Blueprints get their own prefixes
	const FString className = assetData.AssetClassPath.GetAssetName().ToString();
	for (const auto& entry : AssetNamingValidator::ClassPrefixes)
	{
		if (className == entry[0])
		{
			return entry[1];
		}
	}

	if (const UBlueprint* blueprint = Cast<UBlueprint>(asset))
	{
		return FindBlueprintPrefix(*blueprint);
	}

	if (asset->IsA<UDataAsset>())
	{
		return TEXT("DA_");
	}

	return FString();
}

FString UAssetNamingValidator::FindBlueprintPrefix(const UBlueprint& blueprint) const
{
	if (blueprint.BlueprintType == BPTYPE_Interface)
	{
		return TEXT("BPI_");
	}

	if (blueprint.BlueprintType == BPTYPE_FunctionLibrary)
	{
		return TEXT("BFL_");
	}

	// Macro libraries have no prefix in 7.1
	if (blueprint.BlueprintType == BPTYPE_MacroLibrary)
	{
		return FString();
	}

	const UClass* parentClass = blueprint.ParentClass;
	if (AssetNamingValidator::IsChildOfClassNamed(parentClass, TEXT("GameplayEffect")))
	{
		return TEXT("GE_");
	}

	if (AssetNamingValidator::IsChildOfClassNamed(parentClass, TEXT("GameplayAbility")))
	{
		return TEXT("GA_");
	}

	if (parentClass && parentClass->IsChildOf(UActorComponent::StaticClass()))
	{
		return TEXT("BPC_");
	}

	return TEXT("BP_");
}

#undef LOCTEXT_NAMESPACE
