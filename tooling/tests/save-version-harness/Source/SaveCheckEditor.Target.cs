using UnrealBuildTool;

public class SaveCheckEditorTarget : TargetRules
{
	public SaveCheckEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("SaveCheck");
	}
}
