#include "CombatLabCharacter.h"
#if !UE_BUILD_SHIPPING
#include "CombatAbilitySystem.h"
#include "EngineUtils.h"
#include "Components/BoxComponent.h"
#include "TimerManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Kismet/KismetSystemLibrary.h"
void ACombatLabCharacter::ConfigurePatternReview()
{
    if(bTrainingEnemy || !FParse::Param(FCommandLine::Get(),TEXT("CombatPatternReview"))) return;
    struct FState { TWeakObjectPtr<ACombatLabCharacter> Enemy; TWeakObjectPtr<AActor> Wall; TSet<FName> Selected; bool Range=false,Sight=false; };
    const auto State=MakeShared<FState>();
    for(TActorIterator<ACombatLabCharacter> It(GetWorld());It;++It) if(It->bTrainingEnemy) State->Enemy=*It;
    if(auto* Enemy=State->Enemy.Get())
    {
        SetActorLocation(Enemy->GetActorLocation()-FVector(400,0,0),false);
        Enemy->SetActorRotation(FRotator(0,180,0));
    }
    // Advance on actual AI decisions, not a guessed startup frame/timer ordering.
    FTimerHandle Observe;
    GetWorldTimerManager().SetTimer(Observe,FTimerDelegate::CreateWeakLambda(this,[this,State]()
    {
        auto* Enemy=State->Enemy.Get(); if(!Enemy) return;
        if(!State->Range && Enemy->Combat->GetExecutionId()==0 && Enemy->Combat->LastPatternDecision.Contains(TEXT("Distance")))
        {
            State->Range=true;
            SetActorLocation(Enemy->GetActorLocation()-FVector(125,0,0),false);
            auto* Wall=GetWorld()->SpawnActor<AActor>(); State->Wall=Wall;
            auto* Box=NewObject<UBoxComponent>(Wall); Wall->SetRootComponent(Box);
            Box->SetBoxExtent(FVector(5,100,150)); Box->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
            Box->SetCollisionResponseToAllChannels(ECR_Block); Box->RegisterComponent();
            Wall->SetActorLocation(Enemy->GetActorLocation()-FVector(62,0,0));
        }
        else if(State->Range && !State->Sight && Enemy->Combat->GetExecutionId()==0 && Enemy->Combat->LastPatternDecision.Contains(TEXT("Sight")))
        {
            State->Sight=true;
            if(State->Wall.IsValid()) State->Wall->Destroy();
        }
        if(!Enemy->Combat->LastSelectedPattern.IsNone()) State->Selected.Add(Enemy->Combat->LastSelectedPattern);
    }),.1f,true);
    FTimerHandle Finish;
    GetWorldTimerManager().SetTimer(Finish,FTimerDelegate::CreateWeakLambda(this,[this,State]()
    {
        auto* Enemy=State->Enemy.Get();
        const bool Passed=Enemy && State->Range && State->Sight && State->Selected.Contains("Light") && State->Selected.Contains("Heavy");
        const FString Report=FString::Printf(TEXT("{\"passed\":%s,\"distance_blocked\":%s,\"sight_blocked\":%s,\"patterns_seen\":%d,\"executions\":%llu}"),
            Passed?TEXT("true"):TEXT("false"),State->Range?TEXT("true"):TEXT("false"),State->Sight?TEXT("true"):TEXT("false"),State->Selected.Num(),Enemy?Enemy->Combat->GetExecutionId():0);
        FFileHelper::SaveStringToFile(Report,*(FPaths::ProjectSavedDir()/TEXT("CombatAudit/20261004/pattern-review.json")));
        UE_LOG(LogTemp,Display,TEXT("COMBAT_PATTERN_REVIEW %s"),*Report);
        UKismetSystemLibrary::QuitGame(this,nullptr,EQuitPreference::Quit,false);
    }),12.f,false);
}
#endif
