#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PickupTutorialTrigger.generated.h"

class UBoxComponent;
class UTutorialPromptWidget;

/** Nonblocking, once-per-visit pickup lesson for an authored player area. */
UCLASS()
class CONSTELLATION_API APickupTutorialTrigger : public AActor
{
 GENERATED_BODY()
public:
 APickupTutorialTrigger();
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Tutorial") TObjectPtr<UBoxComponent> Area;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tutorial", meta=(ClampMin="1")) FVector AreaExtent=FVector(200,350,160);
 UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Transient, Category="Tutorial") bool bHasShown=false;
 virtual void OnConstruction(const FTransform& Transform) override;
 virtual void Tick(float DeltaSeconds) override;
protected:
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
 UPROPERTY(Transient) TObjectPtr<UTutorialPromptWidget> Prompt;
};
