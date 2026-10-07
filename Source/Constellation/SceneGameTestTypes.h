#pragma once
#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "SceneGameTestTypes.generated.h"
UCLASS(Transient,NotBlueprintable)
class USceneGameTestCallbacks:public UObject
{
 GENERATED_BODY()
public:
 int32 Returned=0,Finished=0;
 UFUNCTION() void OnReturned(){++Returned;}
 UFUNCTION() void OnStopped(bool Complete){if(Complete)++Finished;}
};
