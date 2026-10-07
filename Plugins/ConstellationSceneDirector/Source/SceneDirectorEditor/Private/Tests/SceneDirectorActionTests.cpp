#include "SceneDirectorActionTestTypes.h"
#include "SceneDirectorPlayer.h"
TArray<FName> USceneDirectorTestAction::Calls;
bool USceneDirectorTestAction::bReentryDenied=false;
bool USceneDirectorTestAction::Execute_Implementation(ASceneDirectorPlayer* Player,AActor*,const FDirectorActionParameters& P,FString& Error)
{
    if(++ExecutionCount!=1){Error=TEXT("Action instance reused");return false;}
    Calls.Add(P.Identifier);
    if(P.Identifier==TEXT("Fail")){Error=TEXT("Expected action failure");return false;}
    if(P.Identifier==TEXT("Stop")){Player->StopDirector();bReentryDenied=!Player->PlayDirector();}
    return GetWorld()!=nullptr;
}
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorGraph.h"
#include "SceneDirectorLibrary.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Camera/CameraActor.h"
#include "GameFramework/PlayerController.h"
#include "UObject/UnrealType.h"
namespace
{
USceneDirectorAsset* ActionFixture()
{
    auto* A=NewObject<USceneDirectorAsset>();A->Steps.SetNum(11);auto& S=A->Steps;
    S[0].Type=EDirectorNodeType::Start;S[1].Type=EDirectorNodeType::SpawnNPC;S[1].Role=TEXT("Hero");S[1].ActorClass=ACameraActor::StaticClass();
    S[2].Type=EDirectorNodeType::CinematicMode;S[3].Type=EDirectorNodeType::GameAction;S[3].ActionKey=TEXT("Test");S[3].ActionParameters.Identifier=TEXT("Before");
    S[4].Type=EDirectorNodeType::Dialogue;S[4].Role=TEXT("Hero");S[4].DialogueText=FText::FromString(TEXT("Choose"));S[4].Duration=.1f;
    FDirectorChoice Yes;Yes.Key=TEXT("Yes");Yes.Text=FText::FromString(TEXT("Yes"));FDirectorChoice No;No.Key=TEXT("No");No.Text=FText::FromString(TEXT("No"));S[4].Choices={Yes,No};
    S[4].ChoiceTargets.Add(Yes.Key,S[5].Id);S[4].ChoiceTargets.Add(No.Key,S[6].Id);
    for(int32 I:{5,6,8}){S[I].Type=EDirectorNodeType::GameAction;S[I].ActionKey=TEXT("Test");S[I].ActionTarget=TEXT("Hero");}
    S[5].ActionParameters.Identifier=TEXT("Yes");S[6].ActionParameters.Identifier=TEXT("No");S[8].ActionParameters.Identifier=TEXT("After");
    S[7].Type=EDirectorNodeType::Hub;S[9].Type=EDirectorNodeType::Wait;S[9].Duration=.1f;S[10].Type=EDirectorNodeType::End;
    for(int32 I=0;I<4;++I)S[I].NextNodes={S[I+1].Id};S[5].NextNodes=S[6].NextNodes={S[7].Id};S[7].NextNodes={S[8].Id};S[8].NextNodes={S[9].Id};S[9].NextNodes={S[10].Id};
    FDirectorActionEntry E;E.Key=TEXT("Test");E.ActionClass=USceneDirectorTestAction::StaticClass();A->Actions.Add(E);return A;
}
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorActionValidationTest,"Constellation.SceneDirector.ActionValidation",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorActionValidationTest::RunTest(const FString&)
{
    auto* A=ActionFixture();FString Error;USceneDirectorTestAction::Calls.Reset();
    TestTrue(TEXT("Registered actions compile"),FSceneDirectorCompiler::Compile(*A,Error));TestEqual(TEXT("Compilation never executes game actions"),USceneDirectorTestAction::Calls.Num(),0);
    auto* Previous=A->GeneratedSequence.Get();A->Steps[6].ActionKey=TEXT("Missing");TestFalse(TEXT("Unselected invalid action rejected"),FSceneDirectorCompiler::Compile(*A,Error));TestEqual(TEXT("Failed compilation keeps previous sequence"),A->GeneratedSequence.Get(),Previous);
    A->Steps[6].ActionKey=TEXT("Test");A->Steps[5].ActionTarget=TEXT("MissingNPC");TestFalse(TEXT("Missing target rejected"),FSceneDirectorCompiler::Compile(*A,Error));A->Steps[5].ActionTarget=TEXT("Hero");
    A->Actions[0].ActionClass=USceneDirectorAction::StaticClass();TestFalse(TEXT("Abstract action rejected"),FSceneDirectorCompiler::Compile(*A,Error));A->Actions[0].ActionClass=USceneDirectorTestAction::StaticClass();
    const FDirectorActionEntry Duplicate=A->Actions[0];A->Actions.Add(Duplicate);TestFalse(TEXT("Duplicate registration rejected"),FSceneDirectorCompiler::Compile(*A,Error));A->Actions.Pop();
    A->PreEditChange(nullptr);A->Actions[0].Key=TEXT("Renamed");FPropertyChangedEvent Changed(FindFProperty<FProperty>(USceneDirectorAsset::StaticClass(),TEXT("Actions")));A->PostEditChangeProperty(Changed);
    TestEqual(TEXT("Action key rename propagates"),A->Steps[3].ActionKey,FName(TEXT("Renamed")));
    auto* G=NewObject<USceneDirectorGraph>();G->Asset=A;G->Load();G->Sync();auto* N=CastChecked<USceneDirectorGraphNode>(G->Nodes[3]);TestTrue(TEXT("Key picker contains registry"),N->GetActionKeys().Contains(TEXT("Renamed")));
    TestTrue(TEXT("Roundtrip compiles"),FSceneDirectorCompiler::Compile(*A,Error));return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorActionRuntimeTest,"Constellation.SceneDirector.ActionRuntime",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorActionRuntimeTest::RunTest(const FString&)
{
    auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());
    auto* PC=W->SpawnActor<APlayerController>();auto* R=W->SpawnActor<ASceneDirectorPlayer>();R->bAutoPlay=false;FString Error;
    for(FName Choice:{FName(TEXT("Yes")),FName(TEXT("No"))})
    {
        USceneDirectorTestAction::Calls.Reset();R->Director=ActionFixture();TestTrue(TEXT("Compile"),FSceneDirectorCompiler::Compile(*R->Director,Error));TestTrue(TEXT("Play"),R->PlayDirector());
        TestEqual(TEXT("Initial action once"),USceneDirectorTestAction::Calls.Num(),1);R->Tick(50);R->Tick(50);TestTrue(TEXT("Choice waits"),R->IsWaitingForChoice());TestEqual(TEXT("Choice gate blocks later action"),USceneDirectorTestAction::Calls.Num(),1);
        R->SelectDialogueChoice(Choice);R->Tick(.01f);TestEqual(TEXT("Exactly three selected actions"),USceneDirectorTestAction::Calls.Num(),3);
        TestTrue(TEXT("Only selected branch called"),USceneDirectorTestAction::Calls.Contains(Choice));TestFalse(TEXT("Skipped branch not called"),USceneDirectorTestAction::Calls.Contains(Choice==TEXT("Yes")?FName(TEXT("No")):FName(TEXT("Yes"))));
        R->Tick(50);TestFalse(TEXT("Done"),R->IsDirectorPlaying());TestEqual(TEXT("Action result history retained"),R->ActionResults.Num(),3);TestFalse(TEXT("Input restored"),PC->IsMoveInputIgnored());
    }
    USceneDirectorTestAction::Calls.Reset();R->Director=ActionFixture();R->Director->Steps[5].ActionParameters.Identifier=TEXT("Fail");FSceneDirectorCompiler::Compile(*R->Director,Error);R->PlayDirector();R->Tick(50);R->SelectDialogueChoice(TEXT("Yes"));R->Tick(.01f);
    TestFalse(TEXT("Failure stops"),R->IsDirectorPlaying());TestEqual(TEXT("Failure prevents downstream action"),USceneDirectorTestAction::Calls.Num(),2);TestTrue(TEXT("Error preserved"),R->LastError.Contains(TEXT("Expected action failure")));TestFalse(TEXT("Failure unlocks input"),PC->IsMoveInputIgnored());
    USceneDirectorTestAction::Calls.Reset();R->Director=ActionFixture();R->Director->Steps[3].ActionParameters.Identifier=TEXT("Stop");FSceneDirectorCompiler::Compile(*R->Director,Error);
    TestFalse(TEXT("Action can stop playback during initialization"),R->PlayDirector());TestTrue(TEXT("Reentrant playback denied"),USceneDirectorTestAction::bReentryDenied);TestEqual(TEXT("No followup after stop"),USceneDirectorTestAction::Calls.Num(),1);
    // Two decisions must retain the GUID set for already-executed actions.
    USceneDirectorTestAction::Calls.Reset();R->Director=ActionFixture();auto* Nested=R->Director.Get();Nested->Steps.SetNum(14);auto& NS=Nested->Steps;
    NS[11]=NS[4];NS[11].Id=FGuid::NewGuid();NS[11].ChoiceTargets.Reset();NS[11].ChoiceTargets.Add(TEXT("Yes"),NS[12].Id);NS[11].ChoiceTargets.Add(TEXT("No"),NS[13].Id);
    for(int32 I:{12,13}){NS[I].Type=EDirectorNodeType::GameAction;NS[I].ActionKey=TEXT("Test");NS[I].ActionParameters.Identifier=I==12?TEXT("NestedYes"):TEXT("NestedNo");NS[I].NextNodes={NS[8].Id};}
    NS[7].NextNodes={NS[11].Id};TestTrue(TEXT("Nested actions compile"),FSceneDirectorCompiler::Compile(*Nested,Error));R->PlayDirector();R->Tick(50);R->SelectDialogueChoice(TEXT("Yes"));R->Tick(50);
    TestTrue(TEXT("Second decision waits"),R->IsWaitingForChoice());TestEqual(TEXT("First two actions called once"),USceneDirectorTestAction::Calls.Num(),2);
    R->SelectDialogueChoice(TEXT("No"));R->Tick(50);TestEqual(TEXT("Two rebuilds execute four distinct actions"),USceneDirectorTestAction::Calls.Num(),4);TestTrue(TEXT("Nested selected action executed"),USceneDirectorTestAction::Calls.Contains(TEXT("NestedNo")));TestFalse(TEXT("Nested unselected action skipped"),USceneDirectorTestAction::Calls.Contains(TEXT("NestedYes")));
    TestEqual(TEXT("Every fresh instance succeeded"),R->ActionResults.FilterByPredicate([](const FDirectorActionResult& X){return X.bSucceeded;}).Num(),4);
    // No camera/dialogue/wait is required for a graph consisting only of game actions.
    USceneDirectorTestAction::Calls.Reset();R->Director=NewObject<USceneDirectorAsset>();auto* Linear=R->Director.Get();Linear->Steps.SetNum(3);
    Linear->Steps[0].Type=EDirectorNodeType::Start;Linear->Steps[1].Type=EDirectorNodeType::GameAction;Linear->Steps[1].ActionKey=TEXT("Test");Linear->Steps[1].ActionParameters.Identifier=TEXT("Only");Linear->Steps[2].Type=EDirectorNodeType::End;
    Linear->Steps[0].NextNodes={Linear->Steps[1].Id};Linear->Steps[1].NextNodes={Linear->Steps[2].Id};FDirectorActionEntry Entry;Entry.Key=TEXT("Test");Entry.ActionClass=USceneDirectorTestAction::StaticClass();Linear->Actions.Add(Entry);
    TestTrue(TEXT("Action-only graph compiles"),FSceneDirectorCompiler::Compile(*Linear,Error));TestTrue(TEXT("Action-only graph starts"),R->PlayDirector());R->Tick(50);TestEqual(TEXT("Action-only executes once"),USceneDirectorTestAction::Calls.Num(),1);
    TestTrue(TEXT("New playback starts a new execution session"),R->PlayDirector());R->Tick(50);TestEqual(TEXT("New session may run again"),USceneDirectorTestAction::Calls.Num(),2);TestEqual(TEXT("New session clears old history"),R->ActionResults.Num(),1);
    GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorActionBlueprintTest,"Constellation.SceneDirector.ActionBlueprint",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorActionBlueprintTest::RunTest(const FString&)
{
    auto* A=USceneDirectorLibrary::CreateActionsExample();if(!TestNotNull(TEXT("Real BP example created"),A))return false;
    TestEqual(TEXT("Two registered BP adapters"),A->Actions.Num(),2);
    auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());auto* R=W->SpawnActor<ASceneDirectorPlayer>();R->bAutoPlay=false;R->Director=A;
    for(FName Choice:{FName(TEXT("Help")),FName(TEXT("Decline"))})
    {
        TestTrue(TEXT("Example starts"),R->PlayDirector());R->Tick(50);TestTrue(TEXT("Waiting"),R->IsWaitingForChoice());auto* NPC=R->FindNPC(TEXT("Hero"));TestNotNull(TEXT("Target exists"),NPC);
        TestTrue(TEXT("Choice accepted"),R->SelectDialogueChoice(Choice));R->Tick(.01f);TestEqual(TEXT("One BP action result"),R->ActionResults.Num(),1);
        if(NPC)TestTrue(TEXT("Actual BP function changes target tag"),NPC->ActorHasTag(Choice==TEXT("Help")?TEXT("HelpAccepted"):TEXT("HelpDeclined")));
        if(R->ActionResults.Num())TestTrue(TEXT("BP returned success"),R->ActionResults[0].bSucceeded);R->StopDirector();
    }
    GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
#endif
