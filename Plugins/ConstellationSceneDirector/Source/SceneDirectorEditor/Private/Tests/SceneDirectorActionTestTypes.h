#pragma once
#include "SceneDirectorAction.h"
#include "SceneDirectorActionTestTypes.generated.h"
UCLASS()
class USceneDirectorTestAction : public USceneDirectorAction
{
    GENERATED_BODY()
public:
    int32 ExecutionCount=0;
    static TArray<FName> Calls;
    static bool bReentryDenied;
    virtual bool Execute_Implementation(ASceneDirectorPlayer* Player,AActor* Target,const FDirectorActionParameters& Parameters,FString& Error) override;
};
