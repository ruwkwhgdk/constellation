#include "CombatLabCharacter.h"
#if !UE_BUILD_SHIPPING
#include "CombatAbilitySystem.h"
#include "CombatActionDefinition.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "EngineUtils.h"
#include "TimerManager.h"
#include "UnrealClient.h"
#include "Kismet/KismetSystemLibrary.h"
#include "HAL/FileManager.h"

void ACombatLabCharacter::ConfigureAutomatedReview()
{
    ConfigureMovementReview();
    ConfigureSpecialReview();
    ConfigureGroupReview();
    ConfigureVFXReview();
    ConfigureComboReview();
    ConfigureStaminaReview();
    ConfigureHitReview();
    ConfigureDodgeReview();
    ConfigurePatternReview();
    ConfigureEncounterReview();
    if (bTrainingEnemy || !FParse::Param(FCommandLine::Get(),TEXT("CombatCoreReview"))) return;
    FTimerHandle Start, Capture, Finish;
    GetWorldTimerManager().SetTimer(Start, FTimerDelegate::CreateWeakLambda(this,[this]()
    {
        for (TActorIterator<ACombatLabCharacter> It(GetWorld());It;++It)
            if (It->bTrainingEnemy)
            {
                SetActorLocation(It->GetActorLocation()-FVector(125,0,0),false);
                SetActorRotation(FRotator::ZeroRotator);
                Combat->TryStartAction(Action); break;
            }
    }),2.f,false);
    GetWorldTimerManager().SetTimer(Capture, FTimerDelegate::CreateWeakLambda(this,[]()
    {
        FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("CombatAudit/20261004/combat-core.png"),true,false);
    }),2.4f,false);
    GetWorldTimerManager().SetTimer(Finish, FTimerDelegate::CreateWeakLambda(this,[this]()
    {
        float EnemyHP=-1;
        for (TActorIterator<ACombatLabCharacter> It(GetWorld());It;++It)
            if (It->bTrainingEnemy) EnemyHP=It->Combat->GetHealth();
        const bool Passed=EnemyHP==80.f && Combat->GetHealth()<100.f && Combat->GetStamina()==100.f && !Combat->IsActing();
        const FString Report=FString::Printf(TEXT("{\"passed\":%s,\"player_hp\":%.1f,\"enemy_hp\":%.1f,\"stamina\":%.1f,\"player_acting\":%s}"),
            Passed?TEXT("true"):TEXT("false"),Combat->GetHealth(),EnemyHP,Combat->GetStamina(),Combat->IsActing()?TEXT("true"):TEXT("false"));
        const FString Directory=FPaths::ProjectSavedDir()/TEXT("CombatAudit/20261004");
        IFileManager::Get().MakeDirectory(*Directory,true);
        FFileHelper::SaveStringToFile(Report,*(Directory/TEXT("play-review.json")));
        UE_LOG(LogTemp,Display,TEXT("COMBAT_PLAY_REVIEW %s"),*Report);
        UKismetSystemLibrary::QuitGame(this,nullptr,EQuitPreference::Quit,false);
    }),7.f,false);
}
#endif
