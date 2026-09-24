using UnrealBuildTool;

public class NamingCheckEditor : ModuleRules
{
	public NamingCheckEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		// Strict: no PCH and no unity, so every file must include what it uses. A missing include that
		// a shared PCH would have hidden fails here, which is the point of this build.
		PCHUsage = PCHUsageMode.NoPCHs;
		bUseUnity = false;

		PrivateDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "DataValidation" });
	}
}
