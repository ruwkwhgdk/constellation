#include "CombatLabCharacter.h"
#if !UE_BUILD_SHIPPING
#include "CombatAbilitySystem.h"
#include "CombatEnemyAgent.h"
#include "CombatEncounterProfile.h"
#include "EngineUtils.h"
#include "TimerManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Serialization/JsonSerializer.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/KismetSystemLibrary.h"
void ACombatLabCharacter::ConfigureEncounterReview()
{
    if(bTrainingEnemy || !FParse::Param(FCommandLine::Get(),TEXT("CombatEncounterReview"))) return;
    struct FState
    {
        TWeakObjectPtr<ACombatLabCharacter> Enemy;
        bool Valid=false,Damaged=false,Chased=false,Attacked=false,Returned=false,Recovered=false,Cancelled=false,Restore=true;
        float Detour=0,ExitDistance=0,HomeTolerance=0,ExpectedHealth=0,ActualHealth=0;
        uint64 Execution=0;
        FString Reason;
    };
    const auto State=MakeShared<FState>();
    int32 EnemyCount=0;
    for(TActorIterator<ACombatLabCharacter> It(GetWorld());It;++It)
        if(It->bTrainingEnemy) { State->Enemy=*It; ++EnemyCount; }
    float Seconds=18.f;
    FParse::Value(FCommandLine::Get(),TEXT("CombatReviewSeconds="),Seconds);
    if(!FMath::IsFinite(Seconds) || Seconds<5 || Seconds>120)
    { State->Reason=TEXT("CombatReviewSeconds must be 5..120"); Seconds=18; }
    else if(EnemyCount!=1) State->Reason=TEXT("The obstacle scenario requires exactly one enemy");
    else if(auto* Enemy=State->Enemy.Get())
    {
        auto* Profile=Enemy->EncounterProfile.Get();
        if(!Profile) State->Reason=TEXT("EncounterProfile is missing");
        else if(Profile->Validate(State->Reason))
        {
            const float Distance=FVector::Dist2D(GetActorLocation(),Enemy->GetActorLocation());
            if(Distance>Profile->DetectRadius || Distance>Profile->LeashRadius || Distance<=Profile->AttackDistance)
                State->Reason=TEXT("Initial placement must be inside detection/leash and outside attack range");
            else
            {
                State->Valid=true;
                State->ExitDistance=Profile->LeashRadius+FMath::Max(300.f,2.f*Profile->HomeTolerance);
                State->HomeTolerance=Profile->HomeTolerance;
                State->Restore=Profile->bRestoreOnReturn;
            }
        }
    }
    FTimerHandle Observe;
    GetWorldTimerManager().SetTimer(Observe,FTimerDelegate::CreateWeakLambda(this,[this,State]()
    {
        auto* Enemy=State->Enemy.Get(); if(!Enemy || !State->Valid) return;
        State->Chased|=Enemy->EnemyAgent->State==ECombatEnemyState::Chasing;
        State->Detour=FMath::Max(State->Detour,FMath::Abs(Enemy->GetActorLocation().Y));
        State->ActualHealth=Enemy->Combat->GetHealth();
        if(!State->Damaged && State->Chased)
        {
            State->Damaged=Enemy->Combat->ReceiveCombatDamage(10,this);
            State->ExpectedHealth=State->Restore?Enemy->Combat->GetMaxHealth():Enemy->Combat->GetHealth();
        }
        if(State->Damaged && !State->Attacked && Enemy->Combat->IsActing())
        {
            State->Attacked=true;
            State->Execution=Enemy->Combat->GetExecutionId();
            Enemy->Combat->OnActionEnded.AddWeakLambda(this,[State](uint64 Execution,ECombatActionResult Result)
            {
                auto* Target=State->Enemy.Get();
                if(Target && Execution==State->Execution && Result==ECombatActionResult::Cancelled &&
                    Target->EnemyAgent->State==ECombatEnemyState::Returning) State->Cancelled=true;
            });
            // Test-only: suspend player movement so an exit outside the small arena cannot fall away.
            GetCharacterMovement()->DisableMovement();
            SetActorLocation(Enemy->EnemyAgent->GetHome()+FVector(State->ExitDistance,0,0),false);
        }
        if(State->Attacked && Enemy->EnemyAgent->GetEncounterEpoch()>0 && Enemy->EnemyAgent->State==ECombatEnemyState::Idle &&
            FVector::Dist2D(Enemy->EnemyAgent->GetHome(),Enemy->GetActorLocation())<=State->HomeTolerance)
        {
            State->Returned=true;
            State->Recovered=FMath::IsNearlyEqual(Enemy->Combat->GetHealth(),State->ExpectedHealth,.01f);
        }
    }),.1f,true);
    FTimerHandle Finish;
    GetWorldTimerManager().SetTimer(Finish,FTimerDelegate::CreateWeakLambda(this,[this,State,Seconds]()
    {
        const bool Passed=State->Valid && State->Chased && State->Damaged && State->Attacked && State->Returned &&
            State->Recovered && State->Cancelled && State->Detour>200;
        auto Json=MakeShared<FJsonObject>();
        Json->SetNumberField(TEXT("schema_version"),2);
        Json->SetBoolField(TEXT("passed"),Passed);
        Json->SetBoolField(TEXT("scenario_valid"),State->Valid);
        Json->SetStringField(TEXT("scenario_reason"),State->Reason);
        Json->SetBoolField(TEXT("chased"),State->Chased);
        Json->SetBoolField(TEXT("attacked"),State->Attacked);
        Json->SetBoolField(TEXT("returned"),State->Returned);
        Json->SetBoolField(TEXT("recovery_policy_matched"),State->Recovered);
        Json->SetBoolField(TEXT("return_cancelled_action"),State->Cancelled);
        Json->SetNumberField(TEXT("detour_y"),State->Detour);
        Json->SetNumberField(TEXT("scenario_seconds"),Seconds);
        Json->SetNumberField(TEXT("exit_distance"),State->ExitDistance);
        Json->SetNumberField(TEXT("home_tolerance"),State->HomeTolerance);
        Json->SetBoolField(TEXT("restore_on_return"),State->Restore);
        Json->SetNumberField(TEXT("expected_health"),State->ExpectedHealth);
        Json->SetNumberField(TEXT("actual_health"),State->ActualHealth);
        FString Report;
        FJsonSerializer::Serialize(Json,TJsonWriterFactory<TCHAR,TCondensedJsonPrintPolicy<TCHAR>>::Create(&Report));
        const FString Directory=FPaths::ProjectSavedDir()/TEXT("CombatAudit/20261004");
        IFileManager::Get().MakeDirectory(*Directory,true);
        FFileHelper::SaveStringToFile(Report,*(Directory/TEXT("encounter-review.json")));
        UE_LOG(LogTemp,Display,TEXT("COMBAT_ENCOUNTER_REVIEW %s"),*Report);
        if(auto* Enemy=State->Enemy.Get()) UE_LOG(LogTemp,Display,TEXT("COMBAT_ENCOUNTER_END state=%d decision=%s location=%s"),int32(Enemy->EnemyAgent->State),*Enemy->EnemyAgent->Decision,*Enemy->GetActorLocation().ToString());
        UKismetSystemLibrary::QuitGame(this,nullptr,EQuitPreference::Quit,false);
    }),Seconds,false);
}
#endif
