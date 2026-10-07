#include "CombatEnemyAgent.h"
#include "CombatEncounterProfile.h"
#include "CombatLabCharacter.h"
#include "CombatAbilitySystem.h"
#include "AIController.h"
#include "NavigationSystem.h"
#include "Navigation/PathFollowingComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
UCombatEnemyAgent::UCombatEnemyAgent()
{
    PrimaryComponentTick.bCanEverTick=true;
    PrimaryComponentTick.bStartWithTickEnabled=false;
}
void UCombatEnemyAgent::Initialize(UCombatEncounterProfile* InProfile)
{
    if(bInitialized || !InProfile) return;
    Fighter=Cast<ACombatLabCharacter>(GetOwner());
    if(!Fighter.IsValid() || !GetOwner()->HasAuthority()) return;
    Profile=InProfile; Home=GetOwner()->GetActorLocation(); ProgressLocation=Home;
    bInitialized=true; SetComponentTickInterval(FMath::Max(.05f,Profile->ThinkInterval)); SetComponentTickEnabled(true);
}
bool UCombatEnemyAgent::HasSight(APawn* Other) const
{
    if(!Other || !Fighter.IsValid()) return false;
    FHitResult Hit; FCollisionQueryParams Query(SCENE_QUERY_STAT(CombatEnemySight),false,GetOwner());
    const bool Blocked=GetWorld()->LineTraceSingleByChannel(Hit,GetOwner()->GetActorLocation(),Other->GetActorLocation(),ECC_Visibility,Query);
    return !Blocked || Hit.GetActor()==Other;
}
void UCombatEnemyAgent::StopMove()
{
    TGuardValue<bool> Stopping(bStopping,true); MoveId=FAIRequestID::InvalidRequest;
    if(Controller.IsValid()) Controller->StopMovement();
}
void UCombatEnemyAgent::ReturnHome(const FString& Reason)
{
    State=ECombatEnemyState::Returning; Decision=Reason;
    ProgressLocation=GetOwner()->GetActorLocation(); LastProgressTime=Time;
    Target.Reset(); MoveFailures=0; NextMoveTime=Time; AcquireAfter=Time+Profile->RetryCooldown;
    StopMove();
    if(Fighter.IsValid()) Fighter->Combat->CancelAction();
}
void UCombatEnemyAgent::MoveFailed()
{
    ++MoveFailures; NextMoveTime=Time+Profile->RetryDelay;
    Decision=FString::Printf(TEXT("Navigation failed (%d/%d)"),MoveFailures,Profile->MaxMoveFailures);
    if(MoveFailures<Profile->MaxMoveFailures) return;
    if(State==ECombatEnemyState::Returning || State==ECombatEnemyState::Blocked)
    {
        State=ECombatEnemyState::Blocked; Decision=TEXT("Home unreachable; waiting before retry");
        MoveFailures=0; NextMoveTime=Time+Profile->RetryCooldown;
    }
    else ReturnHome(TEXT("Chase navigation failed; returning"));
}
void UCombatEnemyAgent::MoveEnded(FAIRequestID Request,const FPathFollowingResult& Result)
{
    if(bStopping || Request!=MoveId) return;
    MoveId=FAIRequestID::InvalidRequest;
    if(Result.IsSuccess()) MoveFailures=0;
    else MoveFailed();
}
void UCombatEnemyAgent::Move(const FVector& Goal,float Radius)
{
    auto* AI=Controller.Get(); if(!AI || Time<NextMoveTime) return;
    const auto Status=AI->GetMoveStatus();
    if(Status==EPathFollowingStatus::Moving)
    {
        if(FVector::Dist2D(GetOwner()->GetActorLocation(),ProgressLocation)>5)
        { ProgressLocation=GetOwner()->GetActorLocation(); LastProgressTime=Time; }
        if(Time-LastProgressTime>Profile->StuckTimeout) { StopMove(); MoveFailed(); return; }
        if(FVector::Dist2D(Goal,LastGoal)<60) return;
        StopMove();
    }
    // MoveTo may accept an origin goal when no navigation system exists.
    if(!FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld())) { MoveFailed(); return; }
    FAIMoveRequest Request(Goal);
    Request.SetUsePathfinding(true); Request.SetAllowPartialPath(false); Request.SetProjectGoalLocation(true);
    Request.SetAcceptanceRadius(Radius); Request.SetReachTestIncludesAgentRadius(false); Request.SetReachTestIncludesGoalRadius(false);
    const auto Result=AI->MoveTo(Request);
    NextMoveTime=Time+Profile->RetryDelay;
    if(Result.Code==EPathFollowingRequestResult::Failed) { MoveFailed(); return; }
    MoveId=Result.MoveId; LastGoal=Goal;
    if(State==ECombatEnemyState::Blocked) { State=ECombatEnemyState::Returning; Decision=TEXT("Retrying return home"); }
}
void UCombatEnemyAgent::TickComponent(float Delta,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(Delta,TickType,ThisTickFunction);
    auto* Pawn=Fighter.Get();
    if(!bInitialized || !Pawn || !Profile || !Pawn->HasAuthority() || !FMath::IsFinite(Delta) || Delta<=0) return;
    Time+=Delta;
    FString Error;
    if(!Profile->Validate(Error)) { StopMove(); State=ECombatEnemyState::Idle; Decision=Error; return; }
    auto* AI=Cast<AAIController>(Pawn->GetController());
    if(AI!=Controller.Get())
    {
        StopMove();
        if(Controller.IsValid()) Controller->GetPathFollowingComponent()->OnRequestFinished.Remove(MoveEndHandle);
        Controller=AI;
        if(AI) MoveEndHandle=AI->GetPathFollowingComponent()->OnRequestFinished.AddUObject(this,&UCombatEnemyAgent::MoveEnded);
    }
    if(Pawn->Combat->GetHealth()<=0) { StopMove(); Target.Reset(); State=ECombatEnemyState::Dead; Decision=TEXT("Dead"); return; }
    if(!AI) { Target.Reset(); State=ECombatEnemyState::Idle; Pawn->Combat->CancelAction(); Decision=TEXT("No AI controller"); return; }
    Pawn->GetCharacterMovement()->MaxWalkSpeed=Profile->MoveSpeed;
    if(State==ECombatEnemyState::Returning || State==ECombatEnemyState::Blocked)
    {
        if(Pawn->Combat->IsHitReacting()) { StopMove(); Decision=TEXT("Hit while returning"); return; }
        if(FVector::Dist2D(Home,Pawn->GetActorLocation())<=Profile->HomeTolerance)
        {
            StopMove();
            if(Profile->bRestoreOnReturn) Pawn->Combat->ResetAfterReturn();
            ++EncounterEpoch; State=ECombatEnemyState::Idle; MoveFailures=0;
            AcquireAfter=Time+Profile->RetryCooldown; Decision=TEXT("Home reached; encounter reset"); return;
        }
        Move(Home,FMath::Max(1.f,Profile->HomeTolerance-10)); return;
    }
    if(Target.IsValid())
    {
        auto* Other=Target->FindComponentByClass<UCombatAbilitySystem>();
        if(!Other || Other->GetHealth()<=0 || Other->TeamId==Pawn->Combat->TeamId) { ReturnHome(TEXT("Target unavailable; returning")); return; }
    }
    else if(State!=ECombatEnemyState::Idle) { ReturnHome(TEXT("Target lost; returning")); return; }
    if(!Target.IsValid())
    {
        if(Time<AcquireAfter) { Decision=TEXT("Reacquisition cooldown"); return; }
        APawn* Candidate=UGameplayStatics::GetPlayerPawn(Pawn,0);
        auto* Other=Candidate?Candidate->FindComponentByClass<UCombatAbilitySystem>():nullptr;
        if(!Other || Other->GetHealth()<=0 || Other->TeamId==Pawn->Combat->TeamId ||
            FVector::Dist2D(Pawn->GetActorLocation(),Candidate->GetActorLocation())>Profile->DetectRadius ||
            FVector::Dist2D(Home,Candidate->GetActorLocation())>Profile->LeashRadius || !HasSight(Candidate))
            { State=ECombatEnemyState::Idle; Decision=TEXT("Waiting for visible hostile target"); return; }
        Target=Candidate; LastSeen=Candidate->GetActorLocation(); LastSightTime=Time; MoveFailures=0;
        ProgressLocation=Pawn->GetActorLocation(); LastProgressTime=Time;
    }
    const float Distance=FVector::Dist2D(Pawn->GetActorLocation(),Target->GetActorLocation());
    if(Distance>Profile->LoseRadius || FVector::Dist2D(Home,Pawn->GetActorLocation())>Profile->LeashRadius ||
        FVector::Dist2D(Home,Target->GetActorLocation())>Profile->LeashRadius)
        { ReturnHome(TEXT("Leash exceeded; returning")); return; }
    const bool Visible=HasSight(Target.Get());
    if(Visible) { LastSeen=Target->GetActorLocation(); LastSightTime=Time; }
    else if(Time-LastSightTime>=Profile->LostSightTime) { ReturnHome(TEXT("Sight timeout; returning")); return; }
    State=Visible?(Distance<=Profile->AttackDistance?ECombatEnemyState::Fighting:ECombatEnemyState::Chasing):ECombatEnemyState::Searching;
    Decision=Visible?(State==ECombatEnemyState::Fighting?TEXT("Attack range"):TEXT("Approaching target")):TEXT("Searching last seen position");
    if(Pawn->Combat->IsActing() || Pawn->Combat->IsHitReacting() || Pawn->Combat->IsDodging() || State==ECombatEnemyState::Fighting)
        { StopMove(); LastProgressTime=Time; return; }
    Move(LastSeen,Visible?FMath::Max(1.f,Profile->AttackDistance-20):Profile->HomeTolerance);
}
void UCombatEnemyAgent::EndPlay(const EEndPlayReason::Type Reason)
{
    StopMove();
    if(Controller.IsValid()) Controller->GetPathFollowingComponent()->OnRequestFinished.Remove(MoveEndHandle);
    Super::EndPlay(Reason);
}
