using UnrealBuildTool;

public class NamingCheckEditorTarget : TargetRules
{
	public NamingCheckEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("NamingCheckEditor");
	}
}
