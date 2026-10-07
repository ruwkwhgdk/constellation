#include "CombatAbilitySystem.h"
#include "CombatAttributes.h"
#include "CombatEncounterDirector.h"
#include "CombatLabCharacter.h"
#include "CombatActionDefinition.h"
#include "CombatActionAbility.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/Skeleton.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "DrawDebugHelpers.h"
#include "GameplayEffect.h"
#include "GameFramework/RootMotionSource.h"
#include "Engine/OverlapResult.h"

UCombatAbilitySystem::UCombatAbilitySystem()
{

    SetIsReplicatedByDefault(false);
}
void UCombatAbilitySystem::InitializeCombat(AActor* Actor)
{
    if (bInitialized || !IsValid(Actor)) return;
    Attributes = NewObject<UCombatAttributes>(Actor, TEXT("CombatAttributes"));
    Attributes->InitializeResources(MaxHealth, MaxStamina);
    MaxHealth = Attributes->GetMaxHealth();
    MaxStamina = Attributes->GetMaxStamina();
    InitAbilityActorInfo(Actor, Actor);
    AddAttributeSetSubobject(Attributes.Get());
    bInitialized = true;
    UpdateShouldTick();
}
void UCombatAbilitySystem::ResetAfterReturn()
{
    if(!bInitialized || bDead || GetHealth()<=0 || !GetOwner()->HasAuthority()) return;
    TGuardValue<bool> Resetting(bResolvingDamage,true);
    CancelAction(); OnHitReceived.Broadcast();
    HitReactionRemaining=0; RecoveryDelayRemaining=0; Cooldowns.Reset();
    ModifyAttribute(UCombatAttributes::GetHealthAttribute(),GetMaxHealth()-GetHealth(),GetOwner());
    ModifyAttribute(UCombatAttributes::GetStaminaAttribute(),GetMaxStamina()-GetStamina(),GetOwner());
    ModifyAttribute(UCombatAttributes::GetUltimateChargeAttribute(),-GetUltimateCharge(),GetOwner());
    LastReason=TEXT("Encounter reset"); LastPatternDecision.Reset(); LastSelectedPattern=NAME_None;
}
float UCombatAbilitySystem::GetUltimateCharge() const {return Attributes?Attributes->GetUltimateCharge():0.f;}
float UCombatAbilitySystem::GetHealth() const { return Attributes ? Attributes->GetHealth() : GetMaxHealth(); }
float UCombatAbilitySystem::GetStamina() const { return Attributes ? Attributes->GetStamina() : GetMaxStamina(); }
float UCombatAbilitySystem::GetMaxHealth() const { return Attributes ? Attributes->GetMaxHealth() : (FMath::IsFinite(MaxHealth) && MaxHealth > 0.f ? MaxHealth : 100.f); }
float UCombatAbilitySystem::GetMaxStamina() const { return Attributes ? Attributes->GetMaxStamina() : (FMath::IsFinite(MaxStamina) && MaxStamina > 0.f ? MaxStamina : 100.f); }
bool UCombatAbilitySystem::CanStart(const UCombatActionDefinition* Action, FString& Reason) const
{
    if (!bInitialized || !GetOwner() || !GetOwner()->HasAuthority()) { Reason = TEXT("Not initialized or not authority"); return false; }
    if (bCommittingResources) {Reason=TEXT("Resource commit in progress");return false;}
    if (bDead || GetHealth() <= 0.f) { Reason = TEXT("Dead"); return false; }
    if (IsHitReacting() || bResolvingDamage) { Reason = TEXT("Hit reaction"); return false; }
    if (IsDodging() || bStartingDodge) { Reason=TEXT("Dodging"); return false; }
    if (IsActing()) { Reason = TEXT("Another action is active"); return false; }
    if(auto* Lab=Cast<ACombatLabCharacter>(GetAvatarActor());Lab && Lab->bTrainingEnemy && Lab->EncounterDirector)
        if(!Lab->EncounterDirector->CanAcquire(this)){Reason=TEXT("Waiting for encounter attack slot");return false;}
    if (!AllowsExternalAction(Reason)) return false;
    if (!Action || !Action->Validate(Reason)) return false;
    if (GetUltimateCharge() < Action->UltimateCost) {Reason=TEXT("Not enough ultimate charge");return false;}
    if (GetStamina() < Action->StaminaCost) { Reason = TEXT("Not enough stamina"); return false; }
    if (const double* End = Cooldowns.Find(Action); End && GetWorld()->GetTimeSeconds() < *End)
        { Reason = TEXT("Cooldown"); return false; }
    const ACharacter* Character = Cast<ACharacter>(GetAvatarActor());
    if (!Character || !Character->GetMesh()->GetAnimInstance() || !Character->GetMesh()->GetSkeletalMeshAsset() ||
        !Action->Montage->GetSkeleton()->IsCompatibleMesh(Character->GetMesh()->GetSkeletalMeshAsset()))
        { Reason = TEXT("Compatible character mesh and animation instance required"); return false; }
    if(Action->DashDistance>0 && !Character->GetCharacterMovement()->IsMovingOnGround())
        {Reason=TEXT("Dash requires ground");return false;}
    Reason.Reset(); return true;
}
bool UCombatAbilitySystem::TryStartAction(UCombatActionDefinition* Action)
{
    if (!CanStart(Action, LastReason)) return false;
    FGameplayAbilitySpecHandle* Existing = GrantedActions.Find(Action);
    FGameplayAbilitySpecHandle Handle;
    if (Existing) Handle = *Existing;
    else
    {
        Handle = GiveAbility(FGameplayAbilitySpec(UCombatActionAbility::StaticClass(), 1, INDEX_NONE, Action));
        GrantedActions.Add(Action, Handle);
    }
    const uint64 ExpectedExecution = Ledger.GetExecution() + 1;
    const bool Activated = TryActivateAbility(Handle, false);
    return Activated && IsActing() && Ledger.GetExecution() == ExpectedExecution && ActiveAction == Action;
}
bool UCombatAbilitySystem::GetShouldTick() const
{
    // GAS normally stops ticking when the last task ends. Recovery must keep running while idle.
    return Super::GetShouldTick() || (bInitialized && !bDead && GetOwner() && GetOwner()->HasAuthority());
}
void UCombatAbilitySystem::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if(!bInitialized || !GetOwner() || !GetOwner()->HasAuthority() || bDead || GetHealth()<=0 ||
        !FMath::IsFinite(DeltaTime) || DeltaTime<=0) return;
    float DodgingTime=0.f;
    if(bDodging)
    {
        DodgingTime=FMath::Min(DeltaTime,FMath::Max(0.f,ActiveDodgeDuration-DodgeElapsed));
        DodgeElapsed+=DodgingTime;
        if(DodgeElapsed>=ActiveDodgeDuration) CancelDodge();
    }
    const float Reacting=FMath::Min(DeltaTime-DodgingTime,HitReactionRemaining);
    HitReactionRemaining-=Reacting;
    if(IsActing()) return;
    const float Available=DeltaTime-DodgingTime-Reacting;
    const float Waiting=FMath::Min(Available,RecoveryDelayRemaining);
    RecoveryDelayRemaining-=Waiting;
    const float RecoveryTime=Available-Waiting;
    if(RecoveryTime<=0 || !FMath::IsFinite(StaminaRecoveryPerSecond) || StaminaRecoveryPerSecond<=0) return;
    const float Missing=GetMaxStamina()-GetStamina();
    if(Missing>0)
        ModifyAttribute(UCombatAttributes::GetStaminaAttribute(),FMath::Min(Missing,StaminaRecoveryPerSecond*RecoveryTime),GetOwner());
}
void UCombatAbilitySystem::CancelAction()
{
    OnPresentationReset.Broadcast();
    CancelDodge();
    if (ActiveAbility) CancelAbilityHandle(ActiveAbility->GetCurrentAbilitySpecHandle());
}
bool UCombatAbilitySystem::BeginExecution(UCombatActionAbility* Ability, UCombatActionDefinition* Action)
{
    if (IsActing() || !Ability || !Action) return false;
    if(auto* Lab=Cast<ACombatLabCharacter>(GetAvatarActor());Lab && Lab->bTrainingEnemy && Lab->EncounterDirector)
        if(!Lab->EncounterDirector->Acquire(this)) return false;
    ActiveAbility = Ability; ActiveAction = Action; bCommitted = false;
    MontageInstanceId = INDEX_NONE; Ledger.Begin(); return true;
}
bool UCombatAbilitySystem::CommitExecution()
{
    if (!ActiveAction || bCommitted) return false;
    const float Cost=ActiveAction->StaminaCost, ChargeCost=ActiveAction->UltimateCost;
    if(GetStamina()<Cost || GetUltimateCharge()<ChargeCost) return false;
    ACharacter* Character = Cast<ACharacter>(GetAvatarActor());
    FAnimMontageInstance* Instance = Character ? Character->GetMesh()->GetAnimInstance()->GetActiveInstanceForMontage(ActiveAction->Montage) : nullptr;
    if (!Instance) return false;
    if(ActiveAction->DashDistance>0)
    {
        auto Motion=MakeShared<FRootMotionSource_ConstantForce>();
        Motion->InstanceName=TEXT("CombatActionDash");Motion->Priority=450;
        Motion->AccumulateMode=ERootMotionAccumulateMode::Override;
        Motion->Duration=ActiveAction->DashDuration;
        Motion->Force=Character->GetActorForwardVector().GetSafeNormal2D()*(ActiveAction->DashDistance/ActiveAction->DashDuration);
        Motion->Settings.SetFlag(ERootMotionSourceSettingsFlags::IgnoreZAccumulate);
        Motion->FinishVelocityParams.Mode=ERootMotionFinishVelocityMode::SetVelocity;
        Motion->FinishVelocityParams.SetVelocity=FVector::ZeroVector;
        ActionMotionId=Character->GetCharacterMovement()->ApplyRootMotionSource(Motion);
        if(!ActionMotionId) return false;
    }
    MontageInstanceId = Instance->GetInstanceID();
    bCommitted = true;
    RecoveryDelayRemaining=FMath::IsFinite(StaminaRecoveryDelay)?FMath::Max(0.f,StaminaRecoveryDelay):1.f;
    // A committed attack owns movement immediately, including the frame before the pawn's next tick.
    Character->ConsumeMovementInputVector();
    Character->GetCharacterMovement()->StopMovementImmediately();
    TGuardValue<bool> Committing(bCommittingResources,bCommittingResources || ChargeCost>0);
    Cooldowns.Add(ActiveAction, GetWorld()->GetTimeSeconds() + ActiveAction->Cooldown);
    LastReason = TEXT("Action started");
    // Attribute listeners may synchronously end this action. Do not read ActiveAction afterwards.
    ModifyAttribute(UCombatAttributes::GetStaminaAttribute(), -Cost, GetOwner());
    if(ChargeCost>0) ModifyAttribute(UCombatAttributes::GetUltimateChargeAttribute(),-ChargeCost,GetOwner());
    return true;
}
void UCombatAbilitySystem::StopActionMotion()
{
    if(!ActionMotionId) return;
    if(auto* Character=Cast<ACharacter>(GetAvatarActor()))
    {
        auto* Move=Character->GetCharacterMovement();
        Move->RemoveRootMotionSourceByID(ActionMotionId);
        Move->Velocity=FVector(0,0,Move->Velocity.Z);
    }
    ActionMotionId=0;
}
void UCombatAbilitySystem::CloseExecution()
{
    StopActionMotion();
    if(auto* Lab=Cast<ACombatLabCharacter>(GetAvatarActor());Lab && Lab->EncounterDirector) Lab->EncounterDirector->Release(this);
    const uint64 Id = Ledger.GetExecution();
    const TSet<FName> Windows = Ledger.GetOpenWindows();
    Ledger.End(); MontageInstanceId = INDEX_NONE;
    for (FName Window : Windows) OnHitWindowClosed.Broadcast(Id, Window);
}
void UCombatAbilitySystem::FinishExecution(UCombatActionAbility* Ability, ECombatActionResult Result)
{
    if (ActiveAbility != Ability) return;
    const uint64 Id = Ledger.GetExecution();
    CloseExecution(); ActiveAbility = nullptr; ActiveAction = nullptr; bCommitted = false;
    LastReason = Result == ECombatActionResult::Succeeded ? TEXT("Completed") : Result == ECombatActionResult::Cancelled ? TEXT("Cancelled") : TEXT("Failed");
    OnActionEnded.Broadcast(Id, Result);
}
void UCombatAbilitySystem::ModifyAttribute(const FGameplayAttribute& Attribute, float Delta, AActor* Source)
{
    UGameplayEffect* Effect = NewObject<UGameplayEffect>(GetTransientPackage());
    Effect->DurationPolicy = EGameplayEffectDurationType::Instant;
    FGameplayModifierInfo& Modifier = Effect->Modifiers.AddDefaulted_GetRef();
    Modifier.Attribute = Attribute; Modifier.ModifierOp = EGameplayModOp::Additive;
    Modifier.ModifierMagnitude = FScalableFloat(Delta);
    FGameplayEffectContextHandle Context = MakeEffectContext();
    Context.AddInstigator(Source, Source);
    ApplyGameplayEffectSpecToSelf(FGameplayEffectSpec(Effect, Context, 1.f));
}
bool UCombatAbilitySystem::ReceiveCombatDamage(float Damage, AActor* Source)
{
    if (!bInitialized || bDead || GetHealth() <= 0 || !GetOwner()->HasAuthority() ||
        !FMath::IsFinite(Damage) || Damage <= 0) return false;
    if(IsInvulnerable()) {RecordDamage(0,Source,true);return false;}
    FCombatAcceptedDamage Accepted;
    Accepted.Source=Source;
    if(IsValid(Source))
    {
        const FVector Direction=GetOwner()->GetActorQuat().UnrotateVector(Source->GetActorLocation()-GetOwner()->GetActorLocation()).GetSafeNormal2D();
        if(!Direction.IsNearlyZero() && !Direction.ContainsNaN()) Accepted.LocalSourceDirection=Direction;
    }
    // Block reentrant action starts before cancellation/attribute/damage listeners run.
    TGuardValue<bool> ResolvingDamage(bResolvingDamage,true);
    HitReactionRemaining=FMath::IsFinite(HitReactionDuration)?FMath::Max(0.f,HitReactionDuration):.35f;
    RecoveryDelayRemaining=FMath::IsFinite(StaminaRecoveryDelay)?FMath::Max(0.f,StaminaRecoveryDelay):1.f;
    CancelAction();
    OnHitReceived.Broadcast();
    if(auto* Character=Cast<ACharacter>(GetAvatarActor()))
    {
        Character->ConsumeMovementInputVector();
        Character->GetCharacterMovement()->StopMovementImmediately();
    }
    const float Applied = FMath::Min(Damage, GetHealth());
    ModifyAttribute(UCombatAttributes::GetHealthAttribute(), -Applied, Source);
    RecordDamage(Applied,Source,false);
    Accepted.AppliedDamage=Applied;
    if(Applied>0) OnDamageAccepted.Broadcast(Accepted);
    // This is a notification for existing carry listeners, not another ApplyDamage call.
    GetOwner()->OnTakeAnyDamage.Broadcast(GetOwner(), Applied, GetDefault<UDamageType>(), nullptr, Source);
    if (GetHealth() <= 0 && !bDead)
    {
        bDead = true; HitReactionRemaining=0.f; CancelAction(); OnDied.Broadcast();
    }
    return true;
}
bool UCombatAbilitySystem::MatchesMontageInstance(int32 InstanceId) const
{
    return ActiveAbility && bCommitted && InstanceId != INDEX_NONE && InstanceId == MontageInstanceId;
}
void UCombatAbilitySystem::OpenHitWindow(FName Window, int32 Id)
{
    if (!MatchesMontageInstance(Id)) return;
    const bool AlreadyOpen = Ledger.IsOpen(Window);
    if (!Ledger.Open(Window)) return;
    if (!AlreadyOpen) OnHitWindowOpened.Broadcast(Ledger.GetExecution(), Window);
    TickHitWindow(Window, Id);
}
void UCombatAbilitySystem::CloseHitWindow(FName Window, int32 Id)
{
    if (!MatchesMontageInstance(Id) || !Ledger.IsOpen(Window)) return;
    Ledger.Close(Window);
    OnHitWindowClosed.Broadcast(Ledger.GetExecution(), Window);
}
bool UCombatAbilitySystem::ApplyHit(FName Window, AActor* Target)
{
    const FVector Position = IsValid(Target) ? Target->GetActorLocation() : FVector::ZeroVector;
    const FVector Normal = GetAvatarActor() ? (GetAvatarActor()->GetActorLocation()-Position).GetSafeNormal() : FVector::UpVector;
    return ApplyHit(Window, Target, Position, Normal);
}
bool UCombatAbilitySystem::ApplyHit(FName Window, AActor* Target, const FVector& Position, const FVector& Normal)
{
    if (!ActiveAction || !IsValid(Target) || Target == GetAvatarActor()) return false;
    UCombatAbilitySystem* Other = Target->FindComponentByClass<UCombatAbilitySystem>();
    if (!Other || Other->TeamId == TeamId || Other->GetHealth() <= 0) return false;
    if (!Ledger.Claim(Window, Target)) return false;
    FCombatConfirmedHit Hit;
    Hit.ExecutionId = Ledger.GetExecution(); Hit.Window = Window;
    Hit.Source = GetAvatarActor(); Hit.Target = Target;
    Hit.Position = Position.ContainsNaN() ? Target->GetActorLocation() : Position;
    Hit.Normal = Normal.ContainsNaN() ? FVector::UpVector : Normal.GetSafeNormal();
    if (Hit.Normal.IsNearlyZero()) Hit.Normal = FVector::UpVector;
    const float Damage = ActiveAction->Damage;
    const float Gain = ActiveAction->UltimateGain;
    Hit.AppliedDamage = FMath::Min(Damage, Other->GetHealth());
    // Damage listeners can cancel/restart this source; only the captured context is read afterwards.
    if (!Other->ReceiveCombatDamage(Damage, Hit.Source.Get())) return false;
    if (Gain>0 && !bDead && GetHealth()>0 && IsValid(GetAvatarActor()))
        ModifyAttribute(UCombatAttributes::GetUltimateChargeAttribute(),Gain,GetOwner());
    OnHitConfirmed.Broadcast(Hit);
    return true;
}
void UCombatAbilitySystem::TickHitWindow(FName Window, int32 Id)
{
    if (!MatchesMontageInstance(Id) || !Ledger.IsOpen(Window) || !ActiveAction) return;
    AActor* Avatar = GetAvatarActor();
    const FVector Start = Avatar->GetActorLocation();
    if(ActiveAction->bRadialHit)
    {
        const float Radius=ActiveAction->Radius;
        FCollisionQueryParams Query(SCENE_QUERY_STAT(CombatRadial),false,Avatar);
        TArray<FOverlapResult> Overlaps;
        GetWorld()->OverlapMultiByObjectType(Overlaps,Start,FQuat::Identity,
            FCollisionObjectQueryParams::AllDynamicObjects,FCollisionShape::MakeSphere(Radius),Query);
        if(bDrawHitDebug) DrawDebugSphere(GetWorld(),Start,Radius,32,FColor::Orange,false,0.f,0,1.5f);
        for(const auto& Overlap:Overlaps)
        {
            if(!MatchesMontageInstance(Id)) break;
            AActor* Target=Overlap.GetActor();if(!IsValid(Target) || Target==Avatar) continue;
            FHitResult Block;
            const FVector Position=Target->GetActorLocation();
            FCollisionQueryParams Sight=Query;
            // Area damage is occluded by world geometry, not by another combatant's capsule.
            for(const auto& Other:Overlaps)
                if(auto* Actor=Other.GetActor();Actor && Actor!=Target && Actor->FindComponentByClass<UCombatAbilitySystem>()) Sight.AddIgnoredActor(Actor);
            if(GetWorld()->LineTraceSingleByChannel(Block,Start,Position,ECC_Visibility,Sight) && Block.GetActor()!=Target) continue;
            ApplyHit(Window,Target,Position,(Start-Position).GetSafeNormal());
        }
        return;
    }
    const FVector End = Start + Avatar->GetActorForwardVector() * ActiveAction->Reach;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(CombatCore), false, Avatar);
    TArray<FHitResult> Hits;
    GetWorld()->SweepMultiByChannel(Hits, Start, End, FQuat::Identity, ECC_Visibility,
        FCollisionShape::MakeSphere(ActiveAction->Radius), Params);
    if (bDrawHitDebug)
    {
        DrawDebugCapsule(GetWorld(),(Start+End)*.5f,ActiveAction->Reach*.5f+ActiveAction->Radius,
            ActiveAction->Radius,FQuat::FindBetweenNormals(FVector::UpVector,Avatar->GetActorForwardVector()),
            FColor::Orange,false,0.f,0,1.5f);
    }
    for (const FHitResult& Hit : Hits)
    {
        if (!MatchesMontageInstance(Id)) break;
        ApplyHit(Window, Hit.GetActor(), Hit.ImpactPoint, Hit.ImpactNormal);
    }
}
void UCombatAbilitySystem::EndPlay(const EEndPlayReason::Type Reason)
{
    CancelAction(); CloseExecution(); Super::EndPlay(Reason);
}
