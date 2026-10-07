#include "BTTask_CombatAction.h"
#include "CombatActionDefinition.h"
#include "CombatPatternProfile.h"
#include "CombatEnemyAgent.h"
#include "BehaviorTree/BehaviorTreeComponent.h"
#include "AIController.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/Pawn.h"
UBTTask_CombatAction::UBTTask_CombatAction()
{
    bCreateNodeInstance = true; bNotifyTaskFinished = true; NodeName = TEXT("Execute Combat Action");
}
EBTNodeResult::Type UBTTask_CombatAction::ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8*)
{
    Detach();
    AAIController* AI = OwnerComp.GetAIOwner();
    APawn* Pawn = AI ? AI->GetPawn() : nullptr;
    auto* ASC = Pawn ? Pawn->FindComponentByClass<UCombatAbilitySystem>() : nullptr;
    if (!ASC || ASC->IsActing()) return EBTNodeResult::Failed;
    if(auto* Agent=Pawn->FindComponentByClass<UCombatEnemyAgent>(); Agent && Agent->IsManaging())
    {
        if(EncounterEpoch!=Agent->GetEncounterEpoch()) { EncounterEpoch=Agent->GetEncounterEpoch(); LastPattern=NAME_None; ConsecutiveUses=0; }
        if(!Agent->CanAttack()) return EBTNodeResult::Failed;
    }
    UCombatActionDefinition* SelectedAction=Action;
    FName SelectedId;
    if(PatternProfile)
    {
        APawn* Player=UGameplayStatics::GetPlayerPawn(Pawn,0);
        auto* Other=Player?Player->FindComponentByClass<UCombatAbilitySystem>():nullptr;
        if(!Other || Other->GetHealth()<=0 || Other->TeamId==ASC->TeamId)
            { ASC->LastPatternDecision=TEXT("No living hostile player"); return EBTNodeResult::Failed; }
        const FVector Offset=Player->GetActorLocation()-Pawn->GetActorLocation();
        const float Angle=FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(Pawn->GetActorForwardVector().GetSafeNormal2D(),Offset.GetSafeNormal2D()),-1.f,1.f)));
        FHitResult Hit; FCollisionQueryParams Query(SCENE_QUERY_STAT(CombatPatternSight),false,Pawn);
        const bool Blocked=Pawn->GetWorld()->LineTraceSingleByChannel(Hit,Pawn->GetActorLocation(),Player->GetActorLocation(),ECC_Visibility,Query);
        const bool HasSight=!Blocked || Hit.GetActor()==Player;
        const int32 Index=PatternProfile->Select(ASC,Offset.Size2D(),Angle,HasSight,LastPattern,ConsecutiveUses,FMath::FRand(),ASC->LastPatternDecision);
        if(Index==INDEX_NONE)
        {
            // Turning is a separate observation step; eligibility is reevaluated after the wait.
            if(HasSight && !ASC->IsHitReacting() && !ASC->IsDodging()) Pawn->SetActorRotation(FRotator(0,Offset.Rotation().Yaw,0));
            return EBTNodeResult::Failed;
        }
        SelectedAction=PatternProfile->Patterns[Index].Action;
        SelectedId=PatternProfile->Patterns[Index].Id;
        Pawn->SetActorRotation(FRotator(0,Offset.Rotation().Yaw,0));
    }
    else if (PlayerRange > 0)
    {
        APawn* Player = UGameplayStatics::GetPlayerPawn(Pawn, 0);
        auto* Other = Player ? Player->FindComponentByClass<UCombatAbilitySystem>() : nullptr;
        if (!Other || Other->GetHealth() <= 0 || FVector::Dist2D(Pawn->GetActorLocation(), Player->GetActorLocation()) > PlayerRange)
            return EBTNodeResult::Failed;
        Pawn->SetActorRotation(FRotator(0, (Player->GetActorLocation()-Pawn->GetActorLocation()).Rotation().Yaw, 0));
    }
    System = ASC; Brain = &OwnerComp; ExpectedExecution = ASC->GetExecutionId() + 1;
    EndHandle = ASC->OnActionEnded.AddUObject(this, &UBTTask_CombatAction::Ended);
    bCommittedEndDuringStart=false;
    bStarting = true;
    const bool Started = ASC->TryStartAction(SelectedAction);
    bStarting = false;

    if(PatternProfile && (Started || bCommittedEndDuringStart))
    {
        ConsecutiveUses=LastPattern==SelectedId?ConsecutiveUses+1:1;
        LastPattern=SelectedId; ASC->LastSelectedPattern=SelectedId;
    }
    if (!Started) { Detach(); return EBTNodeResult::Failed; }
    return EBTNodeResult::InProgress;
}
void UBTTask_CombatAction::Ended(uint64 Execution, ECombatActionResult Result)
{
    if (Execution != ExpectedExecution) return;
    if(bStarting)
    {
        // Cancelled/succeeded callbacks have passed the ability's commit stage; failures have not.
        bCommittedEndDuringStart=Result!=ECombatActionResult::Failed;
        return;
    }
    UBehaviorTreeComponent* Owner = Brain.Get();
    Detach();
    if (Owner) FinishLatentTask(*Owner, Result == ECombatActionResult::Succeeded ? EBTNodeResult::Succeeded : EBTNodeResult::Failed);
}
EBTNodeResult::Type UBTTask_CombatAction::AbortTask(UBehaviorTreeComponent&, uint8*)
{
    UCombatAbilitySystem* ASC = System.Get();
    const uint64 Id = ExpectedExecution;
    Detach();
    if (ASC && ASC->GetExecutionId() == Id) ASC->CancelAction();
    return EBTNodeResult::Aborted;
}
void UBTTask_CombatAction::OnTaskFinished(UBehaviorTreeComponent& OwnerComp, uint8* Memory, EBTNodeResult::Type Result)
{
    Detach(); Super::OnTaskFinished(OwnerComp, Memory, Result);
}
void UBTTask_CombatAction::Detach()
{
    if (System.IsValid()) System->OnActionEnded.Remove(EndHandle);
    EndHandle.Reset(); System.Reset(); Brain.Reset();
}
