#include "CombatLabCharacter.h"
#if !UE_BUILD_SHIPPING
#include "CombatAbilitySystem.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "InputKeyEventArgs.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "TimerManager.h"
#include "UnrealClient.h"
#include "Kismet/KismetSystemLibrary.h"

void ACombatLabCharacter::ConfigureMovementReview()
{
    if (bTrainingEnemy || !FParse::Param(FCommandLine::Get(),TEXT("CombatMovementReview"))) return;
    struct FReview
    {
        FVector Start, BeforeAttack;
        float Distance=0, Alignment=0, BlockedDistance=0, RecoveryDistance=0, CameraAlignment=0;
        bool bStarted=false, bRun=false, bMouseYaw=false, bMousePitch=false;
        float MouseYawBefore=0, MousePitchBefore=0;
    };
    const auto Review=MakeShared<FReview>();
    auto Schedule=[this](float Delay,FTimerDelegate Callback)
    { FTimerHandle Handle; GetWorldTimerManager().SetTimer(Handle,Callback,Delay,false); };
    Schedule(.2f,FTimerDelegate::CreateWeakLambda(this,[this,Review]()
    {
        if(auto* PC=Cast<APlayerController>(Controller))
        {
            Review->MouseYawBefore=PC->GetControlRotation().Yaw;
            PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::MouseX,IE_Axis,5.f));
        }
    }));
    Schedule(.4f,FTimerDelegate::CreateWeakLambda(this,[this,Review]()
    {
        if(auto* PC=Cast<APlayerController>(Controller))
        {
            Review->bMouseYaw=FMath::Abs(FMath::FindDeltaAngleDegrees(Review->MouseYawBefore,PC->GetControlRotation().Yaw))>.01f;
            Review->MousePitchBefore=PC->GetControlRotation().Pitch;
            PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::MouseY,IE_Axis,5.f));
        }
    }));
    Schedule(.6f,FTimerDelegate::CreateWeakLambda(this,[this,Review]()
    {
        if(auto* PC=Cast<APlayerController>(Controller))
            Review->bMousePitch=FMath::Abs(FMath::FindDeltaAngleDegrees(Review->MousePitchBefore,PC->GetControlRotation().Pitch))>.01f;
    }));

    Schedule(1.f,FTimerDelegate::CreateWeakLambda(this,[this,Review]()
    {
        SetActorLocation(FVector(-400,-400,100));
        if(auto* PC=Cast<APlayerController>(Controller))
        {
            PC->SetControlRotation(FRotator(-25,90,0));
            Review->Start=GetActorLocation();
            PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,IE_Pressed,1.f));
        }
    }));
    Schedule(2.f,FTimerDelegate::CreateWeakLambda(this,[this,Review]()
    {
        const FVector Travel=GetActorLocation()-Review->Start;
        Review->Distance=Travel.Size2D();
        Review->Alignment=FVector::DotProduct(Travel.GetSafeNormal2D(),FVector::YAxisVector);
        Review->CameraAlignment=FVector::DotProduct(Camera->GetForwardVector().GetSafeNormal2D(),FVector::YAxisVector);
    }));
    Schedule(2.3f,FTimerDelegate::CreateWeakLambda(this,[this,Review]()
    {
        Review->BeforeAttack=GetActorLocation();
        Review->bStarted=Combat->TryStartAction(Action);
        if(auto* PC=Cast<APlayerController>(Controller))
            PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,IE_Pressed,1.f));
    }));
    Schedule(2.7f,FTimerDelegate::CreateWeakLambda(this,[this,Review]()
    { Review->BlockedDistance=FVector::Dist2D(GetActorLocation(),Review->BeforeAttack); }));
    Schedule(3.9f,FTimerDelegate::CreateWeakLambda(this,[this,Review]()
    {
        Review->RecoveryDistance=FVector::Dist2D(GetActorLocation(),Review->BeforeAttack);
        auto* Single=GetMesh()->GetSingleNodeInstance();
        Review->bRun=Single && Single->GetCurrentAsset()==MoveAnimation;
        FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("CombatAudit/20261004/combat-movement.png"),true,false);
        if(auto* PC=Cast<APlayerController>(Controller))
            PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,IE_Released,0.f));
    }));
    Schedule(4.2f,FTimerDelegate::CreateWeakLambda(this,[this,Review]()
    {
        const bool Passed=Review->Distance>GetCharacterMovement()->MaxWalkSpeed*.7f && Review->Distance<GetCharacterMovement()->MaxWalkSpeed*1.1f && Review->Alignment>.99f &&
            Review->CameraAlignment>.99f && Review->BlockedDistance<.1f && Review->RecoveryDistance>35 &&
            Review->bStarted && Review->bRun && Review->bMouseYaw && Review->bMousePitch && !Combat->IsActing();
        UE_LOG(LogTemp,Display,TEXT("PROJECT_LOOK_REVIEW yaw=%d pitch=%d"),Review->bMouseYaw,Review->bMousePitch);
        const FString Report=FString::Printf(TEXT("{\"passed\":%s,\"distance_cm\":%.2f,\"input_camera_alignment\":%.4f,\"camera_alignment\":%.4f,\"attack_movement_cm\":%.2f,\"recovery_movement_cm\":%.2f,\"run_restored\":%s}"),
            Passed?TEXT("true"):TEXT("false"),Review->Distance,Review->Alignment,Review->CameraAlignment,
            Review->BlockedDistance,Review->RecoveryDistance,Review->bRun?TEXT("true"):TEXT("false"));
        FFileHelper::SaveStringToFile(Report,*(FPaths::ProjectSavedDir()/TEXT("CombatAudit/20261004/movement-review.json")));
        UE_LOG(LogTemp,Display,TEXT("COMBAT_MOVEMENT_REVIEW %s"),*Report);
        UKismetSystemLibrary::QuitGame(this,nullptr,EQuitPreference::Quit,false);
    }));
}
#endif
