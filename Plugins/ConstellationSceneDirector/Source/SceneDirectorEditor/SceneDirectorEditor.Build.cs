using UnrealBuildTool;
public class SceneDirectorEditor : ModuleRules
{
    public SceneDirectorEditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "SceneDirectorRuntime", "UnrealEd" });
        PrivateDependencyModuleNames.AddRange(new[] { "Slate", "SlateCore", "GraphEditor", "PropertyEditor", "AssetTools", "ToolMenus", "LevelSequence", "MovieScene", "MovieSceneTracks", "CinematicCamera", "InputCore", "Sequencer", "LevelSequenceEditor", "KismetCompiler", "BlueprintGraph", "AssetRegistry", "ContentBrowser", "UniversalObjectLocator" });
    }
}
