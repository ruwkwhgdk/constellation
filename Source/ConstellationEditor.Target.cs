// Fill out your copyright notice in the Description page of Project Settings.

using UnrealBuildTool;
using System.Collections.Generic;

public class ConstellationEditorTarget : TargetRules
{
	public ConstellationEditorTarget(TargetInfo Target) : base(Target)
	{
        Type = TargetType.Editor;

        // 5.8 기본 빌드 설정으로 올림
        DefaultBuildSettings = BuildSettingsVersion.V7;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;

        ExtraModuleNames.Add("Constellation");
	}
}
