#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "HAL/IConsoleManager.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorSkipContractTest,"Constellation.SceneDirector.Skip.Contract",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorSkipContractTest::RunTest(const FString&)
{
 return TestNotNull(TEXT("Editor cinematic skip switch registered"),IConsoleManager::Get().FindConsoleVariable(TEXT("SceneDirector.SkipCinematics")));
}
#include "SceneDirectorTesting.h"
#include "SceneEventSubsystem.h"
#include "SceneEventBinding.h"
#include "SceneDirectorPlayer.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Misc/ScopeExit.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/HUD.h"
#include "Camera/CameraActor.h"
#include "Camera/PlayerCameraManager.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorSkipScopeTest,"Constellation.SceneDirector.Skip.Scope",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorSkipScopeTest::RunTest(const FString&)
{
 const bool Before=DirectorTesting::IsSkipEnabled();
 ON_SCOPE_EXIT{DirectorTesting::SetSkipEnabled(Before);};
 DirectorTesting::SetSkipEnabled(true);
 UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);
 ON_SCOPE_EXIT{W->DestroyWorld(false);};
 for(auto Type:{EWorldType::Game,EWorldType::Editor,EWorldType::EditorPreview,EWorldType::GamePreview})
 {W->WorldType=Type;TestFalse(TEXT("Non-PIE worlds unaffected"),DirectorTesting::ShouldSkip(W));}
 W->WorldType=EWorldType::PIE;
 TestTrue(TEXT("PIE and SIE skipped"),DirectorTesting::ShouldSkip(W));
 TestFalse(TEXT("Null world unaffected"),DirectorTesting::ShouldSkip(nullptr));
 DirectorTesting::SetSkipEnabled(false);
 TestFalse(TEXT("Toggle off restores playback"),DirectorTesting::ShouldSkip(W));
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorSkipRequestsTest,"Constellation.SceneDirector.Skip.Requests",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorSkipRequestsTest::RunTest(const FString&)
{
 const bool Before=DirectorTesting::IsSkipEnabled();
 UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);
 GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);
 W->InitializeActorsForPlay(FURL());
 auto* PC=W->SpawnActor<APlayerController>();
 if(!PC->PlayerCameraManager){PC->PlayerCameraManager=W->SpawnActor<APlayerCameraManager>();PC->PlayerCameraManager->InitializeFor(PC);}
 PC->ClientSetHUD(AHUD::StaticClass());
 auto* Pawn=W->SpawnActor<APawn>();PC->Possess(Pawn);
 auto* GameplayCamera=W->SpawnActor<ACameraActor>();PC->SetViewTarget(GameplayCamera);
 auto* S=W->GetSubsystem<USceneEventSubsystem>();
 ON_SCOPE_EXIT{S->CancelActive();W->WorldType=EWorldType::Game;GEngine->DestroyWorldContext(W);W->DestroyWorld(false);DirectorTesting::SetSkipEnabled(Before);};
 auto* Asset=NewObject<USceneDirectorAsset>();Asset->EventKey=TEXT("SkipTest");
 for(auto Type:{EDirectorNodeType::Start,EDirectorNodeType::Wait,EDirectorNodeType::End})
 {FDirectorStep Step;Step.Type=Type;Step.Duration=1;Asset->Steps.Add(Step);}
 for(int I=0;I<2;++I)Asset->Steps[I].NextNodes={Asset->Steps[I+1].Id};
 FString Error;TestTrue(TEXT("Valid compiled graph"),FSceneDirectorCompiler::Compile(*Asset,Error));
 W->WorldType=EWorldType::PIE;DirectorTesting::SetSkipEnabled(true);
 ASceneEventBinding* Replay=nullptr;
 for(auto Trigger:{ESceneEventTrigger::LevelReady,ESceneEventTrigger::Volume,ESceneEventTrigger::Interaction,ESceneEventTrigger::Combat,ESceneEventTrigger::Destroyed,ESceneEventTrigger::LegacySequence})
 {
  auto* B=W->SpawnActor<ASceneEventBinding>();B->Trigger=Trigger;B->Director=Asset;B->CombatKey=TEXT("Fight");B->Repeat=ESceneEventRepeat::OncePerVisit;S->Register(B);
  TestFalse(TEXT("Every trigger skipped"),S->Request(B,TEXT("Signal")));
  TestFalse(TEXT("Skipped event never consumed"),S->IsConsumed(B->EventId));
  if(Trigger==ESceneEventTrigger::Combat)Replay=B;
 }
 TestEqual(TEXT("Nothing queued"),S->PendingCount(),0);
 TestNull(TEXT("No event runner created"),S->ActivePlayer.Get());
 TestNull(TEXT("Direct subsystem call skipped"),S->Start(Asset,TEXT("Direct"),FTransform::Identity,false,{},Error));
 auto* R=W->SpawnActor<ASceneDirectorPlayer>();R->bAutoPlay=false;R->Director=Asset;
 TestFalse(TEXT("Direct player skipped"),R->PlayDirector());
 TestFalse(TEXT("No playback started"),R->IsDirectorPlaying());R->Destroy();
 DirectorTesting::SetSkipEnabled(false);
 TestTrue(TEXT("Same one-shot and signal can play when enabled"),S->Request(Replay,TEXT("Signal")));
 TestNotNull(TEXT("Playback restored"),S->ActivePlayer.Get());
 if(auto* Active=S->ActivePlayer.Get())
 {
  Active->SetInputLocked(true);Active->SetHUDHidden(true);Active->SetPlayerHidden(true);
  PC->SetViewTarget(W->SpawnActor<ACameraActor>());
  TestTrue(TEXT("Input locked before skip"),PC->IsMoveInputIgnored()&&PC->IsLookInputIgnored());
  TestTrue(TEXT("Player hidden before skip"),Pawn->IsHidden());
  if(TestNotNull(TEXT("HUD exists"),PC->GetHUD()))TestFalse(TEXT("HUD hidden before skip"),PC->GetHUD()->bShowHUD);
  // Paused directors must be stopped synchronously, without waiting for playback Tick.
  Active->bDirectorPaused=true;
  DirectorTesting::SetSkipEnabled(true);
  TestNull(TEXT("Active event cleared immediately"),S->ActivePlayer.Get());
  TestFalse(TEXT("Interrupted event is not completed"),S->IsConsumed(Replay->EventId));
  TestTrue(TEXT("Gameplay camera restored"),PC->GetViewTarget()==GameplayCamera);
  TestFalse(TEXT("Movement unlocked"),PC->IsMoveInputIgnored());
  TestFalse(TEXT("Look unlocked"),PC->IsLookInputIgnored());
  TestFalse(TEXT("Player visible again"),Pawn->IsHidden());
  if(PC->GetHUD())TestTrue(TEXT("HUD restored"),PC->GetHUD()->bShowHUD);
  DirectorTesting::SetSkipEnabled(false);
  TestTrue(TEXT("Cancelled event can run after toggle off"),S->Request(Replay,TEXT("Signal")));
 }
 return true;
}
#endif
