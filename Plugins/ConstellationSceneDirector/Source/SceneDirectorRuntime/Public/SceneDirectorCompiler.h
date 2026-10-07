#pragma once
#include "CoreMinimal.h"
class USceneDirectorAsset;
class UAnimSequence;
struct FDirectorSchedule
{
    TArray<int32> Order;
    TArray<int32> StartFrames;
    TArray<int32> FinishFrames;
    TArray<int32> BranchFinishFrames;
    TArray<FTransform> FromPoses, ToPoses;
    TArray<float> EffectiveSpeeds;
    TArray<UAnimSequence*> Animations;
    int32 EndFrame=0;
};
class SCENEDIRECTORRUNTIME_API FSceneDirectorCompiler
{
public:
    static bool Schedule(const USceneDirectorAsset& Asset,FDirectorSchedule& Result,FString& Error);
    static bool Validate(const USceneDirectorAsset& Asset, TArray<int32>& Order, FString& Error);
    static bool Compile(USceneDirectorAsset& Asset, FString& Error);
};
