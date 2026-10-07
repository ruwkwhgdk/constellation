#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Chaos/ChaosGameplayEventDispatcher.h"
#include "ConstellationGlassRelay.generated.h"
class UGeometryCollectionComponent;
/** Adds small debris to existing authored glass fractures without replacing their gameplay. */
UCLASS()
class CONSTELLATIONVFX_API AConstellationGlassRelay : public AActor {
 GENERATED_BODY()
public:
 AConstellationGlassRelay();
 virtual void BeginPlay() override;
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
 UFUNCTION() void OnGlassBreak(const FChaosBreakEvent& Event);
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Glass") int32 BoundCollections=0;
private:
 void BindGlass();FTimerHandle BindTimer;
 TArray<TWeakObjectPtr<UGeometryCollectionComponent>> Collections;
 TArray<FVector> LastLocations;TArray<double> LastTimes;
};
