#include "SceneDirectorLibrary.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorTestFixture.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "GameFramework/Actor.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "SceneDirectorGraph.h"
#include "SGraphNodeDefault.h"
#include "../SceneDirectorToolkit.h"
#include "../SceneDirectorViewport.h"
#include "GraphEditor.h"
#include "Tests/AutomationCommon.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SWindow.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "ScopedTransaction.h"
#include "Editor.h"
#include "SceneDirectorPlayer.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "LevelSequencePlayer.h"
#include "GameFramework/PlayerController.h"
#include "Camera/CameraActor.h"
#include "Camera/PlayerCameraManager.h"
#include "MovieSceneSpawnable.h"
#include "EngineUtils.h"
#include "LevelSequenceActor.h"
#include "EdGraph/EdGraphPin.h"

static USceneDirectorAsset* MakeDirectorTestAsset()
{
    auto* Asset = NewObject<USceneDirectorAsset>();
    for (auto Type : { EDirectorNodeType::Start, EDirectorNodeType::SpawnNPC, EDirectorNodeType::Camera, EDirectorNodeType::Wait, EDirectorNodeType::End })
    {
        FDirectorStep Step; Step.Type = Type; Step.ActorClass = AActor::StaticClass(); Step.EditorPosition=FVector2D(Asset->Steps.Num()*280,0);
        Asset->Steps.Add(Step);
    }
    for (int32 I=0; I<Asset->Steps.Num()-1; ++I) Asset->Steps[I].Next=Asset->Steps[I+1].Id;
    return Asset;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorValidTest,"Constellation.SceneDirector.ValidGraph",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorValidTest::RunTest(const FString&)
{
    auto* Asset=MakeDirectorTestAsset(); TArray<int32> Order; FString Error;
    TestTrue(TEXT("A connected NPC/camera graph validates"),FSceneDirectorCompiler::Validate(*Asset,Order,Error));
    TestEqual(TEXT("All five nodes ordered"),Order.Num(),5);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorInvalidTest,"Constellation.SceneDirector.InvalidGraphs",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorInvalidTest::RunTest(const FString&)
{
    TArray<int32> Order; FString Error;
    auto* Asset=MakeDirectorTestAsset(); Asset->Steps[3].Next=Asset->Steps[1].Id;
    TestFalse(TEXT("Cycles rejected"),FSceneDirectorCompiler::Validate(*Asset,Order,Error));
    TestFalse(TEXT("Error is actionable"),Error.IsEmpty());
    Asset=MakeDirectorTestAsset(); Asset->Steps[1].ActorClass=nullptr;
    TestFalse(TEXT("Missing BP rejected"),FSceneDirectorCompiler::Validate(*Asset,Order,Error));
    Asset=MakeDirectorTestAsset(); Asset->Steps[2].Role=TEXT("Missing");
    TestFalse(TEXT("Missing camera target rejected"),FSceneDirectorCompiler::Validate(*Asset,Order,Error));
    Asset=MakeDirectorTestAsset(); Asset->Steps[3].Duration=-1;
    TestFalse(TEXT("Negative duration rejected"),FSceneDirectorCompiler::Validate(*Asset,Order,Error));
    Asset=MakeDirectorTestAsset(); Asset->Steps[1].Id=Asset->Steps[0].Id;
    TestFalse(TEXT("Duplicate IDs rejected"),FSceneDirectorCompiler::Validate(*Asset,Order,Error));
    Asset=MakeDirectorTestAsset(); Asset->Steps.Add(FDirectorStep());
    TestFalse(TEXT("Disconnected nodes rejected"),FSceneDirectorCompiler::Validate(*Asset,Order,Error));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorCompileTest,"Constellation.SceneDirector.CompileAndRegenerate",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorCompileTest::RunTest(const FString&)
{
    auto* Asset=MakeDirectorTestAsset(); FString Error;
    if (!TestTrue(TEXT("Compile succeeds"),FSceneDirectorCompiler::Compile(*Asset,Error))) return false;
    ULevelSequence* First=Asset->GeneratedSequence;
    if (!TestNotNull(TEXT("Real Level Sequence generated"),First)) return false;
    TestEqual(TEXT("NPC and camera spawnables"),First->GetMovieScene()->GetSpawnableCount(),2);
    TestTrue(TEXT("Second compile succeeds"),FSceneDirectorCompiler::Compile(*Asset,Error));
    TestEqual(TEXT("No duplicate spawnables"),Asset->GeneratedSequence->GetMovieScene()->GetSpawnableCount(),2);
    auto* LastGood=Asset->GeneratedSequence.Get(); Asset->Steps[1].ActorClass=nullptr;
    TestFalse(TEXT("Invalid regeneration fails"),FSceneDirectorCompiler::Compile(*Asset,Error));
    TestTrue(TEXT("Last good sequence preserved"),Asset->GeneratedSequence==LastGood);
    return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorGraphRoundtripTest,"Constellation.SceneDirector.GraphRoundtrip",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorGraphRoundtripTest::RunTest(const FString&)
{
    auto* Asset=MakeDirectorTestAsset();auto* Graph=NewObject<USceneDirectorGraph>();Graph->Schema=USceneDirectorSchema::StaticClass();Graph->Asset=Asset;Graph->Load();
    TestEqual(TEXT("Every step has a visual node"),Graph->Nodes.Num(),5);
    const FGuid NPCId=Asset->Steps[1].Id;
    auto* NPC=CastChecked<USceneDirectorGraphNode>(Graph->Nodes[1]);NPC->Step.Role=TEXT("EditedNPC");Graph->Sync();
    TestEqual(TEXT("Property edits persisted"),Asset->Steps[1].Role,FName(TEXT("EditedNPC")));
    TestEqual(TEXT("Identity retained"),Asset->Steps[1].Id,NPCId);
    NPC->FindPin(TEXT("Out"))->BreakAllPinLinks();Graph->Sync();
    TArray<int32> Order;FString Error;
    TestFalse(TEXT("Broken visual connection prevents compile"),FSceneDirectorCompiler::Validate(*Asset,Order,Error));
    TestTrue(TEXT("Edits require regeneration"),Asset->bNeedsCompile);
    Graph->Load();NPC=CastChecked<USceneDirectorGraphNode>(Graph->Nodes[1]);
    TestEqual(TEXT("Disconnected state reloads"),NPC->FindPin(TEXT("Out"))->LinkedTo.Num(),0);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorRuntimeTest,"Constellation.SceneDirector.RuntimeLifecycle",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorRuntimeTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    auto* Controller=World->SpawnActor<APlayerController>();
    if(!Controller->PlayerCameraManager){Controller->PlayerCameraManager=World->SpawnActor<APlayerCameraManager>();Controller->PlayerCameraManager->InitializeFor(Controller);}
    auto* ViewTarget=World->SpawnActor<ACameraActor>();Controller->SetViewTarget(ViewTarget);
    auto* Player=World->SpawnActor<ASceneDirectorPlayer>();Player->bAutoPlay=false;
    TestFalse(TEXT("Missing asset rejected"),Player->PlayDirector());
    Player->Director=MakeDirectorTestAsset();
    TestFalse(TEXT("Uncompiled asset rejected"),Player->PlayDirector());
    FString Error;
    if(TestTrue(TEXT("Compile for runtime"),FSceneDirectorCompiler::Compile(*Player->Director,Error)))
    {
        for(int32 I=0;I<20;++I)
        {
            TestTrue(TEXT("Sequence starts"),Player->PlayDirector());
            TestFalse(TEXT("Duplicate start refused"),Player->PlayDirector());
            TArray<TWeakObjectPtr<UObject>> Spawned;
            for(TActorIterator<ALevelSequenceActor> It(World);It;++It)
                for(UObject* Object:It->GetSequencePlayer()->GetBoundObjects(UE::MovieScene::FRelativeObjectBindingID(Player->Director->GeneratedSequence->GetMovieScene()->GetSpawnable(0).GetGuid())))Spawned.Add(Object);
            TestEqual(TEXT("Actual NPC spawned"),Spawned.Num(),1);
            Player->StopDirector();
            TestFalse(TEXT("Stop resets running state"),Player->IsDirectorPlaying());
            int32 Live=0;for(TActorIterator<ALevelSequenceActor> It(World);It;++It)++Live;
            TestEqual(TEXT("No retained sequence actors"),Live,0);
            for(const auto& NPC:Spawned)TestFalse(TEXT("NPC removed after stop"),NPC.IsValid());
            TestTrue(TEXT("Original camera restored"),Controller->GetViewTarget()==ViewTarget);
        }
    }
    TestTrue(TEXT("Start for natural completion"),Player->PlayDirector());
    ULevelSequencePlayer* FinishingPlayer=nullptr;for(TActorIterator<ALevelSequenceActor> It(World);It;++It)FinishingPlayer=It->GetSequencePlayer();
    for(int32 Frame=0;Frame<150 && Player->IsDirectorPlaying() && FinishingPlayer;++Frame)FinishingPlayer->Update(1.f/30.f);
    if(FinishingPlayer)AddInfo(FString::Printf(TEXT("Completion diagnostic: time=%f duration=%f playing=%d clock=%d"),FinishingPlayer->GetCurrentTime().AsSeconds(),FinishingPlayer->GetDuration().AsSeconds(),FinishingPlayer->IsPlaying(),static_cast<int32>(Player->Director->GeneratedSequence->GetMovieScene()->GetClockSource())));
    TestFalse(TEXT("Natural completion clears running state"),Player->IsDirectorPlaying());
    TestTrue(TEXT("Natural completion restores camera"),Controller->GetViewTarget()==ViewTarget);
    Player->StopDirector();
    GEngine->DestroyWorldContext(World);World->DestroyWorld(false);return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorMovementTest,"Constellation.SceneDirector.MovementUndo",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorMovementTest::RunTest(const FString&)
{
    auto* Asset=MakeDirectorTestAsset();Asset->SetFlags(RF_Transactional);
    auto* Graph=NewObject<USceneDirectorGraph>(GetTransientPackage(),NAME_None,RF_Transactional);Graph->Schema=USceneDirectorSchema::StaticClass();Graph->Asset=Asset;Graph->Load();
    auto* Node=CastChecked<USceneDirectorGraphNode>(Graph->Nodes[1]);
    TSharedPtr<SGraphNode> Widget=Node->CreateVisualWidget();
    if(!Widget)Widget=SNew(SGraphNodeDefault).GraphNodeObj(Node);
    {
        const FScopedTransaction Tx(FText::FromString(TEXT("Director test movement")));
        SGraphNode::FNodeSet Filter;Widget->MoveTo(FVector2f(480,240),Filter);
    }
    TestEqual(TEXT("Dragging updates persistent layout"),Asset->Steps[1].EditorPosition,FVector2D(480,240));
    GEditor->UndoTransaction();TestEqual(TEXT("Undo restores layout"),Asset->Steps[1].EditorPosition,FVector2D(280,0));
    GEditor->RedoTransaction();TestEqual(TEXT("Redo restores moved layout"),Asset->Steps[1].EditorPosition,FVector2D(480,240));
    return true;
}



static TSharedPtr<FSceneDirectorToolkit> DirectorReviewEditor;
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FDirectorEditorCapture,FAutomationTestBase*,Test);
bool FDirectorEditorCapture::Update()
{
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorGirlCapture")))
    {
        auto S=DirectorReviewEditor->Sequencer;
        for(int Pass=0;Pass<2;++Pass)
        {
            if(Pass){S->SetGlobalTime(FFrameTime(0));S->ForceEvaluate();S->SetGlobalTime(FFrameTime(108));S->ForceEvaluate();DirectorReviewEditor->SceneViewport->GetViewportClient()->Tick(0);}
            auto Bound=S->FindBoundObjects(DirectorReviewEditor->Asset->NPCBindings.FindChecked(TEXT("Heroine")),MovieSceneSequenceID::Root);
            Test->TestEqual(TEXT("One heroine exists after preview seek"),Bound.Num(),1);
            for(auto O:Bound)if(auto* A=Cast<AActor>(O.Get()))
            {
                Test->TestFalse(TEXT("Preview heroine visible"),A->IsHidden());
                Test->TestTrue(TEXT("Heroine follows cave attachment after preview seek"),A->GetActorLocation().Equals(FVector(-25800,-11850,-650),.1));
            }
        }
        auto* Client=static_cast<FDirectorViewportClient*>(DirectorReviewEditor->SceneViewport->GetViewportClient().Get());
        Test->TestEqual(TEXT("Camera return included in scene preview"),Client->ReturnStarts.Num(),1);
        for(const auto& Entry:Client->ReturnStarts)Test->TestTrue(TEXT("Camera return starts at final cave shot"),Entry.Value.View.GetLocation().Equals(FVector(-25810,-12280,70),.1));
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorSequenceCapture")))
    {
        auto S=DirectorReviewEditor->Sequencer;UCameraComponent* Camera=nullptr;
        for(auto* T:S->GetRootMovieSceneSequence()->GetMovieScene()->GetTracks())if(auto* SubTrack=Cast<UMovieSceneSubTrack>(T))
            for(auto* Base:SubTrack->GetAllSections())if(auto* Sub=Cast<UMovieSceneSubSection>(Base))
                if(auto* Cuts=Sub->GetSequence()->GetMovieScene()->GetCameraCutTrack())for(auto* C:Cuts->GetAllSections())
                    if(auto* Cut=Cast<UMovieSceneCameraCutSection>(C))for(auto O:S->FindBoundObjects(Cut->GetCameraBindingID().GetGuid(),Sub->GetSequenceID()))
                        if(auto* A=Cast<ACameraActor>(O.Get()))Camera=A->GetCameraComponent();
        Test->TestNotNull(TEXT("Reused camera cut resolves"),Camera);if(Camera)Test->TestTrue(TEXT("Preview follows reused camera"),DirectorReviewEditor->SceneViewport->GetViewportClient()->GetViewLocation().Equals(Camera->GetComponentLocation(),.1));
    }
    if(!FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorGirlCapture"))&&!FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorStatueCapture"))&&!FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorConversationCapture"))&&!FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorBranchCapture"))&&!FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorActionCapture"))&&!FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorSequenceCapture"))&&!FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorImportCapture")))Test->TestTrue(TEXT("Scene preview follows generated camera"),DirectorReviewEditor->SceneViewport->GetViewportClient()->GetViewLocation().Equals(FVector(-350,100,150),.1));
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorCapture")))
    {
        TArray<FColor> Pixels;FIntVector Size;
        auto Window=FSlateApplication::Get().GetActiveTopLevelWindow();
        if(Test->TestTrue(TEXT("Review window exists"),Window.IsValid()))
        {
            bool Captured=FSlateApplication::Get().TakeScreenshot(Window.ToSharedRef(),Pixels,Size);
            if(Test->TestTrue(TEXT("Editor screenshot captured"),Captured))
            {
                TArray64<uint8> PNG;FImageUtils::PNGCompressImageArray(Size.X,Size.Y,Pixels,PNG);
                Test->TestTrue(TEXT("Screenshot saved"),FFileHelper::SaveArrayToFile(PNG,*(FPaths::ProjectSavedDir()/TEXT("SceneDirector-editor.png"))));
            }
        }
    }
    DirectorReviewEditor->CloseWindow(EAssetEditorCloseReason::AssetEditorHostClosed);DirectorReviewEditor.Reset();
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorEditorSmokeTest,"Constellation.SceneDirector.EditorSmoke",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorEditorSmokeTest::RunTest(const FString&)
{
    auto* Asset=FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorGirlCapture"))?LoadObject<USceneDirectorAsset>(nullptr,TEXT("/Game/SceneDirector/School/DA_Little_Girl_Event_Mushroom_Cave")):FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorStatueCapture"))?LoadObject<USceneDirectorAsset>(nullptr,TEXT("/Game/SceneDirector/Statue/DA_StatueInteraction.DA_StatueInteraction")):FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorImportCapture"))?USceneDirectorLibrary::CreateImportExample():FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorSequenceCapture"))?USceneDirectorLibrary::CreateSequenceExample():FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorActionCapture"))?USceneDirectorLibrary::CreateActionsExample():FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorBranchCapture"))?USceneDirectorLibrary::CreateBranchingExample():(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorConversationCapture"))?USceneDirectorLibrary::CreateConversationExample():MakeAnimationTestAsset()); if(!TestNotNull(TEXT("Animation preview fixture"),Asset))return false;
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorMovementCapture")))
    {
        Asset->Steps[2].Type=EDirectorNodeType::CharacterMove;Asset->Steps[2].bAutoLocomotion=false;Asset->Steps[2].MoveSpeed=75;
        FDirectorVectorEntry V;V.Key=TEXT("NPCGoal");V.Value=FVector(0,150,0);Asset->Vectors.Add(V);
        Asset->Steps[2].Destination.Mode=EDirectorValueMode::Key;Asset->Steps[2].Destination.Key=V.Key;
        Asset->Steps[3].Type=EDirectorNodeType::CameraMove;Asset->Steps[3].CameraKey=TEXT("MainCamera");
        const FVector Rotation=(FVector(0,0,80)-Asset->Steps[3].Transform.GetLocation()).Rotation().Euler();
        Asset->Steps[3].Transform.SetRotation(FRotator::MakeFromEuler(Rotation).Quaternion());
        Asset->Steps[3].Destination.Value=FVector(-350,250,150);Asset->Steps[3].Rotation.Value=Rotation;
        Asset->Steps[1].WalkAnimation=Asset->Steps[2].Animation;Asset->Steps[1].RunAnimation=Asset->Steps[2].Animation;
    }
    // Manual capture uses an unsaved duplicate, so documentation cannot change authored scenes.
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorSpeakerCapture")))
    {
        Asset=DuplicateObject<USceneDirectorAsset>(Asset,GetTransientPackage());
        for(auto& Step:Asset->Steps)if(Step.Type==EDirectorNodeType::Dialogue)
        {Step.SpeakerSource=EDirectorSpeakerSource::Table;Step.SpeakerRow.DataTable=LoadObject<UDataTable>(nullptr,TEXT("/Game/Constellation/Gameplay/Sequences/Data/DT_SpeakerData"));Step.SpeakerRow.RowName=TEXT("Heroine");break;}
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorManualCapture")))
    {
        Asset=NewObject<USceneDirectorAsset>();Asset->EventKey=TEXT("Greeting");
        const EDirectorNodeType Types[]={EDirectorNodeType::Start,EDirectorNodeType::InputLock,EDirectorNodeType::HUDHidden,EDirectorNodeType::Dialogue,EDirectorNodeType::CloseDialogue,EDirectorNodeType::HUDHidden,EDirectorNodeType::InputLock,EDirectorNodeType::End};
        for(int32 I=0;I<8;++I){FDirectorStep S;S.Type=Types[I];S.EditorPosition=FVector2D((I<4?I:7-I)*205,I<4?0:180);S.bLockInput=I==1;S.bHideHUD=I==2;S.Duration=1.f;
            if(I==3){S.SpeakerSource=EDirectorSpeakerSource::Table;S.SpeakerRow.DataTable=LoadObject<UDataTable>(nullptr,TEXT("/Game/Constellation/Gameplay/Sequences/Data/DT_SpeakerData"));S.SpeakerRow.RowName=TEXT("Heroine");S.DialogueText=FText::FromString(TEXT("어서 와. 여기서부터 함께 가자."));S.DialogueAdvance=EDirectorDialogueAdvance::Click;}
            Asset->Steps.Add(S);}
        for(int32 I=0;I<7;++I)Asset->Steps[I].NextNodes={Asset->Steps[I+1].Id};
    }
    DirectorReviewEditor=MakeShared<FSceneDirectorToolkit>();DirectorReviewEditor->Init(Asset,nullptr);
    TestTrue(TEXT("Editor tab created"),DirectorReviewEditor->GetTabManager().IsValid());
    if(auto Window=DirectorReviewEditor->GetTabManager()->GetOwnerTab()->GetParentWindow())Window->Resize(FVector2D(1500,950));
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorMovementCapture")))
    {DirectorReviewEditor->AddEvent();DirectorReviewEditor->RenameEvent(TEXT("Arrival"));DirectorReviewEditor->SelectEvent(Asset);}
    DirectorReviewEditor->BuildPreview();
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorGirlCapture")))DirectorReviewEditor->Sequencer->SetGlobalTime(FFrameTime(108));
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorMovementCapture")))
    {DirectorReviewEditor->GraphEditor->ClearSelectionSet();DirectorReviewEditor->GraphEditor->SetNodeSelection(DirectorReviewEditor->Graph->Nodes[2],true);DirectorReviewEditor->GraphEditor->ZoomToFit(false);}
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorConversationCapture"))){DirectorReviewEditor->Sequencer->SetGlobalTime(FFrameTime(15));DirectorReviewEditor->GraphEditor->ClearSelectionSet();DirectorReviewEditor->GraphEditor->SetNodeSelection(DirectorReviewEditor->Graph->Nodes[6],true);DirectorReviewEditor->GraphEditor->ZoomToFit(false);}
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorBranchCapture"))){DirectorReviewEditor->Sequencer->SetGlobalTime(FFrameTime(45));DirectorReviewEditor->GraphEditor->ClearSelectionSet();DirectorReviewEditor->GraphEditor->SetNodeSelection(DirectorReviewEditor->Graph->Nodes[4],true);DirectorReviewEditor->GraphEditor->ZoomToFit(false);}
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorActionCapture"))){DirectorReviewEditor->Sequencer->SetGlobalTime(FFrameTime(65));DirectorReviewEditor->GraphEditor->ClearSelectionSet();DirectorReviewEditor->GraphEditor->SetNodeSelection(DirectorReviewEditor->Graph->Nodes[12],true);DirectorReviewEditor->GraphEditor->ZoomToFit(false);}
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorSequenceCapture"))){DirectorReviewEditor->Sequencer->SetGlobalTime(FFrameTime(30));DirectorReviewEditor->GraphEditor->ClearSelectionSet();DirectorReviewEditor->GraphEditor->SetNodeSelection(DirectorReviewEditor->Graph->Nodes[3],true);DirectorReviewEditor->GraphEditor->ZoomToFit(false);}
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorImportCapture")))
    {
        DirectorReviewEditor->Sequencer->SetGlobalTime(FFrameTime(38));DirectorReviewEditor->PreviewOriginal();
        TestTrue(TEXT("Original comparison retains elapsed time"),FMath::IsNearlyEqual(DirectorReviewEditor->PreviewElapsed(),38./30.,.0001));
        TestTrue(TEXT("Original comparison uses independent copy"),DirectorReviewEditor->ComparisonSequence&&DirectorReviewEditor->ComparisonSequence!=Asset->ImportedFrom);
        DirectorReviewEditor->BuildPreview();TestTrue(TEXT("Converted preview retains comparison time"),FMath::IsNearlyEqual(DirectorReviewEditor->PreviewElapsed(),38./30.,.0001));
        DirectorReviewEditor->GraphEditor->ClearSelectionSet();for(auto Base:DirectorReviewEditor->Graph->Nodes)if(auto* Node=Cast<USceneDirectorGraphNode>(Base))if(Node->Step.Type==EDirectorNodeType::CharacterMove){DirectorReviewEditor->GraphEditor->SetNodeSelection(Node,true);break;}DirectorReviewEditor->GraphEditor->ZoomToFit(false);
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorStatueCapture"))){DirectorReviewEditor->Sequencer->SetGlobalTime(FFrameTime(120));DirectorReviewEditor->GraphEditor->ClearSelectionSet();DirectorReviewEditor->GraphEditor->ZoomToFit(false);}
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorAuthoringCapture")))
    {
        DirectorReviewEditor->GraphEditor->ClearSelectionSet();
        for(auto Base:DirectorReviewEditor->Graph->Nodes)if(auto* Node=Cast<USceneDirectorGraphNode>(Base);Node&&Node->Step.Type==EDirectorNodeType::Dialogue){DirectorReviewEditor->GraphEditor->SetNodeSelection(Node,true);break;}
    }
    TestNotNull(TEXT("Embedded preview compiled"),Asset->GeneratedSequence.Get());
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.f));
    ADD_LATENT_AUTOMATION_COMMAND(FDirectorEditorCapture(this));
    return true;
}
#include "GraphEditor.h"
#include "InputCoreTypes.h"
#include "Input/Events.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorDeleteKeyTest,"Constellation.SceneDirector.DeleteKeyUndo",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorDeleteKeyTest::RunTest(const FString&)
{
    auto* A=MakeDirectorTestAsset();auto Editor=MakeShared<FSceneDirectorToolkit>();Editor->Init(A,nullptr);
    ADD_LATENT_AUTOMATION_COMMAND(FDelayedFunctionLatentCommand([this,A,Editor]
    {
    TestEqual(TEXT("NPC initially selected"),Editor->GraphEditor->GetSelectedNodes().Num(),1);
    Editor->GraphEditor->CaptureKeyboard();
    FSlateApplication::Get().ProcessKeyDownEvent(FKeyEvent(EKeys::Delete,FModifierKeysState(),0,false,0,0));
    TestEqual(TEXT("Delete key removes selected NPC"),A->Steps.Num(),4);
    GEditor->UndoTransaction();TestEqual(TEXT("Undo restores deleted NPC"),A->Steps.Num(),5);
    TArray<int32> Order;FString Error;TestTrue(TEXT("Undo restores all links"),FSceneDirectorCompiler::Validate(*A,Order,Error));
    Editor->CloseWindow(EAssetEditorCloseReason::AssetEditorHostClosed);
    },.5f));return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorAnimationPlaybackTest,"Constellation.SceneDirector.AnimationPlayback",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorAnimationPlaybackTest::RunTest(const FString&)
{
    auto* A=MakeAnimationTestAsset();if(!TestNotNull(TEXT("Animation fixture"),A))return false;
    FString Error;if(!TestTrue(TEXT("Compile"),FSceneDirectorCompiler::Compile(*A,Error)))return false;
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);World->InitializeActorsForPlay(FURL());
    auto* Runner=World->SpawnActor<ASceneDirectorPlayer>();Runner->bAutoPlay=false;Runner->Director=A;
    TestTrue(TEXT("Play animation sequence"),Runner->PlayDirector());
    ULevelSequencePlayer* Player=nullptr;for(TActorIterator<ALevelSequenceActor> It(World);It;++It)Player=It->GetSequencePlayer();
    if(TestNotNull(TEXT("Sequence player"),Player))
    {
        Player->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(.1f,EUpdatePositionMethod::Jump));
        AActor* NPC=Runner->FindNPC(TEXT("Heroine"));
        if(TestNotNull(TEXT("Lookup live NPC by key"),NPC))
        {
            auto* Mesh=NPC->FindComponentByClass<USkeletalMeshComponent>();
            if(TestNotNull(TEXT("Spawned skeletal component"),Mesh))
            {
                Mesh->TickAnimation(0.f,false);Mesh->RefreshBoneTransforms();
                const auto First=Mesh->GetComponentSpaceTransforms();
                Player->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(.6f,EUpdatePositionMethod::Jump));
                Mesh->TickAnimation(0.f,false);Mesh->RefreshBoneTransforms();
                const auto Second=Mesh->GetComponentSpaceTransforms();bool Moved=false;
                for(int32 I=0;I<FMath::Min(First.Num(),Second.Num());++I)if(!First[I].Equals(Second[I],.001f)){Moved=true;break;}
                TestTrue(TEXT("Animation changes actual bone poses"),Moved);
            }
            Runner->Director=MakeDirectorTestAsset();TestEqual(TEXT("Lookup uses active playback after Director reassignment"),Runner->FindNPC(TEXT("Heroine")),NPC);
        }
    }
    Runner->StopDirector();TestNull(TEXT("Key no longer resolves after stop"),Runner->FindNPC(TEXT("Heroine")));
    GEngine->DestroyWorldContext(World);World->DestroyWorld(false);return true;
}
#endif
