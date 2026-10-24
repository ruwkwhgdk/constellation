#include "PlayerFallAnimationComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/World.h"

UPlayerFallAnimationComponent::UPlayerFallAnimationComponent()
{
 PrimaryComponentTick.bCanEverTick=true;
 PrimaryComponentTick.TickGroup=TG_PostPhysics;
}
void UPlayerFallAnimationComponent::BeginPlay()
{
 Super::BeginPlay();Character=Cast<ACharacter>(GetOwner());Fall=GetOwner()->FindComponentByClass<UPlayerFallComponent>();
 if(auto* F=Fall.Get()){AddTickPrerequisiteComponent(F);F->OnLanding.AddDynamic(this,&UPlayerFallAnimationComponent::HandleLanding);}
}
UAnimInstance* UPlayerFallAnimationComponent::ResolveAnim()
{
 auto* C=Character.Get();auto* A=C&&C->GetMesh()?C->GetMesh()->GetAnimInstance():nullptr;
 BoundAnim=A;
 return A;
}
void UPlayerFallAnimationComponent::RememberBounds()
{
 if(!bBoundsChanged)if(auto* C=Character.Get())
 {PreviousBounds=C->GetMesh()->BoundsScale;C->GetMesh()->SetBoundsScale(FMath::Max(PreviousBounds,4.f));bBoundsChanged=true;}
}
void UPlayerFallAnimationComponent::StopOwned(float Blend)
{
 ++PlaybackGeneration;
 auto* Old=ActiveMontage.Get();ActiveMontage=nullptr;PlaybackPhase=NAME_None;
 if(auto* A=BoundAnim.Get();A&&Old)A->Montage_Stop(Blend,Old);
 if(bBoundsChanged)if(auto* C=Character.Get())C->GetMesh()->SetBoundsScale(PreviousBounds);
 bBoundsChanged=false;
}
void UPlayerFallAnimationComponent::CancelFallAnimation()
{
 const int32 Id=RecoveryId;RecoveryId=INDEX_NONE;StopOwned(.12f);bTracking=false;
 if(auto* F=Fall.Get();F&&Id!=INDEX_NONE)F->FinishLanding(Id);
}
void UPlayerFallAnimationComponent::EndPlay(const EEndPlayReason::Type Reason)
{
 CancelFallAnimation();
 if(auto* F=Fall.Get())F->OnLanding.RemoveDynamic(this,&UPlayerFallAnimationComponent::HandleLanding);
 Super::EndPlay(Reason);
}
void UPlayerFallAnimationComponent::TickComponent(float Dt,ELevelTick Type,FActorComponentTickFunction* Tick)
{
 Super::TickComponent(Dt,Type,Tick);auto* C=Character.Get();auto* F=Fall.Get();if(!C||!F)return;
 if(F->State!=EPlayerFallState::Falling)
 {
  bTracking=false;
  if(F->State!=EPlayerFallState::Recovering&&ActiveMontage)CancelFallAnimation();
  return;
 }
 const double Feet=C->GetActorLocation().Z-C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
 if(!bTracking){PeakFeet=Feet;bTracking=true;RecoveryId=INDEX_NONE;}
 PeakFeet=FMath::Max(PeakFeet,Feet);
 if(C->GetVelocity().Z>=0)return;
 // Choose the airborne pose before impact, using the floor below the capsule.
 // Damage and the actual landing tier remain owned by PlayerFallComponent.
 const double Drop=PeakFeet-Feet;
 double ExpectedDrop=Drop;
 FHitResult Floor;
 FCollisionQueryParams Query(SCENE_QUERY_STAT(FallAnimationFloor),false,C);
 const FVector Start=C->GetActorLocation();
 if(GetWorld()->LineTraceSingleByChannel(Floor,Start,Start-FVector(0,0,50000),ECC_Visibility,Query)
    && Floor.ImpactNormal.Z>=C->GetCharacterMovement()->GetWalkableFloorZ())
  ExpectedDrop=FMath::Max(Drop,PeakFeet-Floor.ImpactPoint.Z);
 const auto Tier=F->EvaluateLanding(ExpectedDrop).Tier;
 if(Tier==EPlayerLandingTier::None)return;
 auto* A=ResolveAnim();if(!A)return;
 const bool Strong=Tier==EPlayerLandingTier::Strong;
 const FName Phase=Strong?TEXT("StrongAirborne"):TEXT("Airborne");
 if(PlaybackPhase!=Phase)
 {
  UAnimSequence* Seq=Strong?StrongAirborne.Get():AirborneLoop.Get();if(!Seq)return;
  StopOwned(.15f);RememberBounds();
  UAnimMontage* Montage=UAnimMontage::CreateSlotAnimationAsDynamicMontage(Seq,TEXT("FallFullBody"),.18f,.12f,1.f,Strong?1:1000);
  if(!Montage){StopOwned(0);return;}
  Montage->bEnableAutoBlendOut=!Strong;
  if(A->Montage_Play(Montage,1.f,EMontagePlayReturnType::Duration,0.f,false)<=0){StopOwned(0);return;}
  ActiveMontage=Montage;PlaybackPhase=Phase;BindCompletion(A,Montage);
 }
}
void UPlayerFallAnimationComponent::HandleLanding(const FPlayerLandingResult& R)
{
 bTracking=false;RecoveryId=INDEX_NONE;StopOwned(.10f);
 UAnimMontage* Selected=R.Tier==EPlayerLandingTier::Normal?NormalLanding.Get():R.Tier==EPlayerLandingTier::Weak?WeakLanding.Get():R.Tier==EPlayerLandingTier::Strong?StrongLanding.Get():nullptr;
 auto* A=ResolveAnim();auto* F=Fall.Get();if(!Selected||!A||!F)return;
 RememberBounds();const float Length=A->Montage_Play(Selected,1.f,EMontagePlayReturnType::Duration,0.f,false);
 if(Length<=0){StopOwned(0);return;}
 ActiveMontage=Selected;RecoveryId=R.LandingId;PlaybackPhase=R.Tier==EPlayerLandingTier::Strong?TEXT("StrongRecovery"):R.Tier==EPlayerLandingTier::Weak?TEXT("WeakLanding"):TEXT("NormalLanding");
 // Completion owns the release; the fall component supplies a bounded fallback.
 F->SetLandingRecoveryDuration(RecoveryId,Length+.5f);
 BindCompletion(A,Selected);
}
void UPlayerFallAnimationComponent::BindCompletion(UAnimInstance* Anim,UAnimMontage* Montage)
{
 const uint64 Generation=PlaybackGeneration;
 FOnMontageEnded End;
 End.BindWeakLambda(this,[this,Generation](UAnimMontage* Ended,bool Interrupted)
 {HandleMontageEnded(Ended,Interrupted,Generation);});
 Anim->Montage_SetEndDelegate(End,Montage);
}
void UPlayerFallAnimationComponent::HandleMontageEnded(UAnimMontage* Montage,bool,uint64 Generation)
{
 if(Generation!=PlaybackGeneration||Montage!=ActiveMontage)return;
 const int32 Id=RecoveryId;RecoveryId=INDEX_NONE;StopOwned(0);
 if(auto* F=Fall.Get();F&&Id!=INDEX_NONE)F->FinishLanding(Id);
}
