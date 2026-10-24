#include "PlayerFallComponent.h"
#include "CarryComponent.h"
#include "StarlightPlayerHUDWidget.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "UObject/UnrealType.h"

UPlayerFallComponent::UPlayerFallComponent()
{
 PrimaryComponentTick.bCanEverTick=true;
 bAutoActivate=true;
 PrimaryComponentTick.TickGroup=TG_PostPhysics;
}
void UPlayerFallComponent::BeginPlay()
{
 Super::BeginPlay();OwnerCharacter=Cast<ACharacter>(GetOwner());
 if(auto* C=OwnerCharacter.Get())
 {
  ObservedController=C->GetController();
  AddTickPrerequisiteComponent(C->GetCharacterMovement());
  C->MovementModeChangedDelegate.AddDynamic(this,&UPlayerFallComponent::MovementChanged);
  C->LandedDelegate.AddDynamic(this,&UPlayerFallComponent::Landed);
  if(CanTrack()&&C->GetCharacterMovement()->IsFalling())StartFall();
 }
}
void UPlayerFallComponent::EndPlay(const EEndPlayReason::Type Reason)
{
 ResetFall();
 if(auto* C=OwnerCharacter.Get())
 {
  C->MovementModeChangedDelegate.RemoveDynamic(this,&UPlayerFallComponent::MovementChanged);
  C->LandedDelegate.RemoveDynamic(this,&UPlayerFallComponent::Landed);
 }
 Super::EndPlay(Reason);
}
void UPlayerFallComponent::Deactivate(){ResetFall();Super::Deactivate();}
bool UPlayerFallComponent::CanTrack() const
{
 auto* C=OwnerCharacter.Get();if(!C||!IsActive()||bSuspended||!C->GetController())return false;
 if(const auto* PC=Cast<APlayerController>(C->GetController());PC&&PC->bCinematicMode)return false;
 if(C->GetController()->IsMoveInputIgnored()&&!IsLandingLocked())return false;
 return true;
}
double UPlayerFallComponent::FeetHeight() const
{
 auto* C=OwnerCharacter.Get();return C?C->GetActorLocation().Z-C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight():0;
}
void UPlayerFallComponent::StartFall()
{
 ReleaseLock();Tracker.Begin(FeetHeight());State=EPlayerFallState::Falling;
}
void UPlayerFallComponent::MovementChanged(ACharacter* C,EMovementMode,uint8)
{
 if(!CanTrack()){ResetFall();return;}
 auto* M=C->GetCharacterMovement();
 if(M->IsFalling()){StartFall();return;}
 // Walking after Landed must not cancel the newly acquired recovery lock.
 if(!M->IsMovingOnGround()||State==EPlayerFallState::Falling)ResetFall();
}
void UPlayerFallComponent::TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* Tick)
{
 Super::TickComponent(DeltaTime,TickType,Tick);
 auto* C=OwnerCharacter.Get();if(!C)return;
 if(ObservedController!=C->GetController()){ResetFall();ObservedController=C->GetController();}
 if(!CanTrack()){ResetFall();return;}
 auto* M=C->GetCharacterMovement();
 if(M->IsFalling())
 {
  if(State!=EPlayerFallState::Falling)StartFall();
  Tracker.Sample(FeetHeight());
 }
 else if(!M->IsMovingOnGround())ResetFall();
}
FPlayerLandingResult UPlayerFallComponent::EvaluateLanding(float HeightCm) const
{
 const auto R=FallMath::Evaluate(HeightCm,{ReferenceHeight,NormalHeightMultiplier,WeakHeightMultiplier,StrongHeightMultiplier,MaximumDamageHeightMultiplier});
 FPlayerLandingResult Result;Result.HeightCm=FMath::IsFinite(HeightCm)?FMath::Max(0.f,HeightCm):0;
 Result.Tier=static_cast<EPlayerLandingTier>(R.Tier);Result.DamageRatio=R.DamageRatio;return Result;
}
void UPlayerFallComponent::Landed(const FHitResult&)
{
 if(!CanTrack()){ResetFall();return;}
 double Height=0;if(!Tracker.Land(FeetHeight(),Height))return;
 LastLanding=EvaluateLanding(Height);LastLanding.LandingId=++Generation;
 State=EPlayerFallState::Grounded;
 if(LastLanding.Tier!=EPlayerLandingTier::None)
 {
  State=EPlayerFallState::Recovering;
  auto* C=OwnerCharacter.Get();LockedController=C->GetController();
  if(auto* PC=LockedController.Get())PC->SetIgnoreMoveInput(true);
  C->StopJumping();C->ConsumeMovementInputVector();C->GetCharacterMovement()->StopMovementImmediately();
  const float Duration=LastLanding.Tier==EPlayerLandingTier::Normal?NormalRecoverySeconds:LastLanding.Tier==EPlayerLandingTier::Weak?WeakRecoverySeconds:StrongRecoverySeconds;
  SetLandingRecoveryDuration(LastLanding.LandingId,Duration);
 }
 ApplyLandingDamage();
 OnLanding.Broadcast(LastLanding);
}
void UPlayerFallComponent::ApplyLandingDamage()
{
 // Environmental damage intentionally bypasses combat defense, invincibility and death dispatch.
 // The legacy HUD already observes Ac_Stats. Do not call the generic TakeDamage graph here.
 UObject* Stats=nullptr;
 TInlineComponentArray<UActorComponent*> Components(GetOwner());
 for(auto* Component:Components)
  if(Component->GetClass()->GetName()==TEXT("Ac_Stats_C")){Stats=Component;break;}
 if(!Stats)return;
 auto* HP=FindFProperty<FNumericProperty>(Stats->GetClass(),TEXT("CurrentHP"));
 auto* Max=FindFProperty<FNumericProperty>(Stats->GetClass(),TEXT("MaxHP"));
 if(!HP||!Max||!HP->IsFloatingPoint()||!Max->IsFloatingPoint())return;
 void* HPValue=HP->ContainerPtrToValuePtr<void>(Stats);
 const double Current=HP->GetFloatingPointPropertyValue(HPValue);
 const double Maximum=Max->GetFloatingPointPropertyValue(Max->ContainerPtrToValuePtr<void>(Stats));
 if(!FMath::IsFinite(Maximum)||Maximum<=0)return;
 LastLanding.CalculatedDamage=Maximum*LastLanding.DamageRatio;
 const double Applied=FallMath::AppliedDamage(Maximum,Current,LastLanding.DamageRatio);
 LastLanding.AppliedDamage=Applied;
 if(Applied<=0)return;
 HP->SetFloatingPointPropertyValue(HPValue,FMath::Max(1.0,Current-Applied));
 UStarlightPlayerHUDWidget::NotifyDamage(GetOwner());
 if(auto* Carry=GetOwner()->FindComponentByClass<UCarryComponent>())Carry->AbortCarry();
 if(auto* Event=FindFProperty<FMulticastDelegateProperty>(Stats->GetClass(),TEXT("OnHPChanged")))
 {
  // Ac_Stats.OnHPChanged has no parameters; do not invoke incompatible future signatures.
  if(Event->SignatureFunction&&Event->SignatureFunction->NumParms==0)
   Event->GetMulticastDelegate(Event->ContainerPtrToValuePtr<void>(Stats))->ProcessDelegate<UObject>(nullptr);
 }
}
void UPlayerFallComponent::ReleaseLock()
{
 if(GetWorld())GetWorld()->GetTimerManager().ClearTimer(RecoveryTimer);
 if(auto* PC=LockedController.Get())PC->SetIgnoreMoveInput(false);
 LockedController.Reset();
 if(State==EPlayerFallState::Recovering)State=EPlayerFallState::Grounded;
}
void UPlayerFallComponent::ResetFall(){ReleaseLock();Tracker.Reset();State=EPlayerFallState::Grounded;++Generation;}
void UPlayerFallComponent::SetFallSuspended(bool Suspend){bSuspended=Suspend;if(Suspend)ResetFall();}
void UPlayerFallComponent::FinishLanding(int32 Id){if(IsLandingLocked()&&Id==Generation)ReleaseLock();}
void UPlayerFallComponent::SetLandingRecoveryDuration(int32 Id,float Seconds)
{
 if(!IsLandingLocked()||Id!=Generation||!GetWorld())return;
 if(!FMath::IsFinite(Seconds))Seconds=.8f;
 if(Seconds<=0){FinishLanding(Id);return;}
 FTimerDelegate Done;Done.BindWeakLambda(this,[this,Id]{FinishLanding(Id);});
 GetWorld()->GetTimerManager().SetTimer(RecoveryTimer,Done,FMath::Min(Seconds,30.f),false);
}
