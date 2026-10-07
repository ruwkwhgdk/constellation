#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"

static USceneDirectorAsset* ParallelGraph()
{
    auto* A=NewObject<USceneDirectorAsset>();
    for(auto Type:{EDirectorNodeType::Start,EDirectorNodeType::Wait,EDirectorNodeType::Wait,EDirectorNodeType::Hub,EDirectorNodeType::End})
    {FDirectorStep S;S.Type=Type;A->Steps.Add(S);}
    A->Steps[0].NextNodes={A->Steps[1].Id,A->Steps[2].Id};
    A->Steps[1].Duration=2;A->Steps[2].Duration=3;
    A->Steps[1].NextNodes={A->Steps[3].Id};A->Steps[2].NextNodes={A->Steps[3].Id};
    A->Steps[3].NextNodes={A->Steps[4].Id};return A;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorParallelTest,"Constellation.SceneDirector.ParallelScheduling",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorParallelTest::RunTest(const FString&)
{
    auto* A=ParallelGraph();FDirectorSchedule S;FString Error;
    if(!TestTrue(TEXT("Fan out and fan in supported"),FSceneDirectorCompiler::Schedule(*A,S,Error)))return false;
    TestEqual(TEXT("Both branches start together"),S.StartFrames[1],S.StartFrames[2]);
    TestEqual(TEXT("Join waits for longest branch"),S.StartFrames[3],90);
    TestEqual(TEXT("Parallel duration is max, not sum"),S.EndFrame,90);
    A->Steps[1].bWaitForCompletion=false;A->Steps[2].bWaitForCompletion=false;
    FSceneDirectorCompiler::Schedule(*A,S,Error);TestEqual(TEXT("Join overrides non-wait release"),S.StartFrames[3],90);
    A->Steps[3].NextNodes={A->Steps[1].Id};
    TestFalse(TEXT("Cycle rejected"),FSceneDirectorCompiler::Schedule(*A,S,Error));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorAsyncTest,"Constellation.SceneDirector.NonBlockingAction",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorAsyncTest::RunTest(const FString&)
{
    auto* A=ParallelGraph();
    A->Steps[0].NextNodes={A->Steps[1].Id};A->Steps[1].NextNodes={A->Steps[2].Id};A->Steps[2].NextNodes={A->Steps[3].Id};
    A->Steps[1].bWaitForCompletion=false;A->Steps[1].Duration=5;
    FDirectorSchedule S;FString Error;
    if(!TestTrue(TEXT("Nonblocking graph valid"),FSceneDirectorCompiler::Schedule(*A,S,Error)))return false;
    TestEqual(TEXT("Following action starts immediately"),S.StartFrames[2],0);
    TestEqual(TEXT("End keeps outstanding action alive"),S.EndFrame,150);
    A->Steps[1].bWaitForCompletion=true;FSceneDirectorCompiler::Schedule(*A,S,Error);
    TestEqual(TEXT("Wait enabled delays next action"),S.StartFrames[2],150);
    TestEqual(TEXT("Sequential duration"),S.EndFrame,240);
    return true;
}
#include "SceneDirectorTestFixture.h"
#include "SceneDirectorGraph.h"
#include "EdGraph/EdGraphPin.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "Tracks/MovieSceneSkeletalAnimationTrack.h"
#include "Sections/MovieSceneSkeletalAnimationSection.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorAnimationTest,"Constellation.SceneDirector.AnimationTrack",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorAnimationTest::RunTest(const FString&)
{
    auto* A=MakeAnimationTestAsset();if(!TestNotNull(TEXT("Project animation fixture"),A))return false;
    FString Error;if(!TestTrue(TEXT("Parallel animation and camera compile"),FSceneDirectorCompiler::Compile(*A,Error))){AddError(Error);return false;}
    auto* Track=A->GeneratedSequence->GetMovieScene()->FindTrack<UMovieSceneSkeletalAnimationTrack>(A->NPCBindings.FindChecked(TEXT("Heroine")));
    if(!TestNotNull(TEXT("Animation bound to named NPC"),Track))return false;
    auto* Section=CastChecked<UMovieSceneSkeletalAnimationSection>(Track->GetAllSections()[0]);
    TestEqual(TEXT("Requested duration"),Section->GetRange().Size<FFrameNumber>().Value,60);
    TestEqual(TEXT("Selected clip"),Section->Params.Animation.Get(),static_cast<UAnimSequenceBase*>(A->Steps[2].Animation.Get()));
    TestTrue(TEXT("Clip scaled to requested time"),FMath::IsNearlyEqual(Section->Params.PlayRate.AsFixedPlayRate(),double(A->Steps[2].Animation->GetPlayLength())/2));
        A->Steps[2].Animation=DuplicateObject<UAnimSequence>(A->Steps[2].Animation,GetTransientPackage());A->Steps[2].Animation->RateScale=2.f;
    TestTrue(TEXT("Asset rate scale compiles"),FSceneDirectorCompiler::Compile(*A,Error));
    Track=A->GeneratedSequence->GetMovieScene()->FindTrack<UMovieSceneSkeletalAnimationTrack>(A->NPCBindings.FindChecked(TEXT("Heroine")));
    Section=CastChecked<UMovieSceneSkeletalAnimationSection>(Track->GetAllSections()[0]);
    TestTrue(TEXT("Clip midpoint despite asset rate scale"),FMath::IsNearlyEqual(Section->Params.MapTimeToAnimation(Section,FFrameTime(30),FFrameRate(30,1)),double(A->Steps[2].Animation->GetPlayLength())*.5,.001));
    A->Steps[2].Animation=nullptr;FDirectorSchedule Plan;
    TestFalse(TEXT("Missing animation rejected"),FSceneDirectorCompiler::Schedule(*A,Plan,Error));
    A->Steps[2].Type=EDirectorNodeType::Camera;
    TestFalse(TEXT("Overlapping cameras rejected"),FSceneDirectorCompiler::Schedule(*A,Plan,Error));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorMultiGraphTest,"Constellation.SceneDirector.MultiGraphRoundtrip",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorMultiGraphTest::RunTest(const FString&)
{
    auto* A=ParallelGraph();auto* G=NewObject<USceneDirectorGraph>();G->Asset=A;G->Schema=USceneDirectorSchema::StaticClass();G->Load();
    auto* Start=CastChecked<USceneDirectorGraphNode>(G->Nodes[0]);auto* Hub=CastChecked<USceneDirectorGraphNode>(G->Nodes[3]);
    TestEqual(TEXT("Fanout loaded"),Start->FindPin(TEXT("Out"))->LinkedTo.Num(),2);
    TestEqual(TEXT("Fanin loaded"),Hub->FindPin(TEXT("In"))->LinkedTo.Num(),2);
    G->Sync();G->Load();TestEqual(TEXT("All outgoing edges saved"),A->Steps[0].NextNodes.Num(),2);
    auto* B=CastChecked<USceneDirectorGraphNode>(G->Nodes[1]);Hub=CastChecked<USceneDirectorGraphNode>(G->Nodes[3]);
    TestEqual(TEXT("Cycle cannot be drawn"),G->GetSchema()->CanCreateConnection(Hub->FindPin(TEXT("Out")),B->FindPin(TEXT("In"))).Response,CONNECT_RESPONSE_DISALLOW);
    A->FormatVersion=1;for(auto& S:A->Steps){S.NextNodes.Reset();S.Next.Invalidate();}A->Steps[0].Next=A->Steps[1].Id;A->PostLoad();
    TestEqual(TEXT("Legacy link migrated"),A->Steps[0].NextNodes.Num(),1);TestFalse(TEXT("Legacy link cleared"),A->Steps[0].Next.IsValid());
    A->Steps[0].NextNodes.Reset();A->Steps[0].Next=A->Steps[1].Id;A->bNeedsCompile=false;A->PostLoad();
    TestTrue(TEXT("Legacy links migrated even when old default version was omitted"),A->bNeedsCompile&&A->Steps[0].NextNodes.Num()==1&&!A->Steps[0].Next.IsValid());
    return true;
}
#endif
