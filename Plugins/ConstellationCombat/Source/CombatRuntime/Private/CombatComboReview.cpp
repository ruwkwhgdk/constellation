#include "CombatLabCharacter.h"
#if !UE_BUILD_SHIPPING
#include "CombatAttackInput.h"
#include "CombatAbilitySystem.h"
#include "GameFramework/PlayerController.h"
#include "InputKeyEventArgs.h"
#include "EngineUtils.h"
#include "TimerManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Kismet/KismetSystemLibrary.h"
#include "UnrealClient.h"
void ACombatLabCharacter::ConfigureComboReview()
{
    if(bTrainingEnemy || !FParse::Param(FCommandLine::Get(),TEXT("CombatComboReview"))) return;
    auto Schedule=[this](float Delay,FTimerDelegate Callback)
    { FTimerHandle Handle; GetWorldTimerManager().SetTimer(Handle,Callback,Delay,false); };
    Schedule(.8f,FTimerDelegate::CreateWeakLambda(this,[this]()
    {
        for(TActorIterator<ACombatLabCharacter> It(GetWorld());It;++It)
            if(It->bTrainingEnemy)
            {
                SetActorLocation(It->GetActorLocation()-FVector(125,0,0),false);
                SetActorRotation(FRotator::ZeroRotator); break;
            }
    }));
    for(float Time : {1.f,1.55f,1.60f,2.58f})
    {
        Schedule(Time,FTimerDelegate::CreateWeakLambda(this,[this]()
        { if(auto* PC=Cast<APlayerController>(Controller)) PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::LeftMouseButton,IE_Pressed,1.f)); }));
        Schedule(Time+.02f,FTimerDelegate::CreateWeakLambda(this,[this]()
        { if(auto* PC=Cast<APlayerController>(Controller)) PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::LeftMouseButton,IE_Released,0.f)); }));
    }
    Schedule(3.6f,FTimerDelegate::CreateWeakLambda(this,[]()
    { FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("CombatAudit/20261004/combat-combo.png"),true,false); }));
    Schedule(4.6f,FTimerDelegate::CreateWeakLambda(this,[this]()
    {
        float EnemyHP=-1;
        for(TActorIterator<ACombatLabCharacter> It(GetWorld());It;++It)
            if(It->bTrainingEnemy) EnemyHP=It->Combat->GetHealth();
        const bool Passed=Combat->GetExecutionId()==3 && Combat->GetStamina()==70 && EnemyHP==40 &&
            !Combat->IsActing() && !AttackInput->HasBufferedAttack();
        const FString Report=FString::Printf(TEXT("{\"passed\":%s,\"executions\":%llu,\"stamina\":%.1f,\"enemy_hp\":%.1f,\"buffered\":%s}"),
            Passed?TEXT("true"):TEXT("false"),Combat->GetExecutionId(),Combat->GetStamina(),EnemyHP,AttackInput->HasBufferedAttack()?TEXT("true"):TEXT("false"));
        FFileHelper::SaveStringToFile(Report,*(FPaths::ProjectSavedDir()/TEXT("CombatAudit/20261004/combo-review.json")));
        UE_LOG(LogTemp,Display,TEXT("COMBAT_COMBO_REVIEW %s"),*Report);
        UKismetSystemLibrary::QuitGame(this,nullptr,EQuitPreference::Quit,false);
    }));
}
#endif
