#pragma once
#include "CoreMinimal.h"
#include "SceneDirectorAction.h"
#include "SchoolOpeningSceneAction.generated.h"
UCLASS()
class CONSTELLATION_API USchoolOpeningSceneAction : public USceneDirectorAction
{
 GENERATED_BODY()
public:
 virtual bool Execute_Implementation(ASceneDirectorPlayer* Player,AActor* Target,const FDirectorActionParameters& Parameters,FString& Error) override;
};
