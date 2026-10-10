#pragma once
#include "SceneDirectorAsset.h"
struct FDirectorVisionState
{
 float EyeOpen=1,Blur=0,Haze=0;
 FLinearColor HazeColor=FLinearColor::White;
};
namespace DirectorVision
{
 SCENEDIRECTORRUNTIME_API bool Validate(const FDirectorStep& Step,FString& Error);
 SCENEDIRECTORRUNTIME_API double Duration(const FDirectorStep& Step);
 SCENEDIRECTORRUNTIME_API bool Conflicts(EDirectorNodeType A,EDirectorNodeType B);
 // Stateless sampling is shared by paused playback, reverse scrubbing and runtime.
 SCENEDIRECTORRUNTIME_API FDirectorVisionState Evaluate(const TArray<FDirectorCue>& Cues,double Frame);
}
