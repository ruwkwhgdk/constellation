#pragma once
#include "CoreMinimal.h"
#include "SceneDirectorAction.h"
#include "SceneSchoolAction.generated.h"
/** Adapters for the audited school sequences. No arbitrary function execution. */
UCLASS()
class CONSTELLATION_API USceneSchoolAction:public USceneDirectorAction
{
 GENERATED_BODY()
public:
 virtual bool Execute_Implementation(ASceneDirectorPlayer* Player,AActor* Target,const FDirectorActionParameters& Parameters,FString& Error) override;
};
