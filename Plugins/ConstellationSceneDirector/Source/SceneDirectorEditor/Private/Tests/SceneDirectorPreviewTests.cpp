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
