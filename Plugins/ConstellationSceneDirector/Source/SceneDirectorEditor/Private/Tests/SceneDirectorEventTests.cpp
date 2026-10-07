#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../SceneDirectorToolkit.h"
#include "../SceneDirectorNodeMenu.h"
#include "SceneDirectorGraph.h"
#include "GraphEditor.h"
#include "EdGraph/EdGraphPin.h"
#include "Editor.h"
#include "SceneDirectorCompiler.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "UObject/SavePackage.h"
#include "Misc/Paths.h"
#include "PackageTools.h"
#include "SceneDirectorPlayer.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LevelSequenceActor.h"
#include "LevelSequencePlayer.h"
static USceneDirectorAsset* MakeEventTestAsset()
{
    auto* Asset=NewObject<USceneDirectorAsset>();
    for(auto Type:{EDirectorNodeType::Start,EDirectorNodeType::Wait,EDirectorNodeType::End}){FDirectorStep S;S.Type=Type;Asset->Steps.Add(S);}
    Asset->Steps[0].NextNodes={Asset->Steps[1].Id};Asset->Steps[1].NextNodes={Asset->Steps[2].Id};return Asset;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorContextMenuTest,"Constellation.SceneDirector.ContextNodeCreation",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorContextMenuTest::RunTest(const FString&)
{
    const auto Entries=DirectorNodeMenuEntries();TestEqual(TEXT("All creatable node types"),Entries.Num(),25);
    TSet<FString> Groups;for(const auto& E:Entries){Groups.Add(E.Category);TestTrue(TEXT("Start/end excluded"),E.Type!=EDirectorNodeType::Start&&E.Type!=EDirectorNodeType::End);}TestEqual(TEXT("Five categories"),Groups.Num(),5);
    auto* Asset=MakeEventTestAsset();auto Editor=MakeShared<FSceneDirectorToolkit>();Editor->Init(Asset,nullptr);
    auto* Start=CastChecked<USceneDirectorGraphNode>(Editor->Graph->Nodes[0]);auto* Out=Start->FindPin(TEXT("Out"));
    auto Menu=Editor->CreateNodeMenu(FVector2f(630,240),{});TestTrue(TEXT("Menu widget built"),Menu.Content->GetType()!=FName(TEXT("SNullWidget")));
    Editor->AddNode(EDirectorNodeType::Wait,FVector2f(630,240),Out);
    TestEqual(TEXT("Created at clicked graph location"),Asset->Steps.Last().EditorPosition,FVector2D(630,240));
    TestEqual(TEXT("Pin drag connects without losing prior branch"),Out->LinkedTo.Num(),2);
    GEditor->UndoTransaction();TestEqual(TEXT("Creation undo"),Asset->Steps.Num(),3);
    GEditor->RedoTransaction();TestEqual(TEXT("Creation redo"),Asset->Steps.Num(),4);
    Editor->CloseWindow(EAssetEditorCloseReason::AssetEditorHostClosed);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorEventGraphsTest,"Constellation.SceneDirector.EventGraphSwitching",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorEventGraphsTest::RunTest(const FString&)
{
    auto* Root=MakeEventTestAsset();auto Editor=MakeShared<FSceneDirectorToolkit>();Editor->Init(Root,nullptr);
    auto* Wait=CastChecked<USceneDirectorGraphNode>(Editor->Graph->Nodes[1]);Wait->Step.Duration=5;Editor->Graph->Sync();
    Editor->AddEvent();if(!TestEqual(TEXT("Second event owned by root"),Root->EventGraphs.Num(),1))return false;
    auto* Second=Editor->Asset.Get();TestTrue(TEXT("Selected new event"),Second!=Root);TestEqual(TEXT("Default graph"),Second->Steps.Num(),3);
    FDirectorVectorEntry V;V.Key=TEXT("Point");V.Value=FVector(10,20,30);Second->Vectors.Add(V);
    Wait=CastChecked<USceneDirectorGraphNode>(Editor->Graph->Nodes[1]);Wait->Step.Duration=3;Editor->Graph->Sync();
    Editor->SelectEvent(Root);TestEqual(TEXT("Original graph duration retained"),Root->Steps[1].Duration,5.f);TestEqual(TEXT("Registry isolated"),Editor->Asset->Vectors.Num(),0);
    Editor->SelectEvent(Second);TestEqual(TEXT("Second graph duration retained"),Editor->Asset->Steps[1].Duration,3.f);TestEqual(TEXT("Second registry retained"),Editor->Asset->Vectors.Num(),1);
    TestFalse(TEXT("Duplicate event name refused"),Editor->RenameEvent(Root->EventKey));TestTrue(TEXT("Rename event"),Editor->RenameEvent(TEXT("Arrival")));TestEqual(TEXT("Runtime lookup"),Root->FindEvent(TEXT("Arrival")),Second);
    GEditor->UndoTransaction();TestEqual(TEXT("Undo event rename"),Second->EventKey,FName(TEXT("Event_2")));GEditor->RedoTransaction();TestEqual(TEXT("Redo event rename"),Second->EventKey,FName(TEXT("Arrival")));
    Editor->AddEvent();TestEqual(TEXT("Third event"),Root->EventGraphs.Num(),2);GEditor->UndoTransaction();TestEqual(TEXT("Undo event add"),Root->EventGraphs.Num(),1);TestEqual(TEXT("Undo leaves a valid selected graph"),Editor->Asset.Get(),Root);
    Editor->SelectEvent(Second);FString Error;TestTrue(TEXT("Compile first event"),FSceneDirectorCompiler::Compile(*Root,Error));TestTrue(TEXT("Compile second event"),FSceneDirectorCompiler::Compile(*Second,Error));TestTrue(TEXT("Independent sequences"),Root->GeneratedSequence!=Second->GeneratedSequence);
    auto* Copy=DuplicateObject<USceneDirectorAsset>(Root,GetTransientPackage());TestTrue(TEXT("Duplicate includes independent child"),Copy->EventGraphs[0]!=Second&&Copy->EventGraphs[0]->GetOuter()==Copy);TestEqual(TEXT("Duplicate preserves registry"),Copy->EventGraphs[0]->Vectors[0].Value,V.Value);
    Editor->CloseWindow(EAssetEditorCloseReason::AssetEditorHostClosed);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorEventPersistenceTest,"Constellation.SceneDirector.EventGraphPersistence",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorEventPersistenceTest::RunTest(const FString&)
{
    const FString Name=TEXT("/Temp/DirectorEventPersistence_")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    UPackage* Package=CreatePackage(*Name);
    auto* Root=DuplicateObject<USceneDirectorAsset>(MakeEventTestAsset(),Package,TEXT("DirectorEvents"));Root->SetFlags(RF_Public|RF_Standalone);
    auto* Child=DuplicateObject<USceneDirectorAsset>(MakeEventTestAsset(),Root,TEXT("Arrival"));Child->EventKey=TEXT("Arrival");Child->Steps[1].Duration=3;
    FDirectorVectorEntry V;V.Key=TEXT("Point");V.Value=FVector(1,2,3);Child->Vectors.Add(V);Root->EventGraphs.Add(Child);
    FString Error;FSceneDirectorCompiler::Compile(*Root,Error);FSceneDirectorCompiler::Compile(*Child,Error);
    const FString File=FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()/TEXT("SceneDirector-event-persistence.uasset"));
    FSavePackageArgs Args;Args.TopLevelFlags=RF_Public|RF_Standalone;Args.SaveFlags=SAVE_NoError;
    if(!TestTrue(TEXT("Save embedded events"),UPackage::SavePackage(Package,Root,*File,Args)))return false;
    UPackage* LevelPackage=CreatePackage(*(Name+TEXT("_Level")));
    UWorld* Level=UWorld::CreateWorld(EWorldType::Editor,false,TEXT("EventLevel"),LevelPackage,false);Level->SetFlags(RF_Public|RF_Standalone);
    auto* Runner=Level->SpawnActor<ASceneDirectorPlayer>();Runner->Director=Root;Runner->EventKey=TEXT("Arrival");Runner->bAutoPlay=false;
    const FString LevelFile=FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()/TEXT("SceneDirector-event-level.umap"));
    TestTrue(TEXT("External level references only public root and event key"),UPackage::SavePackage(LevelPackage,Level,*LevelFile,Args));
    Runner->Director=nullptr;Level->DestroyWorld(false);
    Package->SetDirtyFlag(false);Root=nullptr;Child=nullptr;
    TArray<UPackage*> ToUnload{Package};if(!TestTrue(TEXT("Unload saved package"),UPackageTools::UnloadPackages(ToUnload)))return false;
    auto* Reloaded=LoadPackage(nullptr,*File,LOAD_None);if(!TestNotNull(TEXT("Reload package from disk"),Reloaded))return false;
    auto* Restored=FindObject<USceneDirectorAsset>(Reloaded,TEXT("DirectorEvents"));if(!TestNotNull(TEXT("Root restored"),Restored))return false;
    auto* Event=Restored->FindEvent(TEXT("Arrival"));if(!TestNotNull(TEXT("Child event restored"),Event))return false;
    TestEqual(TEXT("Independent graph saved"),Event->Steps[1].Duration,3.f);TestEqual(TEXT("Registry saved"),Event->Vectors[0].Value,V.Value);TestNotNull(TEXT("Child sequence saved"),Event->GeneratedSequence.Get());
    UWorld* PlayWorld=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(PlayWorld);PlayWorld->InitializeActorsForPlay(FURL());
    auto* PlayerActor=PlayWorld->SpawnActor<ASceneDirectorPlayer>();PlayerActor->Director=Restored;PlayerActor->EventKey=TEXT("Arrival");PlayerActor->bAutoPlay=false;
    TestTrue(TEXT("Play selected child through root reference"),PlayerActor->PlayDirector());
    for(TActorIterator<ALevelSequenceActor> It(PlayWorld);It;++It)TestEqual(TEXT("Selected event duration"),It->GetSequencePlayer()->GetDuration().AsSeconds(),3.0);
    PlayerActor->StopDirector();PlayerActor->EventKey=TEXT("Missing");TestFalse(TEXT("Missing event is rejected"),PlayerActor->PlayDirector());
    GEngine->DestroyWorldContext(PlayWorld);PlayWorld->DestroyWorld(false);return true;
}
#endif
