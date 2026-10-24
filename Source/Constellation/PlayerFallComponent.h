#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "FallMath.h"
#include "PlayerFallComponent.generated.h"

UENUM(BlueprintType)
enum class EPlayerLandingTier : uint8 { None, Normal, Weak, Strong };
UENUM(BlueprintType)
enum class EPlayerFallState : uint8 { Grounded, Falling, Recovering };
USTRUCT(BlueprintType)
struct FPlayerLandingResult
{
 GENERATED_BODY()
 UPROPERTY(BlueprintReadOnly) int32 LandingId=0;
 UPROPERTY(BlueprintReadOnly) EPlayerLandingTier Tier=EPlayerLandingTier::None;
 UPROPERTY(BlueprintReadOnly) float HeightCm=0;
 UPROPERTY(BlueprintReadOnly) double DamageRatio=0;
 UPROPERTY(BlueprintReadOnly) double CalculatedDamage=0;
 UPROPERTY(BlueprintReadOnly) double AppliedDamage=0;
};
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FPlayerLandingEvent,const FPlayerLandingResult&,Result);

// Add only to playable characters. Animation/VFX consumers subscribe to OnLanding.
UCLASS(ClassGroup=(Player),meta=(BlueprintSpawnableComponent))
class CONSTELLATION_API UPlayerFallComponent : public UActorComponent
{
 GENERATED_BODY()
public:
 UPlayerFallComponent();
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Fall|Height",meta=(ClampMin="1",Units="cm")) float ReferenceHeight=160;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Fall|Height",meta=(ClampMin="0.01")) float NormalHeightMultiplier=2;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Fall|Height",meta=(ClampMin="0.01")) float WeakHeightMultiplier=6;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Fall|Height",meta=(ClampMin="0.01")) float StrongHeightMultiplier=12;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Fall|Height",meta=(ClampMin="0.01")) float MaximumDamageHeightMultiplier=24;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Fall|Recovery",meta=(ClampMin="0",ClampMax="30",Units="s")) float NormalRecoverySeconds=.2f;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Fall|Recovery",meta=(ClampMin="0",ClampMax="30",Units="s")) float WeakRecoverySeconds=.45f;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Fall|Recovery",meta=(ClampMin="0",ClampMax="30",Units="s")) float StrongRecoverySeconds=.8f;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Fall") EPlayerFallState State=EPlayerFallState::Grounded;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Fall") FPlayerLandingResult LastLanding;
 UPROPERTY(BlueprintAssignable,Category="Fall") FPlayerLandingEvent OnLanding;
 UFUNCTION(BlueprintPure,Category="Fall") bool IsLandingLocked() const { return State==EPlayerFallState::Recovering; }
 UFUNCTION(BlueprintPure,Category="Fall") FPlayerLandingResult EvaluateLanding(float HeightCm) const;
 // Cinematics, custom locomotion and respawn can explicitly cancel and suspend tracking.
 UFUNCTION(BlueprintCallable,Category="Fall") void SetFallSuspended(bool bSuspend);
 UFUNCTION(BlueprintCallable,Category="Fall") void ResetFall();
 // Animation completion must pass its landing id; late callbacks cannot release a newer landing.
 UFUNCTION(BlueprintCallable,Category="Fall") void FinishLanding(int32 LandingId);
 // Call from OnLanding when a montage starts; keep a finite watchdog for missing completion callbacks.
 UFUNCTION(BlueprintCallable,Category="Fall") void SetLandingRecoveryDuration(int32 LandingId,float Seconds);
 virtual void Deactivate() override;
 virtual void TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction) override;
protected:
 virtual void BeginPlay() override;
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
 UFUNCTION() void MovementChanged(ACharacter* Character,EMovementMode Previous,uint8 PreviousCustom);
 UFUNCTION() void Landed(const FHitResult& Hit);
 bool CanTrack() const;
 double FeetHeight() const;
 void StartFall();
 void ReleaseLock();
 void ApplyLandingDamage();
 TWeakObjectPtr<ACharacter> OwnerCharacter;
 TWeakObjectPtr<AController> ObservedController;
 TWeakObjectPtr<AController> LockedController;
 FallMath::Tracker Tracker;
 FTimerHandle RecoveryTimer;
 int32 Generation=0;
 bool bSuspended=false;
};
