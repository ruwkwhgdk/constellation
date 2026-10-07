#include "CombatAttackInput.h"
#include "CombatActionDefinition.h"
#include "GameFramework/Character.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "TimerManager.h"
void UCombatAttackInput::Initialize(UCombatAbilitySystem* InSystem)
{
    if(System==InSystem) return;
    Detach(); System=InSystem;
    if(System)
    {
        EndHandle=System->OnActionEnded.AddUObject(this,&UCombatAttackInput::Ended);
        DeathHandle=System->OnDied.AddUObject(this,&UCombatAttackInput::Clear);
        HitHandle=System->OnHitReceived.AddUObject(this,&UCombatAttackInput::Clear);
        DodgeHandle=System->OnDodgeStarted.AddUObject(this,&UCombatAttackInput::Clear);
    }
}
void UCombatAttackInput::Clear()
{
    ++Generation; PendingAction=nullptr; BufferedExecution=0;
    LastInputReason=TEXT("No buffered attack");
}
void UCombatAttackInput::Detach()
{
    Clear();
    if(System)
    {
        System->OnActionEnded.Remove(EndHandle);
        System->OnDied.Remove(DeathHandle);
        System->OnHitReceived.Remove(HitHandle);
        System->OnDodgeStarted.Remove(DodgeHandle);
    }
    EndHandle.Reset(); DeathHandle.Reset(); HitHandle.Reset(); DodgeHandle.Reset(); System=nullptr;
}
bool UCombatAttackInput::RequestAttack(UCombatActionDefinition* EntryAction)
{
    if(!System) return false;
    if(!System->IsActing())
    {
        // Natural completion has scheduled the next action; extra presses keep that handoff intact.
        if(PendingAction && BufferedExecution==System->GetExecutionId())
        {
            LastInputReason=TEXT("Follow-up queued"); return true;
        }
        Clear();
        const bool Started=System->TryStartAction(EntryAction);
        LastInputReason=Started?TEXT("Started"):System->LastReason; return Started;
    }
    if(PendingAction && BufferedExecution!=System->GetExecutionId()) Clear();
    UCombatActionDefinition* Current=System->GetActiveAction();
    if(!Current || !Current->NextAction) { LastInputReason=TEXT("No follow-up"); return false; }
    FString Reason;
    if(!Current->Validate(Reason) || !Current->NextAction->Validate(Reason))
        { LastInputReason=Reason; return false; }
    const ACharacter* Character=Cast<ACharacter>(System->GetAvatarActor());
    UAnimInstance* Anim=Character ? Character->GetMesh()->GetAnimInstance() : nullptr;
    FAnimMontageInstance* Instance=Anim ? Anim->GetActiveInstanceForMontage(Current->Montage) : nullptr;
    if(!Instance || !System->MatchesMontageInstance(Instance->GetInstanceID())) return false;
    const float Position=Instance->GetPosition();
    if(Position<Current->InputWindowStart || Position>Current->InputWindowEnd)
        { LastInputReason=TEXT("Outside follow-up input window"); return false; }
    PendingAction=Current->NextAction; BufferedExecution=System->GetExecutionId();
    LastInputReason=TEXT("Follow-up queued"); return true;
}
void UCombatAttackInput::Ended(uint64 Execution,ECombatActionResult Result)
{
    if(Execution!=BufferedExecution || !PendingAction) return;
    if(Result!=ECombatActionResult::Succeeded) { Clear(); LastInputReason=TEXT("Queue cancelled"); return; }
    // Defer until GAS/animation completion callbacks have fully unwound.
    const uint64 Ticket=++Generation;
    GetWorld()->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(this,[this,Execution,Ticket]()
    {
        if(Generation!=Ticket) return;
        UCombatActionDefinition* Next=PendingAction;
        const bool StillCurrent=System && !System->IsActing() && System->GetExecutionId()==Execution;
        Clear();
        if(StillCurrent && Next)
        {
            const bool Started=System->TryStartAction(Next);
            LastInputReason=Started?TEXT("Follow-up started"):System->LastReason;
        }
    }));
}
void UCombatAttackInput::EndPlay(const EEndPlayReason::Type Reason)
{
    Detach(); Super::EndPlay(Reason);
}
