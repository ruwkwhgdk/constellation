#include "CombatLabCharacter.h"
#if !UE_BUILD_SHIPPING
#include "CombatAbilitySystem.h"
#include "CombatAttackInput.h"
#include "CombatAttributes.h"
#include "GameFramework/PlayerController.h"
#include "InputKeyEventArgs.h"
#include "TimerManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Kismet/KismetSystemLibrary.h"
void ACombatLabCharacter::ConfigureStaminaReview()
{
    if(bTrainingEnemy || !FParse::Param(FCommandLine::Get(),TEXT("CombatStaminaReview"))) return;
    // One attack empties this fixture. The normal recovery settings remain enabled.

    const auto ObservedExhaustion=MakeShared<bool>(false);
    auto Schedule=[this](float Delay,FTimerDelegate Callback)
    { FTimerHandle Handle; GetWorldTimerManager().SetTimer(Handle,Callback,Delay,false); };
    for(float Time : {1.f,1.55f,2.3f,4.f})
    {
        Schedule(Time,FTimerDelegate::CreateWeakLambda(this,[this,Time]()
        {
            if(Time==1.f) Combat->SetNumericAttributeBase(UCombatAttributes::GetStaminaAttribute(),10.f);
            if(auto* PC=Cast<APlayerController>(Controller)) PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::LeftMouseButton,IE_Pressed,1.f));
        }));
        Schedule(Time+.02f,FTimerDelegate::CreateWeakLambda(this,[this]()
        { if(auto* PC=Cast<APlayerController>(Controller)) PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::LeftMouseButton,IE_Released,0.f)); }));
    }
    Schedule(2.4f,FTimerDelegate::CreateWeakLambda(this,[this,ObservedExhaustion]()
    {
        *ObservedExhaustion=Combat->GetExecutionId()==1 && Combat->GetStamina()==0.f &&
            !Combat->IsActing() && !AttackInput->HasBufferedAttack() && Combat->LastReason==TEXT("Not enough stamina");
    }));
    Schedule(6.5f,FTimerDelegate::CreateWeakLambda(this,[this,ObservedExhaustion]()
    {
        const bool Passed=*ObservedExhaustion && Combat->GetExecutionId()==2 && Combat->GetStamina()>=10.f &&
            !Combat->IsActing() && !AttackInput->HasBufferedAttack();
        const FString Report=FString::Printf(TEXT("{\"passed\":%s,\"observed_exhaustion\":%s,\"executions\":%llu,\"stamina\":%.2f}"),
            Passed?TEXT("true"):TEXT("false"),*ObservedExhaustion?TEXT("true"):TEXT("false"),Combat->GetExecutionId(),Combat->GetStamina());
        FFileHelper::SaveStringToFile(Report,*(FPaths::ProjectSavedDir()/TEXT("CombatAudit/20261004/stamina-review.json")));
        UE_LOG(LogTemp,Display,TEXT("COMBAT_STAMINA_REVIEW %s"),*Report);
        UKismetSystemLibrary::QuitGame(this,nullptr,EQuitPreference::Quit,false);
    }));
}
#endif
