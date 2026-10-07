#pragma once
#include "CoreMinimal.h"
#include "SceneDirectorAction.h"
#include "ConstellationSceneFXAction.generated.h"
UCLASS()
class CONSTELLATIONVFX_API UConstellationSceneFXAction : public USceneDirectorAction {
 GENERATED_BODY()
public:
 virtual bool Execute_Implementation(ASceneDirectorPlayer* Player,AActor* Target,const FDirectorActionParameters& Parameters,FString& Error) override;
};
