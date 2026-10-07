// Fill out your copyright notice in the Description page of Project Settings.

using UnrealBuildTool;

public class Constellation : ModuleRules
{
	public Constellation(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		PublicIncludePaths.Add(ModuleDirectory);
	
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "UMG", "EnhancedInput", "PhysicsCore", "SceneDirectorRuntime", "CombatRuntime" });

		PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore", "LevelSequence", "MovieScene" });
		
		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}
