#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SubwayStreamingGate.h"
#include "SubwayTravelVolume.generated.h"
class UBoxComponent;
UCLASS()
class CONSTELLATION_API ASubwayTravelVolume : public AActor
{
    GENERATED_BODY()
  public:
    ASubwayTravelVolume();
    virtual void Tick(float DeltaSeconds) override;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Subway")
    TObjectPtr<UBoxComponent> Zone;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Subway")
    TObjectPtr<UBoxComponent> SafetyBarrier;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subway")
    TSoftObjectPtr<UWorld> DestinationMap;
    // Frames at floor height. +X goes into source and out of destination.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subway") FTransform ArrivalTransform;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subway")
    float MaximumFootHeight = 1000000;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subway") float PreloadDistance = 4000;

  private:
    FSubwayStreamingGate Gate;
};
