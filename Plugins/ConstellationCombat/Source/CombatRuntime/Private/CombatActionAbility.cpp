#include "CombatActionAbility.h"
#include "CombatActionDefinition.h"
#include "Abilities/Tasks/AbilityTask_PlayMontageAndWait.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/AnimMontage.h"
UCombatActionAbility::UCombatActionAbility()
{
    InstancingPolicy = EGameplayAbilityInstancingPolicy::InstancedPerActor;
    NetExecutionPolicy = EGameplayAbilityNetExecutionPolicy::ServerOnly;
}
bool UCombatActionAbility::CanActivateAbility(FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* Info,
    const FGameplayTagContainer* SourceTags, const FGameplayTagContainer* TargetTags, FGameplayTagContainer* RelevantTags) const
{
    if (!Info || !Super::CanActivateAbility(Handle, Info, SourceTags, TargetTags, RelevantTags)) return false;
    UCombatAbilitySystem* ASC = Cast<UCombatAbilitySystem>(Info->AbilitySystemComponent.Get());
    const FGameplayAbilitySpec* Spec = ASC ? ASC->FindAbilitySpecFromHandle(Handle) : nullptr;
    FString Reason;
    return Spec && ASC->CanStart(Cast<UCombatActionDefinition>(Spec->SourceObject.Get()), Reason);
}
void UCombatActionAbility::ActivateAbility(FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* Info,
    FGameplayAbilityActivationInfo Activation, const FGameplayEventData* Event)
{
    bFinishing = false; Result = ECombatActionResult::Failed;
    UCombatAbilitySystem* ASC = Cast<UCombatAbilitySystem>(Info->AbilitySystemComponent.Get());
    UCombatActionDefinition* Action = Cast<UCombatActionDefinition>(GetCurrentSourceObject());
    if (!ASC || !Action || !CommitAbility(Handle, Info, Activation) || !ASC->BeginExecution(this, Action))
    {
        EndAbility(Handle, Info, Activation, false, true); return;
    }
    // Native review character uses a single-node instance. Production AnimBPs use their slot graph.
    if (UAnimSingleNodeInstance* Single = Cast<UAnimSingleNodeInstance>(Info->GetAnimInstance()))
        Single->SetAnimationAsset(Action->Montage, false, Action->PlayRate);
    auto* Task = UAbilityTask_PlayMontageAndWait::CreatePlayMontageAndWaitProxy(
        this, NAME_None, Action->Montage, Action->PlayRate, NAME_None, true, 1.f, 0.f, true);
    Task->OnCompleted.AddDynamic(this, &UCombatActionAbility::MontageCompleted);
    Task->OnInterrupted.AddDynamic(this, &UCombatActionAbility::MontageInterrupted);
    Task->OnCancelled.AddDynamic(this, &UCombatActionAbility::MontageInterrupted);
    Task->ReadyForActivation();
    if (IsActive())
    {
        Result = ECombatActionResult::Cancelled;
        if (!ASC->CommitExecution())
        {
            Result = ECombatActionResult::Failed;
            EndAbility(Handle, Info, Activation, false, true);
        }
    }
}
void UCombatActionAbility::MontageCompleted()
{
    Result = ECombatActionResult::Succeeded;
    EndAbility(CurrentSpecHandle, CurrentActorInfo, CurrentActivationInfo, false, false);
}
void UCombatActionAbility::MontageInterrupted()
{
    EndAbility(CurrentSpecHandle, CurrentActorInfo, CurrentActivationInfo, false, true);
}
void UCombatActionAbility::EndAbility(FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* Info,
    FGameplayAbilityActivationInfo Activation, bool Replicate, bool Cancelled)
{
    if (bFinishing || !IsActive()) return;
    bFinishing = true;
    UCombatAbilitySystem* ASC = Info ? Cast<UCombatAbilitySystem>(Info->AbilitySystemComponent.Get()) : nullptr;
    if (ASC) ASC->CloseExecution();
    const ECombatActionResult FinalResult = Cancelled && Result != ECombatActionResult::Failed ? ECombatActionResult::Cancelled : Result;
    Super::EndAbility(Handle, Info, Activation, Replicate, Cancelled);
    if (ASC) ASC->FinishExecution(this, FinalResult);
}
