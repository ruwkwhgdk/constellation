#pragma once
#include "CoreMinimal.h"
#include "SceneDirectorAsset.h"
class SCENEDIRECTORRUNTIME_API FDirectorPerformance
{
public:
    FDirectorPerformance();
    ~FDirectorPerformance();
    bool Evaluate(const TArray<FDirectorCue>& Cues,double Frame,TFunctionRef<AActor*(FName)> Resolve,FString& Error);
    void Reset();
private:
    struct FState;TUniquePtr<FState> State;
};
