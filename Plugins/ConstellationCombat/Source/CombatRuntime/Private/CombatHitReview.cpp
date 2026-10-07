#include "CombatLabCharacter.h"
#if !UE_BUILD_SHIPPING
#include "CombatAbilitySystem.h"
#include "CombatAttackInput.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "InputKeyEventArgs.h"
#include "TimerManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Kismet/KismetSystemLibrary.h"
void ACombatLabCharacter::ConfigureHitReview()
{
    if(bTrainingEnemy || !FParse::Param(FCommandLine::Get(),TEXT("CombatHitReview"))) return;
    struct FObserved { bool Interrupted=false,Blocked=false; FVector HitLocation; };
    const auto Observed=MakeShared<FObserved>();
    auto Schedule=[this](float Delay,FTimerDelegate Callback)
    { FTimerHandle Handle; GetWorldTimerManager().SetTimer(Handle,Callback,Delay,false); };
    for(float Time : {1.f,1.55f,1.8f,2.3f})
    {
        Schedule(Time,FTimerDelegate::CreateWeakLambda(this,[this]()
        { if(auto* PC=Cast<APlayerController>(Controller)) PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::LeftMouseButton,IE_Pressed,1.f)); }));
        Schedule(Time+.02f,FTimerDelegate::CreateWeakLambda(this,[this]()
        { if(auto* PC=Cast<APlayerController>(Controller)) PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::LeftMouseButton,IE_Released,0.f)); }));
    }
    Schedule(1.65f,FTimerDelegate::CreateWeakLambda(this,[this,Observed]()
    {
        const bool HadQueue=AttackInput->HasBufferedAttack();
        Combat->ReceiveCombatDamage(10,nullptr);
        Observed->HitLocation=GetActorLocation();
        Observed->Interrupted=HadQueue && Combat->IsHitReacting() && !Combat->IsActing() && !AttackInput->HasBufferedAttack();
        if(auto* PC=Cast<APlayerController>(Controller)) PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,IE_Pressed,1.f));
    }));
    Schedule(1.9f,FTimerDelegate::CreateWeakLambda(this,[this,Observed]()
    {
        Observed->Blocked=Combat->GetExecutionId()==1 && Combat->IsHitReacting() &&
            FVector::Dist2D(Observed->HitLocation,GetActorLocation())<1.f;
    }));
    Schedule(2.2f,FTimerDelegate::CreateWeakLambda(this,[this]()
    { if(auto* PC=Cast<APlayerController>(Controller)) PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,IE_Released,0.f)); }));
    Schedule(4.7f,FTimerDelegate::CreateWeakLambda(this,[this,Observed]()
    {
        const bool Moved=FVector::Dist2D(Observed->HitLocation,GetActorLocation())>5.f;
        const bool Passed=Observed->Interrupted && Observed->Blocked && Moved && Combat->GetExecutionId()==2 &&
            Combat->GetHealth()==90 && Combat->GetStamina()>80 && !Combat->IsActing() && !Combat->IsHitReacting() && !AttackInput->HasBufferedAttack();
        const FString Report=FString::Printf(TEXT("{\"passed\":%s,\"interrupted\":%s,\"blocked_during_reaction\":%s,\"movement_resumed\":%s,\"executions\":%llu,\"hp\":%.1f,\"sp\":%.2f}"),
            Passed?TEXT("true"):TEXT("false"),Observed->Interrupted?TEXT("true"):TEXT("false"),Observed->Blocked?TEXT("true"):TEXT("false"),Moved?TEXT("true"):TEXT("false"),Combat->GetExecutionId(),Combat->GetHealth(),Combat->GetStamina());
        FFileHelper::SaveStringToFile(Report,*(FPaths::ProjectSavedDir()/TEXT("CombatAudit/20261004/hit-review.json")));
        UE_LOG(LogTemp,Display,TEXT("COMBAT_HIT_REVIEW %s"),*Report);
        UKismetSystemLibrary::QuitGame(this,nullptr,EQuitPreference::Quit,false);
    }));
}
#endif
