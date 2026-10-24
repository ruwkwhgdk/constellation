#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "TutorialPromptTestTypes.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "CombatLabCharacter.h"
#include "CombatAbilitySystem.h"
#include "CombatActionDefinition.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTutorialPromptRemovalTest,
 "Constellation.Audit.TutorialPrompt.NonblockingLifecycle",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FTutorialPromptRemovalTest::RunTest(const FString&)
{
 UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
 if(!TestNotNull(TEXT("Transient world"),World))return false;
 auto* PC=World->SpawnActor<ATutorialPromptTestController>();
 if(!TestNotNull(TEXT("Test controller"),PC)){World->DestroyWorld(false);return false;}
 auto* Player=NewObject<ULocalPlayer>(GEngine);Player->PlayerController=PC;PC->Player=Player;World->AddController(PC);
 auto MakePrompt=[World,PC]()
 {
  auto* Prompt=NewObject<UTutorialPromptTestWidget>(World);Prompt->SetOwningPlayer(PC);
  Prompt->TargetKeys={EKeys::SpaceBar};
  Prompt->OnTutorialPromptDismissed.AddDynamic(Prompt,&UTutorialPromptTestWidget::RecordDismissal);
  return Prompt;
 };
 PC->bShowMouseCursor=true;PC->LastInputMode=TEXT("Existing mode");
 auto* First=MakePrompt();First->ConstructForTest();
 TestTrue(TEXT("Cursor remains unchanged"),PC->bShowMouseCursor!=0);
 TestEqual(TEXT("Input mode remains unchanged"),PC->LastInputMode,FString(TEXT("Existing mode")));
 TestFalse(TEXT("Toast cannot receive focus"),First->IsFocusable());
 TestEqual(TEXT("Toast ignores pointer hit tests"),First->GetVisibility(),ESlateVisibility::HitTestInvisible);
 TestEqual(TEXT("Starts transparent"),First->GetRenderOpacity(),0.f);
 First->AdvanceForTest(.25f);TestEqual(TEXT("Fade in reaches full opacity"),First->GetRenderOpacity(),1.f);
 auto* Second=MakePrompt();Second->ConstructForTest();
 TestEqual(TEXT("Second toast does not dismiss first"),First->DismissCount,0);
 TestEqual(TEXT("First stack index"),First->StackIndexForTest(),0);
 TestEqual(TEXT("Second stack index"),Second->StackIndexForTest(),1);
 TestFalse(TEXT("Unrelated key unhandled"),First->KeyForTest(EKeys::Q));
 TestFalse(TEXT("Target key also unhandled"),First->KeyForTest(EKeys::SpaceBar));
 TestFalse(TEXT("Mouse events unhandled"),First->MouseForTest());
 TestEqual(TEXT("Raw key does not complete action"),First->DismissCount,0);
 First->NotifyTutorialActionCompleted(ETutorialPromptAction::Attack);
 First->AdvanceForTest(.1f);TestEqual(TEXT("Unrelated action ignored"),First->GetRenderOpacity(),1.f);
 First->NotifyTutorialActionCompleted(ETutorialPromptAction::Jump);
 First->Dismiss();TestEqual(TEXT("No completion before fade out"),First->DismissCount,0);
 First->AdvanceForTest(.175f);TestTrue(TEXT("Fade out is gradual"),First->GetRenderOpacity()>0&&First->GetRenderOpacity()<1);
 First->AdvanceForTest(.2f);First->Dismiss();First->AdvanceForTest(10);
 TestEqual(TEXT("Completed action dismisses exactly once"),First->DismissCount,1);
 TestEqual(TEXT("Remaining card reflows"),Second->StackIndexForTest(),0);
 Second->AdvanceForTest(8.25f);TestEqual(TEXT("Timeout starts fade before broadcast"),Second->DismissCount,0);
 Second->AdvanceForTest(.35f);TestEqual(TEXT("Timeout independently completes"),Second->DismissCount,1);
 First->ConstructForTest();First->ConstructForTest();
 TestEqual(TEXT("Repeated construct does not duplicate registration"),First->StackIndexForTest(),0);
 Second->ConstructForTest();TestEqual(TEXT("No hidden duplicate in stack"),Second->StackIndexForTest(),1);
 auto* OtherPC=World->SpawnActor<ATutorialPromptTestController>();
 auto* OtherPlayer=NewObject<ULocalPlayer>(GEngine);OtherPlayer->PlayerController=OtherPC;OtherPC->Player=OtherPlayer;World->AddController(OtherPC);
 auto* OtherPrompt=NewObject<UTutorialPromptTestWidget>(World);OtherPrompt->SetOwningPlayer(OtherPC);OtherPrompt->TargetKeys={EKeys::SpaceBar};OtherPrompt->ConstructForTest();
 TestEqual(TEXT("Other owning player has an independent stack"),OtherPrompt->StackIndexForTest(),0);
 UTutorialPromptWidget::NotifyPlayerTutorialActionCompleted(OtherPC,ETutorialPromptAction::Jump);
 OtherPrompt->AdvanceForTest(.4f);
 TestEqual(TEXT("Other player action leaves first stack active"),Second->StackIndexForTest(),1);
 OtherPrompt->DestructForTest();
 First->DestructForTest();First->AdvanceForTest(100);
 TestEqual(TEXT("External removal does not broadcast"),First->DismissCount,1);
 TestEqual(TEXT("External removal reflows"),Second->StackIndexForTest(),0);
 Second->FadeInSeconds=0;Second->HoldSeconds=0;Second->FadeOutSeconds=0;
 Second->DestructForTest();Second->ConstructForTest();Second->AdvanceForTest(0);
 TestEqual(TEXT("Zero duration completes once"),Second->DismissCount,2);
 TestEqual(TEXT("All lifecycle paths preserve input"),PC->LastInputMode,FString(TEXT("Existing mode")));
 TestEqual(TEXT("No input mode calls in any lifecycle path"),PC->InputModeCalls,0);
 TestTrue(TEXT("All lifecycle paths preserve cursor"),PC->bShowMouseCursor!=0);
 First->DestructForTest();Second->DestructForTest();World->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTutorialPromptActionObservationTest,
 "Constellation.Audit.TutorialPrompt.ActionObservation",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FTutorialPromptActionObservationTest::RunTest(const FString&)
{
 UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
 if(!TestNotNull(TEXT("Observation world"),World))return false;
 auto* PC=World->SpawnActor<ATutorialPromptTestController>();
 auto* Character=World->SpawnActor<ACharacter>(FVector(0,0,100),FRotator::ZeroRotator);
 if(!TestNotNull(TEXT("Observation controller"),PC)||!TestNotNull(TEXT("Observation character"),Character))
 {World->DestroyWorld(false);return false;}
 auto* Player=NewObject<ULocalPlayer>(GEngine);Player->PlayerController=PC;PC->Player=Player;World->AddController(PC);PC->Possess(Character);
 auto MakePrompt=[World,PC](FKey Key)
 {
  auto* Prompt=NewObject<UTutorialPromptTestWidget>(World);Prompt->SetOwningPlayer(PC);Prompt->TargetKeys={Key};
  Prompt->FadeInSeconds=0;Prompt->FadeOutSeconds=0;Prompt->HoldSeconds=100;
  Prompt->OnTutorialPromptDismissed.AddDynamic(Prompt,&UTutorialPromptTestWidget::RecordDismissal);
  Prompt->ConstructForTest();return Prompt;
 };
 auto* Movement=Character->GetCharacterMovement();
 auto* JumpPrompt=MakePrompt(EKeys::SpaceBar);
 JumpPrompt->KeyForTest(EKeys::SpaceBar);JumpPrompt->AdvanceForTest(.02f);
 TestEqual(TEXT("Space key without a jump does not complete"),JumpPrompt->DismissCount,0);
 Movement->SetMovementMode(MOVE_None);
 Character->Jump();Character->CheckJumpInput(.02f);JumpPrompt->AdvanceForTest(.02f);
 TestFalse(TEXT("Disabled movement rejects real jump attempt"),Character->bWasJumping!=0);
 TestEqual(TEXT("Rejected jump does not complete"),JumpPrompt->DismissCount,0);
 Character->StopJumping();Movement->SetMovementMode(MOVE_Walking);
 Character->Jump();Character->CheckJumpInput(.02f);
 TestTrue(TEXT("Engine jump produces positive airborne velocity"),Character->bWasJumping&&Movement->IsFalling()&&Movement->Velocity.Z>0);
 JumpPrompt->AdvanceForTest(.02f);
 TestEqual(TEXT("Actual engine jump completes tutorial"),JumpPrompt->DismissCount,1);
 JumpPrompt->DestructForTest();Character->StopJumping();Movement->SetMovementMode(MOVE_Walking);

 auto* MovePrompt=MakePrompt(EKeys::W);
 Character->AddMovementInput(FVector::ForwardVector,1.f,true);Character->ConsumeMovementInputVector();
 Movement->Velocity=FVector(100,0,0);MovePrompt->AdvanceForTest(.02f);
 TestEqual(TEXT("Movement input without displacement stays open"),MovePrompt->DismissCount,0);
 Character->ConsumeMovementInputVector(); // No pending input: clear last input before external displacement.
 Character->SetActorLocation(FVector(10,0,100));MovePrompt->AdvanceForTest(.02f);
 TestEqual(TEXT("External displacement without locomotion input stays open"),MovePrompt->DismissCount,0);
 Character->AddMovementInput(FVector::ForwardVector,1.f,true);Character->ConsumeMovementInputVector();
 Character->SetActorLocation(FVector(20,0,100));MovePrompt->AdvanceForTest(.02f);
 TestEqual(TEXT("Input plus actual pawn displacement completes movement"),MovePrompt->DismissCount,1);
 MovePrompt->DestructForTest();PC->UnPossess();Character->Destroy();

 // Reuse the real project's native combat character and authored compatible assets.
 auto* Fighter=World->SpawnActor<ACombatLabCharacter>(FVector(0,0,100),FRotator::ZeroRotator);
 if(!TestNotNull(TEXT("Combat observation character"),Fighter)){World->DestroyWorld(false);return false;}
 auto* Mesh=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/SK_player_heroine_new_RunPreview.SK_player_heroine_new_RunPreview"));
 auto* Action=LoadObject<UCombatActionDefinition>(nullptr,TEXT("/Game/Constellation/Review/CombatCore/DA_PlayerSlash.DA_PlayerSlash"));
 if(!TestNotNull(TEXT("Compatible combat mesh"),Mesh)||!TestNotNull(TEXT("Authored slash action"),Action)){World->DestroyWorld(false);return false;}
 Fighter->GetMesh()->SetSkeletalMeshAsset(Mesh);Fighter->GetMesh()->SetAnimationMode(EAnimationMode::AnimationSingleNode);Fighter->GetMesh()->InitAnim(true);
 Fighter->Combat->InitializeCombat(Fighter);Fighter->GetCharacterMovement()->SetMovementMode(MOVE_Walking);PC->Possess(Fighter);
 auto* AttackPrompt=MakePrompt(EKeys::LeftMouseButton);
 AttackPrompt->KeyForTest(EKeys::LeftMouseButton);AttackPrompt->AdvanceForTest(.02f);
 TestEqual(TEXT("Raw attack input cannot complete without execution"),AttackPrompt->DismissCount,0);
 TestFalse(TEXT("Invalid combat request rejected"),Fighter->Combat->TryStartAction(nullptr));AttackPrompt->AdvanceForTest(.02f);
 TestEqual(TEXT("Rejected combat request leaves tutorial open"),AttackPrompt->DismissCount,0);
 TestTrue(TEXT("Authored attack commits successfully"),Fighter->Combat->TryStartAction(Action));
 TestTrue(TEXT("Combat reports a committed active montage"),Fighter->Combat->ObserveAction().bActive);
 AttackPrompt->AdvanceForTest(.02f);
 TestEqual(TEXT("Committed attack completes tutorial"),AttackPrompt->DismissCount,1);
 AttackPrompt->DestructForTest();
 auto* AlreadyActingPrompt=MakePrompt(EKeys::LeftMouseButton);AlreadyActingPrompt->AdvanceForTest(.02f);
 TestEqual(TEXT("Attack predating the toast does not count"),AlreadyActingPrompt->DismissCount,0);
 AlreadyActingPrompt->DestructForTest();Fighter->Combat->CancelAction();World->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTutorialPromptVisibilityBudgetTest,
 "Constellation.Audit.TutorialPrompt.VisibilityBudget",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FTutorialPromptVisibilityBudgetTest::RunTest(const FString&)
{
 auto* World=UWorld::CreateWorld(EWorldType::Game,false);
 auto* PC=World->SpawnActor<ATutorialPromptTestController>();
 auto* Player=NewObject<ULocalPlayer>(GEngine);Player->PlayerController=PC;PC->Player=Player;World->AddController(PC);
 TArray<UTutorialPromptTestWidget*> Prompts;
 for(int32 I=0;I<4;++I)
 {
  auto* P=NewObject<UTutorialPromptTestWidget>(World);P->SetOwningPlayer(PC);
  P->TargetKeys={EKeys::SpaceBar};P->FadeInSeconds=0;P->FadeOutSeconds=0;P->HoldSeconds=8;
  P->OnTutorialPromptDismissed.AddDynamic(P,&UTutorialPromptTestWidget::RecordDismissal);
  P->ConstructForTest();Prompts.Add(P);
 }
 TestTrue(TEXT("Overflow toast waits instead of leaving the screen"),Prompts[2]->bQueued);
 Prompts[2]->AdvanceForTest(20);
 TestEqual(TEXT("Queued toast retains its reading time"),Prompts[2]->DismissCount,0);
 PC->SetIgnoreMoveInput(true);Prompts[0]->AdvanceForTest(20);
 TestEqual(TEXT("Cinematic input lock cannot expire a tutorial"),Prompts[0]->DismissCount,0);
 PC->ResetIgnoreMoveInput();Prompts[0]->AdvanceForTest(.1f);
 TestEqual(TEXT("Tutorial returns after input restoration"),Prompts[0]->GetVisibility(),ESlateVisibility::HitTestInvisible);
 Prompts[0]->SetVisibility(ESlateVisibility::Hidden);Prompts[0]->AdvanceForTest(20);
 TestEqual(TEXT("Externally hidden tutorial cannot expire"),Prompts[0]->DismissCount,0);
 TestEqual(TEXT("Cinematic owns its visibility"),Prompts[0]->GetVisibility(),ESlateVisibility::Hidden);
 Prompts[0]->SetVisibility(ESlateVisibility::HitTestInvisible);
 for(int32 I=0;I<2;++I)Prompts[I]->Dismiss();
 TestFalse(TEXT("Waiting tutorial is promoted"),Prompts[2]->bQueued);
 Prompts[2]->AdvanceForTest(7);
 TestEqual(TEXT("Promoted tutorial receives its full hold duration"),Prompts[2]->DismissCount,0);
 Prompts[2]->AdvanceForTest(2);
 TestEqual(TEXT("Promoted tutorial eventually expires"),Prompts[2]->DismissCount,1);
 for(auto* P:Prompts)P->DestructForTest();
 World->DestroyWorld(false);return true;
}
#endif
