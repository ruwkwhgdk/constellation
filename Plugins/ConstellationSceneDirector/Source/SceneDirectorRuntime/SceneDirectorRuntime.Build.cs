using UnrealBuildTool;
public class SceneDirectorRuntime : ModuleRules
{
    public SceneDirectorRuntime(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "LevelSequence", "MovieScene", "MovieSceneTracks", "UniversalObjectLocator", "Slate", "SlateCore", "InputCore", "UMG" });
    }
}
