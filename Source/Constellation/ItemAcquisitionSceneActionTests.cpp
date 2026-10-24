#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "ItemAcquisitionSceneAction.h"
#include "ItemAcquisitionSceneTestAction.h"
#include "ItemAcquisitionDefinition.h"
#include "ItemAcquisitionSubsystem.h"
#include "SceneDirectorPlayer.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/Texture2D.h"
#include "GameFramework/PlayerController.h"
#include "LevelSequence.h"
#include "MovieScene.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FItemAcquisitionSceneBridgeTest,"Constellation.ItemAcquisition.SceneBridge",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FItemAcquisitionSceneBridgeTest::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);
 auto* Scene=W->SpawnActor<ASceneDirectorPlayer>();
 auto* Action=NewObject<UItemAcquisitionSceneAction>();FString Error;
 TestFalse(TEXT("Missing definition rejects before acquiring input"),Action->Execute_Implementation(Scene,nullptr,FDirectorActionParameters(),Error));
 Action->Definition=NewObject<UItemAcquisitionDefinition>();
 TestFalse(TEXT("Stopped scene cannot queue a card"),Action->Execute_Implementation(Scene,nullptr,FDirectorActionParameters(),Error));
 TestEqual(TEXT("Invalid action has no queue side effects"),W->GetSubsystem<UItemAcquisitionSubsystem>()->PendingCount(),0);
 auto* Lease=NewObject<UItemAcquisitionSceneLease>(Scene);Scene->AddInstanceComponent(Lease);Lease->RegisterComponent();
 Lease->bPending=true;Lease->RequestId=FGuid::NewGuid();
 TestFalse(TEXT("Nested presentation rejected"),Lease->Begin(Action->Definition->Presentation,EKeys::Enter,Error));
 Lease->CancelPending();
 TestFalse(TEXT("Cancellation clears pending latch"),Lease->bPending);
 TestFalse(TEXT("Cancellation clears handle before callbacks"),Lease->RequestId.IsValid());
 Lease->CancelPending();
 Scene->SetDirectorPaused(true);TestTrue(TEXT("Pause getter preserves external ownership"),Scene->IsDirectorPaused());Scene->SetDirectorPaused(false);
 // An actual director tick crossing a game-action boundary must not fire the
 // following same-frame control or finish the sequence while the card waits.
 GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);
 W->SpawnActor<APlayerController>();
 auto* Data=NewObject<USceneDirectorAsset>();
 Data->GeneratedSequence=NewObject<ULevelSequence>(Data);Data->GeneratedSequence->Initialize();
 Data->GeneratedSequence->GetMovieScene()->SetTickResolutionDirectly(FFrameRate(30,1));
 Data->GeneratedSequence->GetMovieScene()->SetDisplayRate(FFrameRate(30,1));
 Data->GeneratedSequence->GetMovieScene()->SetPlaybackRange(0,60);Data->bNeedsCompile=false;
 FDirectorActionEntry Entry;Entry.Key=TEXT("Item");Entry.ActionClass=UItemAcquisitionSceneTestAction::StaticClass();Data->Actions.Add(Entry);
 FDirectorCue Show;Show.StartFrame=30;Show.EndFrame=30;Show.Step.Type=EDirectorNodeType::GameAction;Show.Step.ActionKey=TEXT("Item");
 FDirectorCue After;After.StartFrame=30;After.EndFrame=30;After.Step.Type=EDirectorNodeType::SetBool;After.Step.BoolKey=TEXT("AfterCard");After.Step.BoolValue=true;
 Data->Cues={Show,After};Scene->Director=Data;
 auto* Defaults=GetMutableDefault<UItemAcquisitionSceneAction>();
 TGuardValue<TObjectPtr<UItemAcquisitionDefinition>> RestoreDefinition(Defaults->Definition,Action->Definition);
 auto& P=Action->Definition->Presentation;P.Sprite=NewObject<UTexture2D>();P.Name=FText::FromString(TEXT("Test"));P.Description=FText::FromString(TEXT("Test only"));
 TestTrue(TEXT("Fixture starts"),Scene->PlayDirector());
 FDirectorActionParameters InvalidAmount;InvalidAmount.Amount=0;
 TestFalse(TEXT("Zero quantity rejected"),Action->Execute_Implementation(Scene,nullptr,InvalidAmount,Error));
 InvalidAmount.Amount=-1;
 TestFalse(TEXT("Negative quantity rejected"),Action->Execute_Implementation(Scene,nullptr,InvalidAmount,Error));
 TestEqual(TEXT("Invalid quantity queues nothing"),W->GetSubsystem<UItemAcquisitionSubsystem>()->PendingCount(),0);
 TestFalse(TEXT("Invalid quantity does not pause scene"),Scene->IsDirectorPaused());
 Scene->Tick(4.f);
 TestTrue(*FString::Printf(TEXT("Authored action accepted: %s"),*Scene->LastError),Scene->ActionResults.Num()==1&&Scene->ActionResults[0].bSucceeded);
 TestTrue(TEXT("Hitch stops at item action without natural completion"),Scene->IsDirectorPlaying()&&Scene->IsDirectorPaused());
 TestFalse(TEXT("Same-frame next node waits"),Scene->BoolValues.FindRef(TEXT("AfterCard")));
 const FGuid PendingId=Lease->RequestId;Lease->Resolve(true);W->GetSubsystem<UItemAcquisitionSubsystem>()->Cancel(PendingId);
 TestFalse(TEXT("Confirmation restores prior unpaused state"),Scene->IsDirectorPaused());Scene->Tick(.01f);
 TestTrue(TEXT("Next node runs after confirmation"),Scene->BoolValues.FindRef(TEXT("AfterCard")));
 Scene->StopDirector();
 TestTrue(TEXT("Cancellation fixture starts"),Scene->PlayDirector());Scene->Tick(1.f);
 W->GetSubsystem<UItemAcquisitionSubsystem>()->Cancel(Lease->RequestId);
 TestFalse(TEXT("Cancellation stops rather than advances event"),Scene->IsDirectorPlaying());
 TestFalse(TEXT("Cancelled event never reaches following node"),Scene->BoolValues.FindRef(TEXT("AfterCard")));
 TestTrue(TEXT("External pause fixture starts"),Scene->PlayDirector());Scene->SetDirectorPaused(true);
 TestTrue(TEXT("Presentation accepts an already paused scene"),Lease->Begin(P,FKey(),Error));
 const FGuid ExternalId=Lease->RequestId;Lease->Resolve(true);W->GetSubsystem<UItemAcquisitionSubsystem>()->Cancel(ExternalId);
 TestTrue(TEXT("Confirmation preserves external pause"),Scene->IsDirectorPaused());Scene->SetDirectorPaused(false);Scene->Tick(1.f);
 Scene->StopDirector();
 TestEqual(TEXT("Director stop removes its queued card"),W->GetSubsystem<UItemAcquisitionSubsystem>()->PendingCount(),0);
 Data->Actions[0].ActionClass=UItemAcquisitionNonblockingTestAction::StaticClass();
 Data->Cues[1].StartFrame=45;Data->Cues[1].EndFrame=45;
 TestTrue(TEXT("Ordinary action fixture starts"),Scene->PlayDirector());Scene->Tick(1.5f);
 TestTrue(TEXT("Ordinary actions preserve full tick delta across their boundary"),Scene->BoolValues.FindRef(TEXT("AfterCard")));
 Scene->StopDirector();
 W->DestroyWorld(false);GEngine->DestroyWorldContext(W);return true;
}
#endif
