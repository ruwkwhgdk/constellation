#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "InteractionAvailabilityComponent.generated.h"

// Per-object runtime state shared by interaction input and its prompt.
UCLASS(Blueprintable, ClassGroup=(Interaction), meta=(BlueprintSpawnableComponent))
class CONSTELLATION_API UInteractionAvailabilityComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UInteractionAvailabilityComponent();
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Interaction")
    bool bInteractionUnavailable=false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Interaction")
    FName CompletedProperty;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Interaction")
    bool bRespectInteractOnce=true;
    UFUNCTION(BlueprintCallable, Category="Interaction")
    bool RefreshAvailability();
    UFUNCTION(BlueprintPure, Category="Interaction")
    static bool CanActorInteract(UObject* Target);
protected:
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* Function) override;
};
