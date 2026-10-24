#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "PlayerFallComponent.h"
#include "PlayerFallAnimationComponent.generated.h"

class UAnimInstance;
class UAnimSequence;
class UAnimMontage;
class ACharacter;

UCLASS(ClassGroup=(Player),meta=(BlueprintSpawnableComponent))
class CONSTELLATION_API UPlayerFallAnimationComponent : public UActorComponent
{
 GENERATED_BODY()
public:
 UPlayerFallAnimationComponent();
 UPROPERTY(EditAnywhere,Category="Fall|Animation") TObjectPtr<UAnimSequence> AirborneLoop;
 UPROPERTY(EditAnywhere,Category="Fall|Animation") TObjectPtr<UAnimSequence> StrongAirborne;
 UPROPERTY(EditAnywhere,Category="Fall|Animation") TObjectPtr<UAnimMontage> NormalLanding;
 UPROPERTY(EditAnywhere,Category="Fall|Animation") TObjectPtr<UAnimMontage> WeakLanding;
 UPROPERTY(EditAnywhere,Category="Fall|Animation") TObjectPtr<UAnimMontage> StrongLanding;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Fall|Animation") FName PlaybackPhase=NAME_None;
 UFUNCTION(BlueprintPure,Category="Fall|Animation") bool IsAnimationActive() const {return ActiveMontage!=nullptr;}
 UFUNCTION(BlueprintCallable,Category="Fall|Animation") void CancelFallAnimation();
 virtual void TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* Tick) override;
protected:
 virtual void BeginPlay() override;
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
 UFUNCTION() void HandleLanding(const FPlayerLandingResult& Result);
 void HandleMontageEnded(UAnimMontage* Montage,bool Interrupted,uint64 Generation);
 void BindCompletion(UAnimInstance* Anim,UAnimMontage* Montage);
 UAnimInstance* ResolveAnim();
 void StopOwned(float Blend);
 void RememberBounds();
 TWeakObjectPtr<ACharacter> Character;
 TWeakObjectPtr<UPlayerFallComponent> Fall;
 TWeakObjectPtr<UAnimInstance> BoundAnim;
 UPROPERTY(Transient) TObjectPtr<UAnimMontage> ActiveMontage;
 uint64 PlaybackGeneration=0;
 double PeakFeet=0;
 float PreviousBounds=1;
 int32 RecoveryId=INDEX_NONE;
 bool bTracking=false;
 bool bBoundsChanged=false;
};
