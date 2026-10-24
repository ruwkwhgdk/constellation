#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorTestFixture.h"
#include "SceneDirectorToolkit.h"
#include "SceneDirectorViewport.h"
#include "SceneDirectorCompiler.h"
#include "LevelSequence.h"
#include "Editor.h"
#include "Widgets/Layout/SBox.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorPreviewVisibilityTest,"Constellation.SceneDirector.PreviewVisibility",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorPreviewVisibilityTest::RunTest(const FString&)
{
 auto* A=MakeAnimationTestAsset();if(!TestNotNull(TEXT("Fixture"),A))return false;
 auto& NPC=A->Steps[1];NPC.Type=EDirectorNodeType::BindNPC;NPC.ActorSource=EDirectorActorSource::Tag;NPC.ActorTag=TEXT("PreviewVisibilityTest");
 auto* CDO=NPC.ActorClass->GetDefaultObject<AActor>();CDO->SetActorHiddenInGame(true);CDO->FindComponentByClass<USkeletalMeshComponent>()->SetVisibility(false);
 auto* World=GEditor->GetEditorWorldContext().World();auto* Original=World->SpawnActor<AActor>(NPC.ActorClass);Original->Tags.Add(NPC.ActorTag);Original->SetIsTemporarilyHiddenInEditor(false);
 FString Error;if(!TestTrue(*Error,FSceneDirectorCompiler::Compile(*A,Error))){Original->Destroy();return false;}
 TSharedPtr<FSceneDirectorToolkit> Editor=MakeShared<FSceneDirectorToolkit>();Editor->Init(A,nullptr);
 for(int Pass=0;Pass<2;++Pass)
 {
  Editor->OpenPreview(A->GeneratedSequence,A,0.5);Editor->Sequencer->ForceEvaluate();Editor->SceneViewport->GetViewportClient()->Tick(0);
  auto Bound=Editor->Sequencer->FindBoundObjects(A->NPCBindings.FindChecked(NPC.Role),MovieSceneSequenceID::Root);
  TestEqual(TEXT("Exactly one preview NPC"),Bound.Num(),1);
  if(Bound.Num())if(auto* Clone=Cast<AActor>(Bound[0].Get())){TestFalse(TEXT("Preview NPC is shown"),Clone->IsHidden());TestTrue(TEXT("Preview mesh is shown"),Clone->FindComponentByClass<USkeletalMeshComponent>()->IsVisible());}
  TestTrue(TEXT("Existing level actor excluded from duplicate preview"),Original->IsTemporarilyHiddenInEditor());
  Editor->ClosePreview();TestFalse(TEXT("Level actor visibility restored on close"),Original->IsTemporarilyHiddenInEditor());
 }
 Editor->CloseWindow(EAssetEditorCloseReason::AssetEditorHostClosed);Editor.Reset();Original->Destroy();return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorPreviewReturnTest,"Constellation.SceneDirector.PreviewGameplayReturn",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorPreviewReturnTest::RunTest(const FString&)
{
 auto* A=MakeAnimationTestAsset();if(!TestNotNull(TEXT("Fixture"),A))return false;
 auto& Return=A->Steps[4];Return.Type=EDirectorNodeType::CameraReturn;Return.Duration=2;Return.bUsePreviewReturnView=true;Return.PreviewReturnView=FTransform(FRotator(0,90,0),FVector(450,100,150));Return.PreviewReturnFOV=90;
 FString Error;if(!TestTrue(*Error,FSceneDirectorCompiler::Compile(*A,Error)))return false;
 TSharedPtr<FSceneDirectorToolkit> Editor=MakeShared<FSceneDirectorToolkit>();Editor->Init(A,nullptr);
 Editor->OpenPreview(A->GeneratedSequence,A,3);Editor->Sequencer->ForceEvaluate();Editor->SceneViewport->GetViewportClient()->Tick(0);
 auto Client=Editor->SceneViewport->GetViewportClient();
 TestTrue(TEXT("Return midpoint blends from last shot to gameplay preview camera"),Client->GetViewLocation().Equals(FVector(50,100,150),.1));
 Editor->Sequencer->SetGlobalTime(FFrameTime(119));Editor->SceneViewport->GetViewportClient()->Tick(0);
 TestTrue(TEXT("Return reaches preview goal"),Client->GetViewLocation().Equals(FVector(436.6667,100,150),.1));
 Editor->Sequencer->SetGlobalTime(FFrameTime(90));Editor->SceneViewport->GetViewportClient()->Tick(0);
 TestTrue(TEXT("Seeking backward reproduces the same return path"),Client->GetViewLocation().Equals(FVector(50,100,150),.1));
 Editor->CloseWindow(EAssetEditorCloseReason::AssetEditorHostClosed);Editor.Reset();return true;
}
#endif

#if WITH_DEV_AUTOMATION_TESTS
#include "SceneDirectorGraph.h"
#include "GraphEditor.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorNodePreviewTest,"Constellation.SceneDirector.SelectedNodePreview",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorNodePreviewTest::RunTest(const FString&)
{
 auto* A=MakeAnimationTestAsset();if(!TestNotNull(TEXT("Fixture"),A))return false;
 TSharedPtr<FSceneDirectorToolkit> Editor=MakeShared<FSceneDirectorToolkit>();Editor->Init(A,nullptr);
 Editor->GraphEditor->ClearSelectionSet();Editor->GraphEditor->SetNodeSelection(Editor->Graph->Nodes[3],true);
 auto* SavedSequence=A->GeneratedSequence.Get();
 Editor->bNodePreview=true;
 TestTrue(TEXT("Selected camera can preview its result"),Editor->RefreshNodePreview());
 if(Editor->SceneViewport)
 {
  auto Client=Editor->SceneViewport->GetViewportClient();
  TestTrue(TEXT("Camera coordinates shown exactly"),Client->GetViewLocation().Equals(A->Steps[3].Transform.GetLocation(),.01));
  TestTrue(TEXT("Generated sequence untouched"),A->GeneratedSequence.Get()==SavedSequence);
  auto* Camera=CastChecked<USceneDirectorGraphNode>(Editor->Graph->Nodes[3]);
  Camera->Step.Type=EDirectorNodeType::CameraMove;Camera->Step.bActivateCamera=false;Camera->Step.Destination.Value=FVector(100,200,300);Editor->Graph->Sync();
  TestTrue(TEXT("Property edit queues preview refresh"),Editor->NodeRefreshAt>0);
  Editor->NodeRefreshAt=FPlatformTime::Seconds()-.1;Editor->TickNodePreview(0);
  TestTrue(TEXT("Edited camera automatically updated"),Editor->SceneViewport->GetViewportClient()->GetViewLocation().Equals(FVector(100,200,300),.01));
  Camera->Step.Type=EDirectorNodeType::CameraPreset;
  Editor->SetNodePreviewPhase(false);
  TestTrue(TEXT("Framing before uses registered incoming camera"),Editor->SceneViewport->GetViewportClient()->GetViewLocation().Equals(A->Cameras[0].Transform.GetLocation(),.01));
  Editor->SetNodePreviewPhase(true);
  // Reuse the animation's existing skeleton/animation to exercise a real relative movement.
  auto* Move=CastChecked<USceneDirectorGraphNode>(Editor->Graph->Nodes[2]);
  Move->Step.Type=EDirectorNodeType::CharacterMove;Move->Step.bAutoLocomotion=false;
  Move->Step.MoveTiming=EDirectorMoveTiming::Duration;Move->Step.Destination.Mode=EDirectorValueMode::Current;
  Move->Step.Destination.Offset=FVector(200,50,0);
  Editor->GraphEditor->ClearSelectionSet();Editor->GraphEditor->SetNodeSelection(Move,true);
  TestTrue(TEXT("Movement preview available"),Editor->RefreshNodePreview());
  auto Position=[&]()->FVector{
   if(!Editor->Sequencer||!Editor->NodePreviewAsset)return FVector(-9999);
   for(auto O:Editor->Sequencer->FindBoundObjects(Editor->NodePreviewAsset->NPCBindings.FindChecked(Move->Step.Role),MovieSceneSequenceID::Root))
    if(auto* Actor=Cast<AActor>(O.Get()))return Actor->GetActorLocation();
   return FVector(-9999);
  };
  const FVector Start=A->Steps[1].Transform.GetLocation(),End=Start+FVector(200,50,0);
  TestTrue(TEXT("Relative endpoint shown exactly"),Position().Equals(End,.01));
  Editor->RefreshNodePreview();TestTrue(TEXT("Refreshing never accumulates offset"),Position().Equals(End,.01));
  Editor->SetNodePreviewPhase(false);TestTrue(TEXT("Before restores incoming pose"),Position().Equals(Start,.01));
  Editor->PlayNodePreview();Editor->TickNodePreview(1);
  TestTrue(TEXT("Segment playback reaches midpoint"),Position().Equals(FMath::Lerp(Start,End,.5),.1));
  Editor->TickNodePreview(2);TestFalse(TEXT("Segment stops at end"),Editor->bNodePlaying);
  TestTrue(TEXT("Segment final pose exact"),Position().Equals(End,.01));
  Move->Step.Destination.Mode=EDirectorValueMode::Key;Move->Step.Destination.Key=TEXT("MissingPreviewKey");
  TestFalse(TEXT("Invalid key fails visibly"),Editor->RefreshNodePreview());
  TestFalse(TEXT("Failure does not leave stale preview"),Editor->Sequencer.IsValid());
 }

 Editor->CloseWindow(EAssetEditorCloseReason::AssetEditorHostClosed);Editor.Reset();return true;
}
#endif

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorArrivalRotationContract,"Constellation.SceneDirector.ArrivalRotationContract",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorArrivalRotationContract::RunTest(const FString&)
{
 return TestNotNull(TEXT("Character movement exposes optional arrival rotation"),FDirectorStep::StaticStruct()->FindPropertyByName(TEXT("bSpecifyArrivalRotation")));
}
#endif

#if WITH_DEV_AUTOMATION_TESTS
#include "Tests/AutomationCommon.h"
#include "Framework/Application/SlateApplication.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorDirectEditingTest,"Constellation.SceneDirector.DirectEditing",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorDirectEditingTest::RunTest(const FString&)
{
 auto* A=MakeAnimationTestAsset();if(!A)return false;
 A->Steps[1].Transform=FTransform(FRotator(0,30,0),FVector(10,20,30));
 auto& Move=A->Steps[2];Move.Type=EDirectorNodeType::CharacterMove;Move.MoveTiming=EDirectorMoveTiming::Duration;Move.bPlayMoveAnimation=false;
 FDirectorVectorEntry V;V.Key=TEXT("WalkOffset");V.Value=FVector(100,0,0);A->Vectors.Add(V);
 Move.Destination.Mode=EDirectorValueMode::Key;Move.Destination.Key=V.Key;Move.Destination.bAddCurrent=true;
 FDirectorSchedule Plan;FString Error;
 TestTrue(TEXT("Legacy movement schedules"),FSceneDirectorCompiler::Schedule(*A,Plan,Error));
 TestTrue(TEXT("Legacy movement preserves rotation"),Plan.ToPoses[2].GetRotation().Equals(Plan.FromPoses[2].GetRotation()));
 Move.bSpecifyArrivalRotation=true;Move.Rotation.Mode=EDirectorValueMode::Current;Move.Rotation.Offset=FVector(0,0,90);
 TestTrue(TEXT("Arrival rotation schedules"),FSceneDirectorCompiler::Schedule(*A,Plan,Error));
 TestTrue(TEXT("Arrival uses incoming rotation plus offset"),Plan.ToPoses[2].GetRotation().Equals(FRotator(0,120,0).Quaternion(),.001));
 TSharedPtr<FSceneDirectorToolkit> Editor=MakeShared<FSceneDirectorToolkit>();Editor->Init(A,nullptr);
 const FGuid Id=Move.Id;
 auto GetNode=[&]()->USceneDirectorGraphNode*{for(auto O:Editor->Graph->Nodes)if(auto* N=Cast<USceneDirectorGraphNode>(O.Get());N&&N->Step.Id==Id)return N;return nullptr;};
 Editor->GraphEditor->ClearSelectionSet();Editor->GraphEditor->SetNodeSelection(GetNode(),true);Editor->bNodePreview=true;Editor->bDirectEdit=true;
 if(TestTrue(TEXT("Direct preview opens"),Editor->RefreshNodePreview()))
 {
  auto* Client=static_cast<FDirectorViewportClient*>(Editor->SceneViewport->GetViewportClient().Get());
  TestTrue(TEXT("Gizmo active only in after pose"),Client->bDirectEdit);
  const FTransform Before=Client->NodeStaticPose.GetValue();
  FVector Drag(15,-20,30),Scale=FVector::ZeroVector;FRotator Rot(0,45,0);
  TestTrue(TEXT("Gizmo handles delta"),Client->InputWidgetDelta(nullptr,EAxisList::X,Drag,Rot,Scale));
  Client->TrackingStopped();TestTrue(TEXT("Commit deferred out of viewport callback"),Editor->PendingDirectPose.IsSet());
  Editor->TickNodePreview(0);
  auto* N=GetNode();
  TestEqual(TEXT("Key mode preserved"),N->Step.Destination.Mode,EDirectorValueMode::Key);
  TestEqual(TEXT("Key preserved"),N->Step.Destination.Key,V.Key);
  TestTrue(TEXT("Key plus current offset inverted"),N->Step.Destination.Offset.Equals(Drag));
  TestTrue(TEXT("Shared Vector unchanged"),A->Vectors[0].Value.Equals(V.Value));
  TestTrue(TEXT("Rotation enabled"),N->Step.bSpecifyArrivalRotation);
  TestTrue(TEXT("Rotation offset correct"),N->Step.Rotation.Offset.Equals(FVector(0,0,135),.01));
  TestTrue(TEXT("Committed graph compiles"),FSceneDirectorCompiler::Schedule(*A,Plan,Error));
  TestTrue(TEXT("Compiled endpoint equals dragged pose"),Plan.ToPoses[2].GetLocation().Equals(Before.GetLocation()+Drag,.01));
  GEditor->UndoTransaction();
  N=GetNode();TestTrue(TEXT("One undo restores translation"),N&&N->Step.Destination.Offset.IsNearlyZero());
  TestTrue(TEXT("One undo restores rotation"),N&&N->Step.Rotation.Offset.Equals(FVector(0,0,90),.01));
  GEditor->RedoTransaction();N=GetNode();TestTrue(TEXT("Redo restores drag"),N&&N->Step.Destination.Offset.Equals(Drag));
  Editor->SetNodePreviewPhase(false);
  TestFalse(TEXT("Before pose cannot be dragged"),static_cast<FDirectorViewportClient*>(Editor->SceneViewport->GetViewportClient().Get())->bDirectEdit);
  Editor->SetNodePreviewPhase(true);
  N=GetNode();N->Step.bUseMotionPath=true;N->Step.MotionPoints.Reset();
  for(int I=0;I<3;++I){FDirectorMotionPoint P;P.Time=I;P.Position=FVector(I*100,0,0);N->Step.MotionPoints.Add(P);}
  Editor->DirectPathPoint=1;TestTrue(TEXT("Path point preview"),Editor->RefreshNodePreview());
  Editor->CommitDirectPose(FTransform(FRotator(0,50,0),FVector(110,40,0)));
  N=GetNode();TestTrue(TEXT("Chosen path point updated"),N->Step.MotionPoints[1].Position.Equals(FVector(110,40,0)));
  TestTrue(TEXT("First path point unchanged"),N->Step.MotionPoints[0].Position.IsNearlyZero());
  TestTrue(TEXT("Last path point unchanged"),N->Step.MotionPoints[2].Position.Equals(FVector(200,0,0)));
  TestEqual(TEXT("Path timing unchanged"),N->Step.MotionPoints[1].Time,1.);
  auto* Camera=CastChecked<USceneDirectorGraphNode>(Editor->Graph->Nodes[3]);Camera->Step.Type=EDirectorNodeType::CameraMove;
  Camera->Step.Destination.Mode=EDirectorValueMode::Current;
  Editor->GraphEditor->ClearSelectionSet();Editor->GraphEditor->SetNodeSelection(Camera,true);Editor->bCameraPilot=true;
  TestTrue(TEXT("Camera pilot preview"),Editor->RefreshNodePreview());
  Client=static_cast<FDirectorViewportClient*>(Editor->SceneViewport->GetViewportClient().Get());
  TestTrue(TEXT("Pilot mode enabled"),Client->bPilotCamera);
  const FVector CameraGoal(300,400,500),Incoming=Editor->DirectIncomingPose.GetLocation();
  Client->bPilotNavigating=true;Client->DragStart=Client->NodeStaticPose.GetValue();
  Client->SetViewLocation(CameraGoal);Client->SetViewRotation(FRotator(10,50,0));Client->Tick(0);
  TestTrue(TEXT("Pilot view is not overwritten by sequencer"),Client->GetViewLocation().Equals(CameraGoal,.01));
  Client->InputKey(FInputKeyEventArgs(Client->Viewport,FInputDeviceId::CreateFromInternalId(0),EKeys::RightMouseButton,IE_Released,uint64(0)));
  TestTrue(TEXT("Releasing pilot navigation queues commit"),Editor->PendingDirectPose.IsSet());Editor->TickNodePreview(0);
  TestTrue(TEXT("Pilot updates current-relative camera offset"),Camera->Step.Destination.Offset.Equals(CameraGoal-Incoming,.01));
  TestTrue(TEXT("Pilot updates camera rotation"),FRotator::MakeFromEuler(Camera->Step.Rotation.Value).Equals(FRotator(10,50,0),.01));
  if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorDirectCapture")))
  {
   Editor->bCameraPilot=false;Editor->GraphEditor->ClearSelectionSet();Editor->GraphEditor->SetNodeSelection(GetNode(),true);Editor->RefreshNodePreview();
   ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(1));
   ADD_LATENT_AUTOMATION_COMMAND(FDelayedFunctionLatentCommand([this,Editor]{
    TArray<FColor> Pixels;FIntVector Size;
    if(TestTrue(TEXT("Capture direct-edit viewport"),FSlateApplication::Get().TakeScreenshot(Editor->SceneViewport.ToSharedRef(),Pixels,Size)))
    {TArray64<uint8> PNG;FImageUtils::PNGCompressImageArray(Size.X,Size.Y,Pixels,PNG);TestTrue(TEXT("Save direct-edit capture"),FFileHelper::SaveArrayToFile(PNG,*(FPaths::ProjectSavedDir()/TEXT("DirectManipulation/viewport.png"))));}
    Editor->CloseWindow(EAssetEditorCloseReason::AssetEditorHostClosed);
   }));
   return true;
  }

 }
 Editor->CloseWindow(EAssetEditorCloseReason::AssetEditorHostClosed);Editor.Reset();return true;
}
#endif
