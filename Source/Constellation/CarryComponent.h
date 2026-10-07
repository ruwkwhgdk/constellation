#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CarryData.h"

#include "CarryComponent.generated.h"

class UHoldableComponent;
class UStaticMeshComponent;
class UAnimMontage;
class UCarryNoticeWidget;

UENUM(BlueprintType)
enum class ECarryState : uint8 { Idle, PickingUp, Carrying, Aiming, Placing, Throwing };

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FCarryStateChanged, ECarryState, State);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FCarryMessage, const FText&, Message);

UCLASS(ClassGroup=(Interaction), meta=(BlueprintSpawnableComponent))
class CONSTELLATION_API UCarryComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UCarryComponent();

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Carry|Data", meta=(RowType="/Script/Constellation.CarrySettingsRow"))
    FDataTableRowHandle SettingsRow;
    UFUNCTION(BlueprintCallable, Category="Carry|Data") bool ApplySettings();
    UFUNCTION(BlueprintPure, Category="Carry|Data") FText GetCarryMessage(FName Key) const;
    UPROPERTY(BlueprintReadOnly, Transient, Category="Carry") ECarryState State = ECarryState::Idle;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float CharacterWeightKg = 50;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float LiftWeightRatio = .2f;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float Reach = 160;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float MaxThrowDistance = 800;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float MinFlightTime = .4f;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float MaxFlightTime = 1.3f;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") FName CarrySocket = "spine_03";
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") FName WeaponComponentName = "Sword";
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") FTransform ReleaseOffset = FTransform(FRotator::ZeroRotator, FVector(65,0,30));
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") TObjectPtr<UAnimMontage> PickupMontage;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") TObjectPtr<UAnimMontage> PlaceMontage;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") TObjectPtr<UAnimMontage> ThrowMontage;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") TObjectPtr<UAnimMontage> HoldMontage;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") TObjectPtr<UAnimMontage> AimMontage;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") TObjectPtr<UMaterialInterface> PreviewMaterial;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float PickupPlayRate = 2.f;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float PlacePlayRate = 2.f;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float ThrowPlayRate = 1.f;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float PickupContactTime = .45f;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float PickupDuration = .9f;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float PlaceContactTime = .55f;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float PlaceDuration = 1.f;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float ThrowContactTime = .25f;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float ThrowDuration = .65f;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") float NoticeDuration = 2.f;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category="Carry|Resolved") TObjectPtr<UStringTable> Messages = nullptr;
    UPROPERTY(BlueprintAssignable, Category="Carry") FCarryStateChanged OnStateChanged;
    UPROPERTY(BlueprintAssignable, Category="Carry") FCarryMessage OnMessage;
    UPROPERTY(BlueprintReadOnly, Transient, Category="Carry") bool bAimValid = false;
    UPROPERTY(BlueprintReadOnly, Transient, Category="Carry") FVector AimLocation = FVector::ZeroVector;
    UFUNCTION(BlueprintCallable, Category="Carry") bool TryPickUp(UHoldableComponent* Item);
    UFUNCTION(BlueprintCallable, Category="Carry") bool TryPlace();
    UFUNCTION(BlueprintCallable, Category="Carry") bool BeginAim();
    UFUNCTION(BlueprintCallable, Category="Carry") void CancelAim();
    UFUNCTION(BlueprintCallable, Category="Carry") bool CommitThrow();
    UFUNCTION(BlueprintCallable, Category="Carry") void OnPickupContact();
    UFUNCTION(BlueprintCallable, Category="Carry") void OnPlaceRelease();
    UFUNCTION(BlueprintCallable, Category="Carry") void OnThrowRelease();
    UFUNCTION(BlueprintCallable, Category="Carry") void FinishAction();
    UFUNCTION(BlueprintCallable, Category="Carry") void AbortCarry();
    UFUNCTION(BlueprintPure, Category="Carry") bool BlocksOtherActions() const { return State != ECarryState::Idle; }
    UFUNCTION(BlueprintPure, Category="Carry") bool AllowsWalking() const;
    UFUNCTION(BlueprintPure, Category="Carry") AActor* GetHeldActor() const;
    UFUNCTION(BlueprintPure, Category="Carry") FTransform GetHandGrip(bool bLeft) const;
    UFUNCTION(BlueprintCallable, Category="Carry") bool HandleInteract();
    UFUNCTION(BlueprintPure, Category="Carry") UHoldableComponent* FindInteractionItem() const;
    UFUNCTION(BlueprintPure, Category="Carry") bool CanPickUp(const UHoldableComponent* Item) const;
    UFUNCTION(BlueprintPure, Category="Carry") bool CanPlace() const;
    UFUNCTION(BlueprintCallable, Category="Carry") void UpdateAim();
protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
private:
    friend class FCarryPlacementTest;
    UPROPERTY(Transient) TObjectPtr<UHoldableComponent> HeldItem;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> PreviewMesh;
    UPROPERTY(Transient) TObjectPtr<UCarryNoticeWidget> Notice;
    UPROPERTY(Transient) TObjectPtr<UAnimMontage> ActiveMontage;
    void SetState(ECarryState Next);
    void StartAction(UAnimMontage* Montage, float ContactTime, float Duration, float PlayRate = 1.f);
    void ReleaseHeld(const FTransform& Transform, const FVector& Velocity, float Spin);
    bool CanReachItem(const UHoldableComponent* Item) const;
    bool FindPlace(FTransform& Transform) const;
    bool IsSpaceFree(const FTransform& Transform, bool bIncludeCarrier = false, bool bLaunching = false) const;
    bool IsPathFree(const FVector& Start, const FVector& End, const FQuat& Rotation, FHitResult& Hit) const;
    FTransform GetReleaseTransform() const;
    void ShowFailure(const FText& Message);
    void ClearPreview();
    void AttachToCarryPosition();
    void AttachToActionHand();
    void OnMontageFinished(UAnimMontage* Montage, bool bInterrupted);
    void PlayLoop(UAnimMontage* Montage);
    UFUNCTION() void OnOwnerDamaged(AActor* Actor, float Damage, const UDamageType* Type, AController* Instigator, AActor* Causer);
    FTimerHandle ContactTimer, FinishTimer;
    FTransform PlaceTransform;
    FVector ThrowVelocity = FVector::ZeroVector;
    FVector LocalCenterOfMass = FVector::ZeroVector;
    float ThrowTime = 1;
    float ThrowSpin = 0;
    bool bSavedPhysics = false;
    bool bSavedGravity = true;
    bool bContactOccurred = false;
    bool bAborting = false;
    FTransform OriginalItemTransform;
    bool bHasLifted = false;
    TWeakObjectPtr<USceneComponent> WeaponVisual;
    bool bSavedWeaponVisible=false;
    ECollisionEnabled::Type SavedCollision = ECollisionEnabled::QueryAndPhysics;
};
