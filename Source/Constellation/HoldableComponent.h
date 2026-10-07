#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CarryData.h"
#include "HoldableComponent.generated.h"

class UStaticMeshComponent;
class UCarryComponent;

UCLASS(Blueprintable, ClassGroup=(Interaction), meta=(BlueprintSpawnableComponent))
class CONSTELLATION_API UHoldableComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UHoldableComponent();
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Holdable|Data", meta=(RowType="/Script/Constellation.HoldableItemRow"))
    FDataTableRowHandle ItemRow;
    UFUNCTION(BlueprintCallable, Category="Holdable|Data") bool ApplySettings();
    UFUNCTION(BlueprintPure, Category="Holdable") float GetWeightKg() const;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Holdable|Resolved")
    TObjectPtr<UStaticMeshComponent> HoldMesh;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Holdable|Resolved")
    FTransform CarryOffset = FTransform(FRotator::ZeroRotator, FVector(32,0,30));
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Holdable|Resolved")
    FTransform LeftHandGrip;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Holdable|Resolved")
    FTransform RightHandGrip;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Holdable|Resolved")
    bool bCanThrow = true;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Holdable|Resolved")
    FRotator PlaceRotation;
    UPROPERTY(BlueprintReadOnly, Transient, Category="Holdable")
    TWeakObjectPtr<UCarryComponent> Carrier;
    UFUNCTION(BlueprintPure, Category="Holdable")
    UStaticMeshComponent* GetHoldMesh() const;
    bool IsUsable() const;
    UPROPERTY(BlueprintReadOnly,Transient,Category="Holdable") bool bHasThrowContact=false;
    UPROPERTY(BlueprintReadOnly,Transient,Category="Holdable") FVector ThrowContactLocation=FVector::ZeroVector;
    void BeginBallisticFlight();
    void EndBallisticFlight();
    void RestoreWhenClear(ECollisionEnabled::Type Collision,bool bGravity,bool bPhysics);
protected:
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction) override;
private:
    UFUNCTION() void OnFlightHit(UPrimitiveComponent* Component,AActor* OtherActor,UPrimitiveComponent* OtherComponent,FVector NormalImpulse,const FHitResult& Hit);
    float FlightLinearDamping=0, FlightAngularDamping=0;
    bool bFlight=false, bSavedHitNotifications=false;
    bool bPendingRestore=false, bRestoreGravity=true, bRestorePhysics=false;
    ECollisionEnabled::Type RestoreCollision=ECollisionEnabled::QueryAndPhysics;
};
