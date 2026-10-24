#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "PhoneMenuComponent.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "Camera/CameraActor.h"
#include "Camera/PlayerCameraManager.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPhoneMenuCleanupTest,"Constellation.PhoneMenu.ApprovalAndCleanup",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FPhoneMenuCleanupTest::RunTest(const FString&)
{
 auto* World=UWorld::CreateWorld(EWorldType::Game,false);
 GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
 auto* C=World->SpawnActor<ACharacter>();
 auto* PC=World->SpawnActor<APlayerController>();PC->Possess(C);
 PC->PlayerCameraManager=World->SpawnActor<APlayerCameraManager>();
 PC->PlayerCameraManager->InitializeFor(PC);
 auto* M=NewObject<UPhoneMenuComponent>(C);C->AddInstanceComponent(M);M->RegisterComponent();
 M->Character=C;M->Controller=PC;
 M->ApprovedPhoneTrack={FTransform(FVector(1,2,3)),FTransform(FVector(3,4,5))};
 TestTrue(TEXT("Approved prop sampling interpolates"),M->SamplePhonePose(1.5f).GetTranslation().Equals(FVector(2,3,4)));
 TestTrue(TEXT("Approved prop sampling clamps last frame"),M->SamplePhonePose(500).GetTranslation().Equals(FVector(3,4,5)));
 M->ApprovedPhoneTrack.Reset();
 TestFalse(TEXT("Unapproved animation fails closed"),M->CanOpen());
 M->ToggleMenu();TestFalse(TEXT("No lock without approved assets"),PC->IsMoveInputIgnored());
 PC->SetIgnoreMoveInput(true);PC->SetIgnoreLookInput(true);
 // This menu owns exactly one additional lock, never the preexisting owner's lock.
 PC->SetIgnoreMoveInput(true);PC->SetIgnoreLookInput(true);
 M->bLocked=true;M->bOldCursor=false;PC->bShowMouseCursor=true;
 M->Flow.RequestOpen(true,0);M->Applied=PhoneMenu::Phase::Preparing;
 auto* NewCamera=World->SpawnActor<ACameraActor>();PC->SetViewTarget(NewCamera);
 M->MenuCamera=World->SpawnActor<ACameraActor>();M->PreviousView=C;
 M->CancelMenu();
 TestTrue(TEXT("Other movement lock remains"),PC->IsMoveInputIgnored());
 TestTrue(TEXT("Other look lock remains"),PC->IsLookInputIgnored());
 TestTrue(TEXT("New cinematic camera not overwritten"),PC->GetViewTarget()==NewCamera);
 TestTrue(TEXT("New UI cursor not overwritten when menu no longer owns UI"),PC->bShowMouseCursor!=0);
 M->CancelMenu();
 TestTrue(TEXT("Repeated cleanup cannot release another lock"),PC->IsMoveInputIgnored());
 M->NotifyPhoneEvent(EPhoneMenuEvent::Drawn,M->GetMenuToken());
 TestFalse(TEXT("Late signal does not reopen"),M->BlocksGameplay());
 PC->SetIgnoreMoveInput(false);PC->SetIgnoreLookInput(false);
 TestFalse(TEXT("Exactly one foreign lock remained"),PC->IsMoveInputIgnored());
 auto* NewPawn=World->SpawnActor<ACharacter>();PC->Possess(NewPawn);
 M->PreviousView=C;M->MenuCamera=World->SpawnActor<ACameraActor>();PC->SetViewTarget(M->MenuCamera);
 M->Cleanup();
 TestTrue(TEXT("Possession change restores new pawn, not stale pawn"),PC->GetViewTarget()==NewPawn);
 World->DestroyWorld(false);GEngine->DestroyWorldContext(World);return true;
}
#endif
