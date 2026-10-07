using UnrealBuildTool;
public class CombatRuntime : ModuleRules
{
    public CombatRuntime(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "GameplayAbilities", "GameplayTags", "GameplayTasks", "AIModule", "EnhancedInput", "ConstellationVFX" });
        PrivateDependencyModuleNames.AddRange(new[] { "InputCore", "NavigationSystem", "Json", "Slate", "SlateCore", "ApplicationCore", "Niagara", "PhysicsCore", "SceneDirectorRuntime" });
    }
}
