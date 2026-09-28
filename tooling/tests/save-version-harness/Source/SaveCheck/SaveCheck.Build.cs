using UnrealBuildTool;

public class SaveCheck : ModuleRules
{
	public SaveCheck(ReadOnlyTargetRules Target) : base(Target)
	{
		// Strict: no PCH and no unity, so every file must include what it uses - the code here is what
		// section 24 tells a project to copy
		PCHUsage = PCHUsageMode.NoPCHs;
		bUseUnity = false;

		PublicIncludePaths.Add(ModuleDirectory);
		PrivateDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });
	}
}
