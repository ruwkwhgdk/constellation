#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SubwayTunnelEnvironment.generated.h"
class UBoxComponent;
class UPostProcessComponent;
/** Local tunnel exposure. Does not change either map's global exposure. */
UCLASS()
class CONSTELLATION_API ASubwayTunnelEnvironment : public AActor
{
    GENERATED_BODY()
  public:
    ASubwayTunnelEnvironment();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Subway")
    TObjectPtr<UBoxComponent> Bounds;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Subway")
    TObjectPtr<UPostProcessComponent> PostProcess;
};
