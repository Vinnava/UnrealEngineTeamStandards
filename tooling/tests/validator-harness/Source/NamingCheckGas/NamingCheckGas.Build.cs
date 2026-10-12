using UnrealBuildTool;

public class NamingCheckGas : ModuleRules
{
	public NamingCheckGas(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.NoPCHs;
		bUseUnity = false;

		// Kept out of NamingCheckEditor, so the validators still prove they build without GAS (25.1).
		// A subclass of the ability system component links its tag and task bases as well.
		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"GameplayAbilities",
			"GameplayTags",
			"GameplayTasks",
		});
	}
}
