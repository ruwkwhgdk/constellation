#pragma once
#include "CoreMinimal.h"
#include "SceneEventSaveData.generated.h"
USTRUCT() struct SCENEDIRECTORRUNTIME_API FSceneEventSavedState
{
 GENERATED_BODY()
 UPROPERTY() FString AssetPath;
 UPROPERTY() TMap<FName,bool> Bools;
 UPROPERTY() TMap<FName,int32> Ints;
};
USTRUCT() struct SCENEDIRECTORRUNTIME_API FSceneEventSaveData
{
 GENERATED_BODY()
 UPROPERTY() int32 Version=1;
 UPROPERTY() TMap<FString,FSceneEventSavedState> States;
 UPROPERTY() TSet<FString> Completed;
 void Merge(const FSceneEventSaveData& Other){for(const auto& Pair:Other.States)States.Add(Pair.Key,Pair.Value);Completed.Append(Other.Completed);}
};
DECLARE_DELEGATE_RetVal_TwoParams(bool,FSceneEventSaveHandler,const FSceneEventSaveData&,FString&);
