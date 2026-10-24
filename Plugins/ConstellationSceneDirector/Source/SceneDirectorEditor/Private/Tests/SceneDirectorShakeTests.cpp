#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorNodeMenu.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorShakeRegistrationTest,"Constellation.SceneDirector.CameraShake.Registration",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorShakeRegistrationTest::RunTest(const FString&)
{
 auto* Types=StaticEnum<EDirectorNodeType>();
 for(const TCHAR* Name:{TEXT("CameraShake"),TEXT("StopCameraShake")})
 {
  const int64 Value=Types->GetValueByNameString(Name);
  TestTrue(FString(Name)+TEXT(" is a serialized node type"),Value!=INDEX_NONE);
  TestTrue(FString(Name)+TEXT(" is in the creation menu"),DirectorNodeMenuEntries().ContainsByPredicate([&](const FDirectorNodeMenuEntry& E){return int64(E.Type)==Value;}));
 }
 return true;
}
#include "SceneDirectorCompiler.h"
#include "SceneDirectorPlayer.h"
#include "Camera/CameraActor.h"
#include "Camera/PlayerCameraManager.h"
#include "GameFramework/PlayerController.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
static USceneDirectorAsset* ShakeFixture()
{
 auto* A=NewObject<USceneDirectorAsset>();
 for(auto T:{EDirectorNodeType::Start,EDirectorNodeType::CameraShake,EDirectorNodeType::Wait,EDirectorNodeType::StopCameraShake,EDirectorNodeType::Wait,EDirectorNodeType::End}){FDirectorStep S;S.Type=T;S.Duration=1;A->Steps.Add(S);}
 for(int32 I=0;I<A->Steps.Num()-1;++I)A->Steps[I].NextNodes={A->Steps[I+1].Id};
 A->Steps[1].Shake.bUnlimited=true;A->Steps[1].Shake.BlendIn=0;return A;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorShakeScheduleTest,"Constellation.SceneDirector.CameraShake.Schedule",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorShakeScheduleTest::RunTest(const FString&)
{
 auto* A=ShakeFixture();FDirectorSchedule P;FString Error;
 if(!TestTrue(TEXT("Unlimited start and stop compile"),FSceneDirectorCompiler::Compile(*A,Error))){AddError(Error);return false;}
 TestTrue(TEXT("Schedule"),FSceneDirectorCompiler::Schedule(*A,P,Error));
 TestEqual(TEXT("Unlimited ignores completion wait"),P.StartFrames[2],0);
 TestEqual(TEXT("Stop at one second"),P.StartFrames[3],30);
 A->Steps[1].Shake.bUnlimited=false;A->Steps[1].Shake.Duration=2;
 TestTrue(TEXT("Finite schedule"),FSceneDirectorCompiler::Schedule(*A,P,Error));TestEqual(TEXT("Finite waits"),P.StartFrames[2],60);
 A->Steps[1].bWaitForCompletion=false;
 TestTrue(TEXT("Nonblocking finite schedule"),FSceneDirectorCompiler::Schedule(*A,P,Error));TestEqual(TEXT("Finite can overlap"),P.StartFrames[2],0);
 A->Steps[1].bShakeCurrentCamera=false;A->Steps[1].CameraKey=TEXT("Missing");TestFalse(TEXT("Unknown target rejected"),FSceneDirectorCompiler::Schedule(*A,P,Error));
 A->Steps[1].bShakeCurrentCamera=true;A->Steps[1].Shake.Frequency=-1;TestFalse(TEXT("Negative frequency rejected"),FSceneDirectorCompiler::Schedule(*A,P,Error));
 A->Steps[1].Shake.Frequency=8;A->Steps[1].Shake.Direction=EDirectorShakeDirection::Custom;A->Steps[1].Shake.CustomDirection=FVector::ZeroVector;TestFalse(TEXT("Zero direction rejected"),FSceneDirectorCompiler::Schedule(*A,P,Error));
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorShakeStateTest,"Constellation.SceneDirector.CameraShake.State",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorShakeStateTest::RunTest(const FString&)
{
 FDirectorStep S;S.Type=EDirectorNodeType::CameraShake;S.bShakeCurrentCamera=false;S.CameraKey=TEXT("A");S.Shake.bUnlimited=true;S.Shake.BlendIn=0;S.Shake.Direction=EDirectorShakeDirection::Vertical;
 FDirectorShakeState State;State.Execute(S);State.Advance(4000);
 TestEqual(TEXT("Unlimited survives time"),State.Num(),1);
 TestTrue(TEXT("Other camera unaffected"),State.Sample(TEXT("B")).Location.IsZero());
 const auto O=State.Sample(TEXT("A"));TestTrue(TEXT("Vertical only"),O.Location.X==0&&O.Location.Y==0);TestTrue(TEXT("Amplitude bounded"),O.Location.Size()<=S.Shake.TranslationRange);
 State.Execute(S);TestEqual(TEXT("Same target replaces"),State.Num(),1);
 S.CameraKey=TEXT("B");State.Execute(S);TestEqual(TEXT("Distinct targets independent"),State.Num(),2);
 FDirectorStep Stop;Stop.Type=EDirectorNodeType::StopCameraShake;Stop.bStopAllCameraShakes=false;Stop.bShakeCurrentCamera=false;Stop.CameraKey=TEXT("A");Stop.StopShakeSeconds=.5f;State.Execute(Stop);State.Advance(.5);
 TestEqual(TEXT("Only A stopped"),State.Num(),1);TestTrue(TEXT("A fully restored"),State.Sample(TEXT("A")).Location.IsZero());
 Stop.bStopAllCameraShakes=true;Stop.StopShakeSeconds=0;State.Execute(Stop);TestEqual(TEXT("Stop all"),State.Num(),0);
 auto* A=ShakeFixture();FString Error;TestTrue(TEXT("Compile preview cues"),FSceneDirectorCompiler::Compile(*A,Error));
 auto Preview=FDirectorShakeState::At(A->Cues,.3);TestEqual(TEXT("Preview active"),Preview.Num(),1);
 TestEqual(TEXT("Preview stop is applied while scrubbing"),FDirectorShakeState::At(A->Cues,1.5).Num(),0);
 TestTrue(TEXT("Backward seek deterministic"),Preview.Sample(NAME_None).Location.Equals(FDirectorShakeState::At(A->Cues,.3).Sample(NAME_None).Location));
 S.bShakeCurrentCamera=true;S.Shake.bUnlimited=false;S.Shake.Duration=.5;State.Execute(S);State.Advance(.5);TestEqual(TEXT("Finite expires"),State.Num(),0);
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorShakeRuntimeTest,"Constellation.SceneDirector.CameraShake.Runtime",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorShakeRuntimeTest::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());
 auto* PC=W->SpawnActor<APlayerController>();if(!PC->PlayerCameraManager){PC->PlayerCameraManager=W->SpawnActor<APlayerCameraManager>();PC->PlayerCameraManager->InitializeFor(PC);}
 auto* Camera=W->SpawnActor<ACameraActor>();Camera->SetActorLocation(FVector(100,200,300));PC->SetViewTarget(Camera);
 const FTransform Original=Camera->GetActorTransform();auto* Runner=W->SpawnActor<ASceneDirectorPlayer>();Runner->bAutoPlay=false;Runner->Director=ShakeFixture();FString Error;
 TestTrue(TEXT("Runtime compile"),FSceneDirectorCompiler::Compile(*Runner->Director,Error));TestTrue(TEXT("Runtime start"),Runner->PlayDirector());Runner->Tick(.123f);
 TestEqual(TEXT("Active"),Runner->GetActiveCameraShakeCount(),1);
 auto* Modifier=PC->PlayerCameraManager->FindCameraModifierByClass(UDirectorCameraShakeModifier::StaticClass());
 if(TestNotNull(TEXT("Owned POV modifier installed"),Modifier))
 {
  FMinimalViewInfo P;P.Location=Original.GetLocation();const auto Base=P;Modifier->ModifyCamera(.016f,P);
  TestFalse(TEXT("Rendered view oscillates"),P.Location.Equals(Base.Location));
  TestTrue(TEXT("Camera actor remains unchanged"),Camera->GetActorTransform().Equals(Original));
 }
 Runner->Tick(1);TestEqual(TEXT("Stop cue clears"),Runner->GetActiveCameraShakeCount(),0);Runner->StopDirector();
 TestNull(TEXT("Cancellation removes only owned modifier"),PC->PlayerCameraManager->FindCameraModifierByClass(UDirectorCameraShakeModifier::StaticClass()));
 TestTrue(TEXT("Replay"),Runner->PlayDirector());Runner->StopDirector();TestEqual(TEXT("Replay cleanup"),Runner->GetActiveCameraShakeCount(),0);
 Runner->PlayDirector();Runner->Tick(3);TestFalse(TEXT("Natural finish"),Runner->IsDirectorPlaying());TestEqual(TEXT("Natural finish cleanup"),Runner->GetActiveCameraShakeCount(),0);
 Runner->Director=ShakeFixture();auto& Dialogue=Runner->Director->Steps[2];Dialogue.Type=EDirectorNodeType::Dialogue;Dialogue.Duration=.1;Dialogue.DialogueAdvance=EDirectorDialogueAdvance::Click;Dialogue.DialogueText=FText::FromString(TEXT("진동 중 대기"));
 TestTrue(TEXT("Dialogue fixture compile"),FSceneDirectorCompiler::Compile(*Runner->Director,Error));Runner->PlayDirector();Runner->Tick(.2);
 TestTrue(TEXT("Waiting for dialogue"),Runner->IsWaitingForDialogue());const auto Before=Runner->GetCameraShake(Camera);Runner->Tick(.173f);
 TestFalse(TEXT("Shake continues while input is awaited"),Runner->GetCameraShake(Camera).Location.Equals(Before.Location));
 Runner->StopDirector();
 W->DestroyWorld(false);GEngine->DestroyWorldContext(W);return true;
}
#include "SceneDirectorToolkit.h"
#include "SceneDirectorViewport.h"
#include "Editor.h"
#include "LevelSequence.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorShakePreviewTest,"Constellation.SceneDirector.CameraShake.Preview",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorShakePreviewTest::RunTest(const FString&)
{
 auto* A=ShakeFixture();FString Error;if(!TestTrue(TEXT("Preview compile"),FSceneDirectorCompiler::Compile(*A,Error)))return false;
 TSharedPtr<FSceneDirectorToolkit> Editor=MakeShared<FSceneDirectorToolkit>();Editor->Init(A,nullptr);
 Editor->OpenPreview(A->GeneratedSequence,A,1.5);auto Client=Editor->SceneViewport->GetViewportClient();Client->Tick(0);
 const FVector Base=Client->GetViewLocation();const FRotator Rotation=Client->GetViewRotation();
 Editor->Sequencer->SetGlobalTime(FFrameTime(9));Client->Tick(0);const FVector Shaken=Client->GetViewLocation();
 TestFalse(TEXT("Preview moves"),Shaken.Equals(Base));Client->Tick(0);TestTrue(TEXT("Repeated tick does not accumulate offset"),Client->GetViewLocation().Equals(Shaken,.001));
 Editor->Sequencer->SetGlobalTime(FFrameTime(45));Client->Tick(0);TestTrue(TEXT("Stop restores base"),Client->GetViewLocation().Equals(Base,.001));TestTrue(TEXT("Stop restores rotation"),Client->GetViewRotation().Equals(Rotation,.001));
 Editor->Sequencer->SetGlobalTime(FFrameTime(9));Client->Tick(0);TestTrue(TEXT("Rewind reproduces view"),Client->GetViewLocation().Equals(Shaken,.001));
 Editor->ClosePreview();Editor->CloseWindow(EAssetEditorCloseReason::AssetEditorHostClosed);return true;
}
#endif
