using UnrealBuildTool;

public class ConstellationResourceTools : ModuleRules
{
    public ConstellationResourceTools(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PrivateDependencyModuleNames.Add("Json");
        PrivateDependencyModuleNames.AddRange(new[] { "MeshDescription", "StaticMeshDescription", "SkeletalMeshDescription" });
        PrivateDependencyModuleNames.AddRange(new[] { "Slate", "RenderCore", "ToolMenus", "PropertyEditor", "Kismet", "StringTableEditor", "SceneDirectorEditor", "ApplicationCore", "InputCore" });
        PrivateDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "UnrealEd", "UMG", "UMGEditor", "SceneDirectorRuntime", "SlateCore", "BlueprintGraph", "AIModule", "Constellation", "EnhancedInput", "InputBlueprintNodes", "AnimGraph", "AnimGraphRuntime", "AssetRegistry", "AnimationBlueprintLibrary" });
    }
}
