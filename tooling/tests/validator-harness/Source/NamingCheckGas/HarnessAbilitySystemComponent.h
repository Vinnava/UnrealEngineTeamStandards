#pragma once

#include "AbilitySystemComponent.h"
#include "HarnessAbilitySystemComponent.generated.h"

/**
 * The project-side ability system component the harness's BP_AC_ cases derive from. The engine's
 * own class is not Blueprintable, so a project's ASC Blueprint always has a C++ parent like this (25.1).
 */
UCLASS(Blueprintable)
class UHarnessAbilitySystemComponent : public UAbilitySystemComponent
{
	GENERATED_BODY()
};
