#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorBranching.h"
#include "SceneDirectorCompiler.h"
#include "GameFramework/Character.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "Tracks/MovieSceneCameraCutTrack.h"
#include "Sections/MovieSceneCameraCutSection.h"
static USceneDirectorAsset* BranchGraph()
{
    auto* A=NewObject<USceneDirectorAsset>();
    for(auto T:{EDirectorNodeType::Start,EDirectorNodeType::Dialogue,EDirectorNodeType::Wait,EDirectorNodeType::Wait,EDirectorNodeType::Hub,EDirectorNodeType::End})
    {FDirectorStep S;S.Type=T;S.Duration=1;A->Steps.Add(S);}
    auto& Q=A->Steps[1];Q.DialogueText=FText::FromString(TEXT("Choose"));
    FDirectorChoice C;C.Key=TEXT("A");C.Text=FText::FromString(TEXT("A"));Q.Choices.Add(C);C.Key=TEXT("B");C.Text=FText::FromString(TEXT("B"));Q.Choices.Add(C);
    A->Steps[0].NextNodes={Q.Id};Q.ChoiceTargets.Add(TEXT("A"),A->Steps[2].Id);Q.ChoiceTargets.Add(TEXT("B"),A->Steps[3].Id);
    A->Steps[2].NextNodes={A->Steps[4].Id};A->Steps[3].NextNodes={A->Steps[4].Id};A->Steps[4].NextNodes={A->Steps[5].Id};FDirectorStep NPC;NPC.Type=EDirectorNodeType::SpawnNPC;NPC.Role=TEXT("Speaker");NPC.ActorClass=ACharacter::StaticClass();NPC.NextNodes={Q.Id};Q.Role=NPC.Role;A->Steps[0].NextNodes={NPC.Id};A->Steps.Add(NPC);return A;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorBranchResolverTest,"Constellation.SceneDirector.BranchResolver",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorBranchResolverTest::RunTest(const FString&)
{
    auto* A=BranchGraph();auto* R=NewObject<USceneDirectorAsset>();FGuid Pending;FString Error;TMap<FGuid,FName> Decisions;
    TestTrue(TEXT("Unanswered prefix resolves"),DirectorBranching::Resolve(*A,Decisions,{},*R,Pending,Error));TestEqual(TEXT("Pending stable ID"),Pending,A->Steps[1].Id);TestEqual(TEXT("Prefix includes synthetic End"),R->Steps.Num(),4);
    Decisions.Add(Pending,TEXT("B"));TestTrue(TEXT("Selected path resolves"),DirectorBranching::Resolve(*A,Decisions,{},*R,Pending,Error));TestFalse(TEXT("Complete route"),Pending.IsValid());TestEqual(TEXT("Inactive branch omitted"),R->Steps.Num(),6);
    TestFalse(TEXT("A absent"),R->Steps.ContainsByPredicate([&](const FDirectorStep& S){return S.Id==A->Steps[2].Id;}));if(!TestTrue(TEXT("All paths validate"),DirectorBranching::ValidateAll(*A,Error)))AddError(Error);
    A->Steps[1].ChoiceTargets.Remove(TEXT("B"));TestFalse(TEXT("Missing output rejected"),DirectorBranching::ValidateAll(*A,Error));
    A=BranchGraph();FDirectorStep Parallel;Parallel.Type=EDirectorNodeType::Wait;Parallel.Duration=1;Parallel.NextNodes={A->Steps[4].Id};A->Steps[0].NextNodes.Add(Parallel.Id);A->Steps.Add(Parallel);TestFalse(TEXT("Parallel decision rejected"),DirectorBranching::ValidateAll(*A,Error));
    A=BranchGraph();A->Steps[2].Type=EDirectorNodeType::SetBool;A->Steps[2].BoolKey=TEXT("Seen");FDirectorBoolEntry V;V.Key=TEXT("Seen");A->BoolVariables.Add(V);
    A->Steps[4].Type=EDirectorNodeType::Condition;A->Steps[4].BoolKey=TEXT("Seen");A->Steps[4].NextNodes.Empty();A->Steps[4].TrueTarget=A->Steps[5].Id;A->Steps[4].FalseTarget=A->Steps[5].Id;
    if(!TestTrue(TEXT("Selected writes and condition merge supported"),DirectorBranching::ValidateAll(*A,Error)))AddError(Error);
    A->Steps[4].BoolKey=TEXT("Missing");TestFalse(TEXT("Unknown variable rejected"),DirectorBranching::ValidateAll(*A,Error));return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorBranchVariablesTest,"Constellation.SceneDirector.BranchVariablesAndNested",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorBranchVariablesTest::RunTest(const FString&)
{
    auto* A=BranchGraph();auto* R=NewObject<USceneDirectorAsset>();FString Error;FGuid Pending;
    FDirectorBoolEntry V;V.Key=TEXT("Seen");A->BoolVariables.Add(V);
    auto& Condition=A->Steps[1];Condition.Type=EDirectorNodeType::Condition;Condition.Choices.Empty();Condition.ChoiceTargets.Empty();Condition.BoolKey=V.Key;Condition.TrueTarget=A->Steps[2].Id;Condition.FalseTarget=A->Steps[3].Id;
    TestTrue(TEXT("Default condition resolves"),DirectorBranching::Resolve(*A,{},{},*R,Pending,Error));
    TestTrue(TEXT("False route selected"),R->Steps.ContainsByPredicate([&](const FDirectorStep& S){return S.Id==A->Steps[3].Id;}));
    TMap<FName,bool> Overrides;Overrides.Add(V.Key,true);
    TestTrue(TEXT("Initial override resolves"),DirectorBranching::Resolve(*A,{},Overrides,*R,Pending,Error));
    TestFalse(TEXT("Override removes false route"),R->Steps.ContainsByPredicate([&](const FDirectorStep& S){return S.Id==A->Steps[3].Id;}));
    A->Steps[2].Type=EDirectorNodeType::Expression;A->Steps[2].Role=TEXT("MissingNPC");
    TestFalse(TEXT("Non-default conditional route validated"),DirectorBranching::ValidateAll(*A,Error));A->Steps[2].Type=EDirectorNodeType::Wait;
    FDirectorStep Write;Write.Type=EDirectorNodeType::SetBool;Write.BoolKey=V.Key;Write.BoolValue=true;Write.NextNodes={Condition.Id};A->Steps[6].NextNodes={Write.Id};A->Steps.Add(Write);
    TestTrue(TEXT("Write before condition resolves"),DirectorBranching::Resolve(*A,{},{},*R,Pending,Error));
    TestFalse(TEXT("Write selects true route"),R->Steps.ContainsByPredicate([&](const FDirectorStep& S){return S.Id==A->Steps[3].Id;}));
    Overrides.Add(TEXT("Unknown"),false);TestFalse(TEXT("Unknown override rejected"),DirectorBranching::Resolve(*A,{},Overrides,*R,Pending,Error));
    A=BranchGraph();FDirectorStep Nested=A->Steps[1];Nested.Id=FGuid::NewGuid();Nested.ChoiceTargets[TEXT("A")]=A->Steps[4].Id;Nested.ChoiceTargets[TEXT("B")]=A->Steps[4].Id;
    A->Steps[2].NextNodes={Nested.Id};A->Steps.Add(Nested);TMap<FGuid,FName> Decisions;Decisions.Add(A->Steps[1].Id,TEXT("A"));
    TestTrue(TEXT("Nested prefix resolves"),DirectorBranching::Resolve(*A,Decisions,{},*R,Pending,Error));TestEqual(TEXT("Nested decision awaits"),Pending,Nested.Id);
    TestTrue(TEXT("Same target choices validate"),DirectorBranching::ValidateAll(*A,Error));
    A->Steps[3].NextNodes={A->Steps[0].Id};TestFalse(TEXT("Cycle rejected"),DirectorBranching::ValidateAll(*A,Error));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorBranchCompileTest,"Constellation.SceneDirector.BranchCompileIsolation",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorBranchCompileTest::RunTest(const FString&)
{
    auto* A=BranchGraph();FString Error;const FGuid AID=A->Steps[2].Id,BID=A->Steps[3].Id;
    A->Steps[1].PreviewChoiceIndex=2;TestTrue(TEXT("Preview compiles"),FSceneDirectorCompiler::Compile(*A,Error));
    TestEqual(TEXT("Source retains all nodes"),A->Steps.Num(),7);TestEqual(TEXT("Source retains outputs"),A->Steps[1].ChoiceTargets.Num(),2);
    TestFalse(TEXT("Unchosen cue absent"),A->Cues.ContainsByPredicate([&](const FDirectorCue& C){return C.Step.Id==AID;}));
    TestTrue(TEXT("Chosen cue present"),A->Cues.ContainsByPredicate([&](const FDirectorCue& C){return C.Step.Id==BID;}));
    auto* Previous=A->GeneratedSequence.Get();A->Steps[1].ChoiceTargets.Remove(TEXT("A"));TestFalse(TEXT("Invalid source fails"),FSceneDirectorCompiler::Compile(*A,Error));TestTrue(TEXT("Previous sequence preserved"),Previous==A->GeneratedSequence.Get());TestTrue(TEXT("Failed branch compile marks previous result stale"),A->bNeedsCompile);
    A=BranchGraph();A->Steps[3].Type=EDirectorNodeType::Expression;A->Steps[3].Role=TEXT("MissingNPC");TestFalse(TEXT("Every selected route checks NPC availability"),DirectorBranching::ValidateAll(*A,Error));return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorBranchCameraHoldTest,"Constellation.SceneDirector.BranchCameraHold",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorBranchCameraHoldTest::RunTest(const FString&)
{
    auto* A=BranchGraph();FDirectorStep Camera;Camera.Type=EDirectorNodeType::Camera;Camera.CameraKey=TEXT("SharedShot");Camera.Duration=1;Camera.bWaitForCompletion=false;Camera.bLookAtTarget=false;Camera.NextNodes={A->Steps[1].Id};A->Steps[6].NextNodes={Camera.Id};A->Steps.Add(Camera);
    for(int32 I:{2,3}){A->Steps[I].Type=EDirectorNodeType::Dialogue;A->Steps[I].Role=TEXT("Speaker");A->Steps[I].DialogueText=FText::FromString(TEXT("Response"));}
    auto* Prefix=NewObject<USceneDirectorAsset>();FGuid Pending;FString Error;TMap<FGuid,FName> Decisions;
    if(!TestTrue(TEXT("Camera prefix resolves"),DirectorBranching::Resolve(*A,Decisions,{},*Prefix,Pending,Error))||!TestTrue(TEXT("Camera prefix compiles"),FSceneDirectorCompiler::Compile(*Prefix,Error))){AddError(Error);return false;}
    auto* Cuts=Cast<UMovieSceneCameraCutTrack>(Prefix->GeneratedSequence->GetMovieScene()->GetCameraCutTrack());
    if(!TestNotNull(TEXT("Prefix has camera cut"),Cuts))return false;
    TestTrue(TEXT("Shot covers choice dialogue after its action ends"),Cuts->GetAllSections()[0]->GetRange().Contains(FFrameNumber(45)));
    TestEqual(TEXT("One camera in prefix"),Prefix->CameraBindings.Num(),1);TestTrue(TEXT("Stable logical camera key"),Prefix->CameraBindings.Contains(Camera.CameraKey));
    Decisions.Add(Pending,TEXT("A"));auto* Extended=NewObject<USceneDirectorAsset>();
    if(!TestTrue(TEXT("Extended route resolves"),DirectorBranching::Resolve(*A,Decisions,{},*Extended,Pending,Error))||!TestTrue(TEXT("Extended route compiles"),FSceneDirectorCompiler::Compile(*Extended,Error))){AddError(Error);return false;}
    Cuts=Cast<UMovieSceneCameraCutTrack>(Extended->GeneratedSequence->GetMovieScene()->GetCameraCutTrack());
    if(!TestNotNull(TEXT("Extended route has camera cut"),Cuts))return false;
    TestTrue(TEXT("Same shot covers following dialogue"),Cuts->GetAllSections()[0]->GetRange().Contains(FFrameNumber(75)));
    TestEqual(TEXT("Prefix growth retains one logical camera"),Extended->CameraBindings.Num(),1);TestTrue(TEXT("Extended route retains camera key"),Extended->CameraBindings.Contains(Camera.CameraKey));return true;
}
#endif
