#include "CombatLabCharacter.h"
#if !UE_BUILD_SHIPPING
#include "CombatAbilitySystem.h"
#include "GameFramework/PlayerController.h"
#include "Components/BoxComponent.h"
#include "InputKeyEventArgs.h"
#include "TimerManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Kismet/KismetSystemLibrary.h"
void ACombatLabCharacter::ConfigureDodgeReview()
{
    if(bTrainingEnemy || !FParse::Param(FCommandLine::Get(),TEXT("CombatDodgeReview"))) return;
    struct FState { FVector Start,WallStart; float OpenDistance=0,WallDistance=0; bool Immune=false,Cost=false,Ended=false; };
    const auto State=MakeShared<FState>();
    auto Schedule=[this](float Delay,FTimerDelegate Callback)
    { FTimerHandle Handle; GetWorldTimerManager().SetTimer(Handle,Callback,Delay,false); };
    for(float Time : {1.f,2.f})
    {
        Schedule(Time,FTimerDelegate::CreateWeakLambda(this,[this,State,Time]()
        {
            if(Time==1.f) State->Start=GetActorLocation();
            else State->WallStart=GetActorLocation();
            if(auto* PC=Cast<APlayerController>(Controller))
            {
                PC->SetControlRotation(FRotator(0,90,0));
                PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,IE_Pressed,1.f));
                PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::SpaceBar,IE_Pressed,1.f));
            }
        }));
        Schedule(Time+.03f,FTimerDelegate::CreateWeakLambda(this,[this]()
        {
            if(auto* PC=Cast<APlayerController>(Controller))
            {
                PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,IE_Released,0.f));
                PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::SpaceBar,IE_Released,0.f));
            }
        }));
    }
    Schedule(1.2f,FTimerDelegate::CreateWeakLambda(this,[this,State]()
    {
        State->Cost=Combat->GetStamina()==80.f;
        State->Immune=Combat->IsInvulnerable() && !Combat->ReceiveCombatDamage(20,nullptr) && Combat->GetHealth()==100.f;
    }));
    Schedule(1.75f,FTimerDelegate::CreateWeakLambda(this,[this,State]()
    {
        State->OpenDistance=GetActorLocation().Y-State->Start.Y;
        State->Ended=!Combat->IsDodging();
        auto* Wall=GetWorld()->SpawnActor<AActor>();
        auto* Box=NewObject<UBoxComponent>(Wall); Wall->SetRootComponent(Box);
        Box->SetBoxExtent(FVector(150,10,150)); Box->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Box->SetCollisionResponseToAllChannels(ECR_Block); Box->RegisterComponent();
        Wall->SetActorLocation(GetActorLocation()+FVector(0,120,0));
    }));
    Schedule(2.8f,FTimerDelegate::CreateWeakLambda(this,[this,State]()
    {
        State->WallDistance=GetActorLocation().Y-State->WallStart.Y;
        if(auto* PC=Cast<APlayerController>(Controller)) PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::LeftMouseButton,IE_Pressed,1.f));
    }));
    Schedule(2.83f,FTimerDelegate::CreateWeakLambda(this,[this]()
    { if(auto* PC=Cast<APlayerController>(Controller)) PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::LeftMouseButton,IE_Released,0.f)); }));
    Schedule(4.2f,FTimerDelegate::CreateWeakLambda(this,[this,State]()
    {
        const bool Passed=State->Cost && State->Immune && State->Ended && State->OpenDistance>200 && State->OpenDistance<270 &&
            State->WallDistance>1 && State->WallDistance<100 && Combat->GetExecutionId()==1 && !Combat->IsDodging() && !Combat->IsActing();
        const FString Report=FString::Printf(TEXT("{\"passed\":%s,\"cost\":%s,\"immune\":%s,\"ended\":%s,\"open_distance\":%.2f,\"wall_distance\":%.2f,\"attacks\":%llu}"),
            Passed?TEXT("true"):TEXT("false"),State->Cost?TEXT("true"):TEXT("false"),State->Immune?TEXT("true"):TEXT("false"),State->Ended?TEXT("true"):TEXT("false"),State->OpenDistance,State->WallDistance,Combat->GetExecutionId());
        FFileHelper::SaveStringToFile(Report,*(FPaths::ProjectSavedDir()/TEXT("CombatAudit/20261004/dodge-review.json")));
        UE_LOG(LogTemp,Display,TEXT("COMBAT_DODGE_REVIEW %s"),*Report);
        UKismetSystemLibrary::QuitGame(this,nullptr,EQuitPreference::Quit,false);
    }));
}
#endif
