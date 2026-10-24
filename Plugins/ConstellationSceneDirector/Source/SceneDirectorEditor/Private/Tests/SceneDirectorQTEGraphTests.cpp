#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorBranching.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorGraph.h"
#include "EdGraph/EdGraphPin.h"

static USceneDirectorAsset* QTEGraphFixture()
{
    auto* A=NewObject<USceneDirectorAsset>();A->Steps.SetNum(5);auto& S=A->Steps;
    S[0].Type=EDirectorNodeType::Start;S[1].Type=EDirectorNodeType::QTE;
    S[2].Type=S[3].Type=EDirectorNodeType::Wait;S[2].Duration=S[3].Duration=.5f;
    S[4].Type=EDirectorNodeType::End;
    S[0].NextNodes={S[1].Id};S[1].ChoiceTargets.Add(TEXT("Success"),S[2].Id);S[1].ChoiceTargets.Add(TEXT("Failure"),S[3].Id);
    S[2].NextNodes=S[3].NextNodes={S[4].Id};return A;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorQTEBranchTest,"Constellation.SceneDirector.QTE.BranchPrefix",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorQTEBranchTest::RunTest(const FString&)
{
    TestEqual(TEXT("Existing enum indices preserved"),int32(EDirectorNodeType::StopCameraShake),33);
    auto* A=QTEGraphFixture();auto* Prefix=NewObject<USceneDirectorAsset>();FString Error;FGuid Pending;
    TestTrue(TEXT("QTE always selects branch resolver"),DirectorBranching::HasBranches(*A));
    TestTrue(TEXT("All QTE routes validate"),DirectorBranching::ValidateAll(*A,Error));
    TestTrue(TEXT("Unanswered prompt resolves prefix"),DirectorBranching::Resolve(*A,{}, {},*Prefix,Pending,Error));
    TestEqual(TEXT("Pending prompt is QTE"),Pending,A->Steps[1].Id);
    TestEqual(TEXT("Prefix contains no speculative followup"),Prefix->Steps.Num(),3);
    TestTrue(TEXT("QTE has no fake dialogue choices"),Prefix->Steps[1].Choices.IsEmpty());
    for(FName Result:{FName(TEXT("Success")),FName(TEXT("Failure"))})
    {
        TMap<FGuid,FName> Decisions;Decisions.Add(A->Steps[1].Id,Result);
        TestTrue(TEXT("Outcome resolves"),DirectorBranching::Resolve(*A,Decisions,{},*Prefix,Pending,Error));
        TestFalse(TEXT("Resolved outcome clears wait"),Pending.IsValid());
        const auto Expected=A->Steps[Result==TEXT("Success")?2:3].Id;
        TestTrue(TEXT("Only selected successor included"),Prefix->Steps.ContainsByPredicate([Expected](const FDirectorStep& S){return S.Id==Expected;}));
        TestEqual(TEXT("Exactly one branch"),Prefix->Steps.Num(),4);
    }
    A->Steps[1].ChoiceTargets.Remove(TEXT("Failure"));
    TestFalse(TEXT("Missing failure output rejected"),DirectorBranching::ValidateAll(*A,Error));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorQTEGraphPinsTest,"Constellation.SceneDirector.QTE.GraphPins",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorQTEGraphPinsTest::RunTest(const FString&)
{
    auto* A=QTEGraphFixture();const auto Success=A->Steps[2].Id,Failure=A->Steps[3].Id;
    auto* Graph=NewObject<USceneDirectorGraph>();Graph->Asset=A;Graph->Schema=USceneDirectorSchema::StaticClass();Graph->Load();
    auto* Node=CastChecked<USceneDirectorGraphNode>(Graph->Nodes[1]);
    TestNotNull(TEXT("Success pin"),Node->FindPin(TEXT("Success")));TestNotNull(TEXT("Failure pin"),Node->FindPin(TEXT("Failure")));
    TestNull(TEXT("No ordinary unconditional output"),Node->FindPin(TEXT("Out")));
    Graph->Sync();Graph->Load();
    TestEqual(TEXT("Success survives graph reload"),A->Steps[1].ChoiceTargets.FindRef(TEXT("Success")),Success);
    TestEqual(TEXT("Failure survives graph reload"),A->Steps[1].ChoiceTargets.FindRef(TEXT("Failure")),Failure);
    Node=CastChecked<USceneDirectorGraphNode>(Graph->Nodes[1]);
    TestEqual(TEXT("Outcome connection replaces old target"),Graph->GetSchema()->CanCreateConnection(Node->FindPin(TEXT("Success")),Graph->Nodes[3]->FindPin(TEXT("In"))).Response,CONNECT_RESPONSE_BREAK_OTHERS_A);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorQTEContinueTest,"Constellation.SceneDirector.QTE.ContinuedMotion",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorQTEContinueTest::RunTest(const FString&)
{
    auto* A=QTEGraphFixture();FDirectorStep Camera;Camera.Type=EDirectorNodeType::CameraMove;Camera.CameraKey=TEXT("Review");Camera.Duration=10;Camera.bWaitForCompletion=false;Camera.NextNodes={A->Steps[1].Id};
    A->Steps[0].NextNodes={Camera.Id};A->Steps.Add(Camera);
    A->Steps[1].QTE.ScenePolicy=EDirectorQTEScenePolicy::Continue;
    auto* Prefix=NewObject<USceneDirectorAsset>();FGuid Pending;FString Error;FDirectorSchedule Plan;
    TestTrue(TEXT("Continue prefix"),DirectorBranching::Resolve(*A,{}, {},*Prefix,Pending,Error));
    if(!TestTrue(TEXT("Continue schedule"),FSceneDirectorCompiler::Schedule(*Prefix,Plan,Error))){AddError(Error);return false;}
    const int32 Q=Prefix->Steps.IndexOfByPredicate([](const FDirectorStep& S){return S.Type==EDirectorNodeType::QTE;});
    TestEqual(TEXT("Continue prompt begins during preceding nonwaiting camera motion"),Plan.StartFrames[Q],0);
    TestTrue(TEXT("Camera motion survives beyond QTE window"),Plan.EndFrame>=300);
    A->Steps[1].QTE.ScenePolicy=EDirectorQTEScenePolicy::Hold;
    TestTrue(TEXT("Hold prefix"),DirectorBranching::Resolve(*A,{}, {},*Prefix,Pending,Error));
    TestTrue(TEXT("Hold schedule"),FSceneDirectorCompiler::Schedule(*Prefix,Plan,Error));
    const int32 HoldQ=Prefix->Steps.IndexOfByPredicate([](const FDirectorStep& S){return S.Type==EDirectorNodeType::QTE;});
    TestEqual(TEXT("Hold joins prior motion before freezing"),Plan.StartFrames[HoldQ],300);
    return true;
}
#endif
