using UnrealBuildTool;
public class CombatEditor : ModuleRules
{
    public CombatEditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine" });
        PrivateDependencyModuleNames.AddRange(new[] { "CombatRuntime", "UnrealEd", "NavigationSystem", "ToolMenus", "Slate", "SlateCore", "Json" });
    }
}
