#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "LittleGirlLocomotionComponent.generated.h"
class UBlendSpace;
class USkeletalMesh;

/** Opt-in bridge for the existing story NPC hierarchy. */
UCLASS(ClassGroup=(Animation), meta=(BlueprintSpawnableComponent))
class CONSTELLATION_API ULittleGirlLocomotionComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    ULittleGirlLocomotionComponent();
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="LittleGirl")
    TObjectPtr<USkeletalMesh> PrototypeMesh;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="LittleGirl")
    TObjectPtr<UBlendSpace> LocomotionBlendSpace;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="LittleGirl")
    bool bStartAutomatically = true;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="LittleGirl")
    float LocomotionSpeed = 0.f;
    UFUNCTION(BlueprintCallable, Category="LittleGirl")
    void ResumeLocomotion();
    UFUNCTION(BlueprintCallable, Category="LittleGirl")
    void SuspendLocomotion();
private:
    bool bFirstTick = true;
    bool bConfigured = false;
    bool bSuspended = false;
    FVector RestMeshLocation = FVector::ZeroVector;
};
