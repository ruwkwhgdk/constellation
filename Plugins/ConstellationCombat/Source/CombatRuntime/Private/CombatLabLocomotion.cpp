#include "CombatLabCharacter.h"
#include "CombatAbilitySystem.h"
#include "CombatHitReactionComponent.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "EngineUtils.h"
#include "DrawDebugHelpers.h"

bool ACombatLabCharacter::CanLockTarget(const ACombatLabCharacter* Target, float Range) const
{
    if (!IsValid(Target) || Target==this || Combat->GetHealth()<=0 ||
        Target->Combat->GetHealth()<=0 || Target->Combat->TeamId==Combat->TeamId ||
        FVector::DistSquared(GetActorLocation(),Target->GetActorLocation())>FMath::Square(Range)) return false;
    FHitResult Hit;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(CombatLock),false,this);
    const bool Blocked=GetWorld()->LineTraceSingleByChannel(Hit,GetActorLocation(),Target->GetActorLocation(),ECC_Visibility,Params);
    return !Blocked || Hit.GetActor()==Target;
}
void ACombatLabCharacter::ToggleTargetLock()
{
    if(bWorkbenchOpen) return;
    if (LockedTarget.IsValid()) { LockedTarget.Reset(); return; }
    auto* PC=Cast<APlayerController>(GetController());
    if (!PC) return;
    const FVector Forward=FRotator(0,PC->GetControlRotation().Yaw,0).Vector();
    float Best=-1.f;
    for(TActorIterator<ACombatLabCharacter> It(GetWorld());It;++It)
    {
        if(!CanLockTarget(*It,900.f)) continue;
        const FVector Offset=It->GetActorLocation()-GetActorLocation();
        const float Alignment=FVector::DotProduct(Forward,Offset.GetSafeNormal2D());
        if(Alignment<.35f) continue;
        const float Score=Alignment-Offset.Size()*.0002f;
        if(Score>Best) { Best=Score; LockedTarget=*It; }
    }
}
void ACombatLabCharacter::UpdateTargetLock(float Delta)
{
    ACombatLabCharacter* Target=LockedTarget.Get();
    if (!Target) return;
    if (!CanLockTarget(Target,1100.f)) { LockedTarget.Reset(); return; }
    if (auto* PC=Cast<APlayerController>(GetController()))
    {
        const FRotator Desired(-20.f,(Target->GetActorLocation()-GetActorLocation()).Rotation().Yaw,0);
        PC->SetControlRotation(FMath::RInterpTo(PC->GetControlRotation(),Desired,Delta,8.f));
    }
    DrawDebugSphere(GetWorld(),Target->GetActorLocation()+FVector(0,0,95),12,12,FColor::Cyan,false,0,0,2);
}
void ACombatLabCharacter::UpdateLocomotion()
{
    if(Combat->IsActing() || Combat->GetHealth()<=0 || HitReaction->IsPresenting()) return;
    UAnimSingleNodeInstance* Single=GetMesh()->GetSingleNodeInstance();
    if(!Single) return;
    const float Speed=GetVelocity().Size2D();
    UAnimSequence* Clip=!Combat->IsDodging() && Speed>3.f && MoveAnimation ? MoveAnimation.Get() : IdleAnimation.Get();
    if(!Clip) return;
    if(Single->GetCurrentAsset()!=Clip) Single->SetAnimationAsset(Clip,true,1.f);
    Single->SetPlayRate(Clip==MoveAnimation ? FMath::Max(.1f,Speed/FMath::Max(1.f,AnimationMoveSpeed)) : 1.f);
    Single->SetPlaying(true);
}
