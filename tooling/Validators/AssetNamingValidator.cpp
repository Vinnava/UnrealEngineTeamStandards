#include "AssetNamingValidator.h"

#include "Components/ActorComponent.h"
#include "Engine/Blueprint.h"
#include "Engine/DataAsset.h"
#include "Misc/DataValidation.h"

#define LOCTEXT_NAMESPACE "AssetNamingValidator"

namespace AssetNamingValidator
{
	/** Asset class name to required prefix (standard 7.1). Blueprints and DataAssets are resolved in code */
	static const TCHAR* const ClassPrefixes[][2] = {
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
		{ TEXT("TextureCube"), TEXT("T_") },
		{ TEXT("Texture2DArray"), TEXT("T_") },
		{ TEXT("TextureCubeArray"), TEXT("T_") },
		{ TEXT("VolumeTexture"), TEXT("T_") },
		{ TEXT("TextureRenderTarget2D"), TEXT("RT_") },
		{ TEXT("TextureRenderTargetCube"), TEXT("RT_") },
		{ TEXT("TextureRenderTarget2DArray"), TEXT("RT_") },
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

	/** The one type that accepts a second prefix: an HDRI backdrop texture is HDRI_, not T_ (7.1) */
	static const TCHAR* const AlternatePrefixes[][2] = {
		{ TEXT("T_"), TEXT("HDRI_") },
	};

	/** Blueprint parent class name to the core-framework role prefix its name carries (standard 7.2) */
	static const TCHAR* const BlueprintRolePrefixes[][2] = {
		{ TEXT("GameModeBase"), TEXT("BP_GM_") },
		{ TEXT("GameStateBase"), TEXT("BP_GS_") },
		{ TEXT("PlayerController"), TEXT("BP_PC_") },
		{ TEXT("PlayerState"), TEXT("BP_PS_") },
		{ TEXT("GameInstance"), TEXT("BP_GI_") },
		{ TEXT("AIController"), TEXT("BP_AIC_") },
		{ TEXT("Character"), TEXT("BP_CH_") },
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

	/** Renders the accepted prefixes for a failure message, as "'T_' or 'HDRI_'" */
	static FString DescribePrefixes(const TArray<FString>& prefixes)
	{
		// The caller holds these longest-first for matching; read out shortest-first, which puts the
		// type's own prefix ahead of the TEMP and alternate forms it also accepts.
		TArray<FString> ordered = prefixes;
		ordered.Sort(
			[](const FString& left, const FString& right)
			{
				return left.Len() < right.Len();
			});

		TArray<FString> quoted;
		quoted.Reserve(ordered.Num());

		for (const FString& prefix : ordered)
		{
			quoted.Add(FString::Printf(TEXT("'%s'"), *prefix));
		}

		return FString::Join(quoted, TEXT(" or "));
	}
} // namespace AssetNamingValidator

UAssetNamingValidator::UAssetNamingValidator()
{
	contentRoot = TEXT("/Game/_Game");
}

bool UAssetNamingValidator::CanValidateAsset_Implementation(
	const FAssetData& assetData, UObject* object, FDataValidationContext& context) const
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

EDataValidationResult UAssetNamingValidator::ValidateLoadedAsset_Implementation(
	const FAssetData& assetData, UObject* asset, FDataValidationContext& context)
{
	const FString assetName = assetData.AssetName.ToString();

	if (assetName.Contains(TEXT(" ")))
	{
		const FText message = FText::Format(
			LOCTEXT("NameHasSpace", "'{0}' contains a space (standard 7.3)."), FText::AsCultureInvariant(assetName));
		AssetFails(asset, message);
		return EDataValidationResult::Invalid;
	}

	TArray<FString> requiredPrefixes;
	FindRequiredPrefixes(assetData, asset, requiredPrefixes);
	if (requiredPrefixes.IsEmpty())
	{
		return EDataValidationResult::NotValidated;
	}

	// The list is longest-first, so this is the longest matching prefix, not merely the first.
	// Predicate runs inline, so capturing by reference is safe here (10.2)
	const FString* matchedPrefix = requiredPrefixes.FindByPredicate(
		[&assetName](const FString& prefix)
		{
			return assetName.StartsWith(prefix, ESearchCase::CaseSensitive);
		});

	if (!matchedPrefix)
	{
		const FText message = FText::Format(LOCTEXT("MissingPrefix", "'{0}' must start with {1} (standard 7.1, 7.2)."),
			FText::AsCultureInvariant(assetName),
			FText::AsCultureInvariant(AssetNamingValidator::DescribePrefixes(requiredPrefixes)));
		AssetFails(asset, message);
		return EDataValidationResult::Invalid;
	}

	// PascalCase after the prefix (7.3); a leading digit is allowed for indexed variants
	const int32 nameStart = matchedPrefix->Len();
	const bool bHasName = assetName.Len() > nameStart;
	if (!bHasName || !(FChar::IsUpper(assetName[nameStart]) || FChar::IsDigit(assetName[nameStart])))
	{
		const FText message =
			FText::Format(LOCTEXT("NotPascalCase", "'{0}' needs a PascalCase name after '{1}' (standard 7.3)."),
				FText::AsCultureInvariant(assetName), FText::AsCultureInvariant(*matchedPrefix));
		AssetFails(asset, message);
		return EDataValidationResult::Invalid;
	}

	AssetPasses(asset);
	return EDataValidationResult::Valid;
}

void UAssetNamingValidator::FindRequiredPrefixes(
	const FAssetData& assetData, const UObject* asset, TArray<FString>& outPrefixes) const
{
	outPrefixes.Reset();

	// The table is checked first, so Widget, Anim and Control Rig Blueprints get their own prefixes
	const FString className = assetData.AssetClassPath.GetAssetName().ToString();
	for (const auto& entry : AssetNamingValidator::ClassPrefixes)
	{
		if (className == entry[0])
		{
			outPrefixes.Add(entry[1]);
			break;
		}
	}

	if (outPrefixes.IsEmpty())
	{
		if (const UBlueprint* blueprint = Cast<UBlueprint>(asset))
		{
			const FString blueprintPrefix = FindBlueprintPrefix(*blueprint);
			if (!blueprintPrefix.IsEmpty())
			{
				outPrefixes.Add(blueprintPrefix);
			}
		}
		else if (IsValid(asset) && asset->IsA<UDataAsset>())
		{
			outPrefixes.Add(TEXT("DA_"));
		}
	}

	if (outPrefixes.IsEmpty())
	{
		return;
	}

	for (const auto& entry : AssetNamingValidator::AlternatePrefixes)
	{
		if (outPrefixes[0] == entry[0])
		{
			outPrefixes.Add(entry[1]);
		}
	}

	// A prototype or test Blueprint is named BP_TEMP_ / WBP_TEMP_ whatever its parent class (8.2)
	if (outPrefixes[0].StartsWith(TEXT("BP_"), ESearchCase::CaseSensitive))
	{
		outPrefixes.AddUnique(TEXT("BP_TEMP_"));
	}
	else if (outPrefixes[0] == TEXT("WBP_"))
	{
		outPrefixes.Add(TEXT("WBP_TEMP_"));
	}

	// Longest first, so BP_TEMP_ is tested before BP_. Matching BP_ against BP_TEMP_thing would put the
	// PascalCase check on the T of TEMP and let a lower-case name through (7.3).
	outPrefixes.Sort(
		[](const FString& left, const FString& right)
		{
			return left.Len() > right.Len();
		});
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

	// Core-framework Blueprints carry a role prefix (7.2); no two of these classes share a line of descent
	for (const auto& entry : AssetNamingValidator::BlueprintRolePrefixes)
	{
		if (AssetNamingValidator::IsChildOfClassNamed(parentClass, entry[0]))
		{
			return entry[1];
		}
	}

	return TEXT("BP_");
}

#undef LOCTEXT_NAMESPACE
