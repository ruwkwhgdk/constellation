using UnrealBuildTool;
public class ConstellationVFX : ModuleRules {
 public ConstellationVFX(ReadOnlyTargetRules Target) : base(Target) {
  PCHUsage=PCHUsageMode.UseExplicitOrSharedPCHs;
  PublicDependencyModuleNames.AddRange(new[]{"Core","CoreUObject","Engine","Niagara","SceneDirectorRuntime","GeometryCollectionEngine","ChaosSolverEngine","PhysicsCore","ProceduralMeshComponent"});
  PrivateDependencyModuleNames.AddRange(new[]{"Json","JsonUtilities","InputCore"});
 }
}
