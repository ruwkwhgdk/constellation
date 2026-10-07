#pragma once
#include "SceneDirectorAction.h"
#include "SceneDirectorStatueAction.generated.h"
/** Adapter for the project's existing Ac_Stats recovery function. Never runs in editor preview. */
UCLASS()
class SCENEDIRECTORRUNTIME_API USceneDirectorStatueRestoreAction : public USceneDirectorAction
{
 GENERATED_BODY()
public:
 virtual bool Execute_Implementation(ASceneDirectorPlayer* Player,AActor* Target,const FDirectorActionParameters& Parameters,FString& Error) override;
};
