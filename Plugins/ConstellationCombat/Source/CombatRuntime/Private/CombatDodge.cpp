#include "CombatAbilitySystem.h"
#include "CombatAttributes.h"
#include "CombatActionDefinition.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/RootMotionSource.h"

bool UCombatAbilitySystem::IsDodgeCancelWindowOpen() const
{
    if(!IsActing() || !ActiveAction || !ActiveAction->bAllowDodgeCancel) return false;
    FString Reason;if(!ActiveAction->Validate(Reason)) return false;
    const auto* Character=Cast<ACharacter>(GetAvatarActor());
    auto* Anim=Character?Character->GetMesh()->GetAnimInstance():nullptr;
    const auto* Instance=Anim?Anim->GetActiveInstanceForMontage(ActiveAction->Montage):nullptr;
    return Instance && MatchesMontageInstance(Instance->GetInstanceID()) &&
        Instance->GetPosition()>=ActiveAction->DodgeCancelStart && Instance->GetPosition()<ActiveAction->DodgeCancelEnd;
}
bool UCombatAbilitySystem::IsInvulnerable() const
{
    return bDodging && DodgeElapsed>=ActiveInvulnerableStart && DodgeElapsed<ActiveInvulnerableEnd;
}
bool UCombatAbilitySystem::TryDodge(FVector Direction)
{
    if(!bInitialized || !GetOwner() || !GetOwner()->HasAuthority() || bDead || GetHealth()<=0)
        { LastReason=TEXT("Cannot dodge: inactive or dead"); return false; }
    if(bCommittingResources || bDodging || bStartingDodge || IsHitReacting() || bResolvingDamage)
        { LastReason=TEXT("Cannot dodge during another action"); return false; }
    if(!AllowsExternalAction(LastReason)) return false;
    if(IsActing() && !IsDodgeCancelWindowOpen())
        {LastReason=TEXT("Dodge cancel window closed");return false;}
    if(!FMath::IsFinite(DodgeDuration) || DodgeDuration<=0 || !FMath::IsFinite(DodgeDistance) || DodgeDistance<=0 ||
        !FMath::IsFinite(DodgeStaminaCost) || DodgeStaminaCost<0 || !FMath::IsFinite(DodgeInvulnerableStart) ||
        !FMath::IsFinite(DodgeInvulnerableEnd) || DodgeInvulnerableStart<0 || DodgeInvulnerableEnd<=DodgeInvulnerableStart || DodgeInvulnerableEnd>DodgeDuration)
        { LastReason=TEXT("Invalid dodge settings"); return false; }
    if(GetStamina()<DodgeStaminaCost) { LastReason=TEXT("Not enough stamina"); return false; }
    auto* Character=Cast<ACharacter>(GetAvatarActor());
    auto* Movement=Character?Character->GetCharacterMovement():nullptr;
    if(!Movement || !Movement->IsMovingOnGround()) { LastReason=TEXT("Dodge requires ground"); return false; }
    if(Direction.ContainsNaN()) { LastReason=TEXT("Invalid dodge direction"); return false; }
    Direction=Direction.GetSafeNormal2D();
    if(Direction.IsNearlyZero()) Direction=Character->GetActorForwardVector().GetSafeNormal2D();
    // Snapshot before cancellation callbacks; guard both attack and dodge starts during handoff.
    const float Cost=DodgeStaminaCost,Duration=DodgeDuration,Distance=DodgeDistance;
    const float InvulnerableStart=DodgeInvulnerableStart,InvulnerableEnd=DodgeInvulnerableEnd;
    TGuardValue<bool> StartingDodge(bStartingDodge,true);
    if(IsActing())
    {
        CancelAction();
        if(!IsValid(Character) || !IsValid(Movement) || bDead || GetHealth()<=0 || IsActing() ||
            IsHitReacting() || bResolvingDamage || !Movement->IsMovingOnGround() || GetStamina()<Cost)
            {LastReason=TEXT("Dodge transition interrupted");return false;}
    }
    auto Motion=MakeShared<FRootMotionSource_ConstantForce>();
    Motion->InstanceName=TEXT("CombatDodge"); Motion->Priority=500;
    Motion->AccumulateMode=ERootMotionAccumulateMode::Override;
    Motion->Duration=Duration; Motion->Force=Direction*(Distance/Duration);
    Motion->Settings.SetFlag(ERootMotionSourceSettingsFlags::IgnoreZAccumulate);
    DodgeMotionId=Movement->ApplyRootMotionSource(Motion);
    if(DodgeMotionId==0) { LastReason=TEXT("Dodge movement failed"); return false; }
    bDodging=true; const uint64 Ticket=++DodgeSerial;
    DodgeElapsed=0; ActiveDodgeDuration=Duration;
    ActiveInvulnerableStart=InvulnerableStart; ActiveInvulnerableEnd=InvulnerableEnd;
    RecoveryDelayRemaining=FMath::IsFinite(StaminaRecoveryDelay)?FMath::Max(0.f,StaminaRecoveryDelay):1.f;
    Character->ConsumeMovementInputVector(); Movement->StopMovementImmediately();
    Character->SetActorRotation(FRotator(0,Direction.Rotation().Yaw,0));
    LastReason=TEXT("Dodge started");
    OnDodgeStarted.Broadcast();
    ModifyAttribute(UCombatAttributes::GetStaminaAttribute(),-Cost,GetOwner());
    return bDodging && DodgeSerial==Ticket;
}
void UCombatAbilitySystem::CancelDodge()
{
    if(!bDodging) return;
    bDodging=false;
    if(auto* Character=Cast<ACharacter>(GetAvatarActor()))
    {
        auto* Movement=Character->GetCharacterMovement();
        Movement->RemoveRootMotionSourceByID(DodgeMotionId);
        Movement->Velocity=FVector(0,0,Movement->Velocity.Z);
        Character->ConsumeMovementInputVector();
    }
    DodgeMotionId=0;
}
