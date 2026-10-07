#include "CarryEditorLibrary.h"
#include "Editor.h"
#include "PlayInEditorDataTypes.h"
#include "Engine/World.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/PlayerController.h"
#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "UnrealClient.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"

void UCarryEditorLibrary::StartCarryReviewPlay()
{
    if(!GEditor||GEditor->PlayWorld) return;
    FRequestPlaySessionParams Params; Params.bAllowOnlineSubsystem=false;
    GEditor->RequestPlaySession(Params);
}
AActor* UCarryEditorLibrary::GetCarryReviewPawn()
{
    APlayerController* PC=GEditor&&GEditor->PlayWorld?GEditor->PlayWorld->GetFirstPlayerController():nullptr;
    return PC?PC->GetPawn():nullptr;
}
bool UCarryEditorLibrary::InjectCarryReviewInput(const FString& ActionPath,FVector Value)
{
    APlayerController* PC=GEditor&&GEditor->PlayWorld?GEditor->PlayWorld->GetFirstPlayerController():nullptr;
    const UInputAction* Action=LoadObject<UInputAction>(nullptr,*ActionPath);
    UEnhancedInputLocalPlayerSubsystem* Input=PC&&PC->GetLocalPlayer()?PC->GetLocalPlayer()->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>():nullptr;
    if(!Input||!Action) return false;
    Input->InjectInputVectorForAction(Action,Value,{},{}); return true;
}
void UCarryEditorLibrary::CaptureCarryReview(const FString& Filename,bool bShowUI)
{
    FScreenshotRequest::RequestScreenshot(Filename,bShowUI,false);
}
void UCarryEditorLibrary::UseCarryReviewCamera(bool bCloseUp)
{
    APlayerController* PC=GEditor&&GEditor->PlayWorld?GEditor->PlayWorld->GetFirstPlayerController():nullptr;
    if(!PC||!PC->GetPawn()) return;
    if(!bCloseUp) { PC->SetViewTarget(PC->GetPawn()); return; }
    const FVector Target=PC->GetPawn()->GetActorLocation()+FVector(0,0,10);
    const FVector Position=PC->GetPawn()->GetActorLocation()+FVector(300,-280,160);
    ACameraActor* Camera=GEditor->PlayWorld->SpawnActor<ACameraActor>(Position,(Target-Position).Rotation());
    Camera->GetCameraComponent()->SetFieldOfView(50); PC->SetViewTarget(Camera);
}
