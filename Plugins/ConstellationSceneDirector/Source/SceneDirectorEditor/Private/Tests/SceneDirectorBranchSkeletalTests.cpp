#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorTestFixture.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorPlayer.h"
#include "Engine/Engine.h"
#include "Engine/World.h"

namespace
{
USceneDirectorAsset* MakeBranchSkeletalFixture()
{
    auto* Asset=MakeAnimationTestAsset();if(!Asset)return nullptr;
    const auto ActorClass=Asset->Steps[1].ActorClass;
    auto* Animation=Asset->Steps[2].Animation.Get();
    Asset->Steps.Reset();Asset->Steps.SetNum(9);auto& S=Asset->Steps;
    S[0].Type=EDirectorNodeType::Start;
    S[1].Type=EDirectorNodeType::SpawnNPC;S[1].Role=TEXT("Heroine");S[1].ActorClass=ActorClass;
    for(int32 I:{2,4,5})
    {
        S[I].Type=EDirectorNodeType::CharacterMove;S[I].Role=TEXT("Heroine");
        S[I].MoveTiming=EDirectorMoveTiming::Duration;S[I].Duration=.3f;
        S[I].bAutoLocomotion=false;S[I].Animation=Animation;
    }
    S[2].Destination.Value=FVector(100,0,0);
    S[3].Type=EDirectorNodeType::Dialogue;S[3].Role=TEXT("Heroine");S[3].Duration=.1f;
    S[3].DialogueText=FText::FromString(TEXT("Which direction?"));
    FDirectorChoice Left;Left.Key=TEXT("Left");Left.Text=FText::FromString(TEXT("Left"));
    FDirectorChoice Right;Right.Key=TEXT("Right");Right.Text=FText::FromString(TEXT("Right"));
    S[3].Choices={Left,Right};S[3].ChoiceTargets.Add(Left.Key,S[4].Id);S[3].ChoiceTargets.Add(Right.Key,S[5].Id);
    S[4].Destination.Mode=S[5].Destination.Mode=EDirectorValueMode::Current;
    S[4].Destination.Offset=FVector(0,100,0);S[5].Destination.Offset=FVector(0,-100,0);
    S[6].Type=EDirectorNodeType::Hub;S[7].Type=EDirectorNodeType::Wait;S[7].Duration=.1f;S[8].Type=EDirectorNodeType::End;
    for(int32 I=0;I<3;++I)S[I].NextNodes={S[I+1].Id};
    S[4].NextNodes=S[5].NextNodes={S[6].Id};S[6].NextNodes={S[7].Id};S[7].NextNodes={S[8].Id};
    return Asset;
}
TArray<FTransform> SampleBranchBones(USkeletalMeshComponent* Mesh)
{
    Mesh->TickAnimation(0.f,false);Mesh->RefreshBoneTransforms();
    return Mesh->GetComponentSpaceTransforms();
}
bool BranchBonesChanged(const TArray<FTransform>& First,const TArray<FTransform>& Second)
{
    for(int32 I=0;I<FMath::Min(First.Num(),Second.Num());++I)
        if(!First[I].Equals(Second[I],.001f))return true;
    return false;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorBranchSkeletalTest,"Constellation.SceneDirector.BranchSkeletalPlayback",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorBranchSkeletalTest::RunTest(const FString&)
{
    auto* Asset=MakeBranchSkeletalFixture();if(!TestNotNull(TEXT("Real heroine animation fixture"),Asset))return false;
    FString Error;if(!TestTrue(TEXT("Both skeletal paths compile"),FSceneDirectorCompiler::Compile(*Asset,Error))){AddError(Error);return false;}
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);World->InitializeActorsForPlay(FURL());
    auto* Runner=World->SpawnActor<ASceneDirectorPlayer>();Runner->bAutoPlay=false;Runner->Director=Asset;
    for(FName Answer:{FName(TEXT("Left")),FName(TEXT("Right"))})
    {
        if(!TestTrue(TEXT("Start skeletal branch"),Runner->PlayDirector())){AddError(Runner->LastError);break;}
        AActor* NPC=Runner->FindNPC(TEXT("Heroine"));
        auto* Mesh=NPC?NPC->FindComponentByClass<USkeletalMeshComponent>():nullptr;
        if(!TestNotNull(TEXT("Session has actual skeletal mesh"),Mesh)){Runner->StopDirector();break;}
        Runner->Tick(.1f);const auto Before=SampleBranchBones(Mesh);
        Runner->Tick(.1f);const auto Later=SampleBranchBones(Mesh);
        TestTrue(TEXT("Pre-choice motion evaluates actual bones"),BranchBonesChanged(Before,Later));
        Runner->Tick(1.f);
        TestTrue(TEXT("Skeletal motion reaches waiting choice"),Runner->IsWaitingForChoice());
        TestTrue(TEXT("Initial movement completed at choice"),NPC->GetActorLocation().Equals(FVector(100,0,0),.1));
        TestTrue(TEXT("Choose skeletal route"),Runner->SelectDialogueChoice(Answer));Runner->Tick(0.f);
        TestTrue(TEXT("Rebuild keeps session playing"),Runner->IsDirectorPlaying());
        TestTrue(TEXT("Rebuild reports no failure"),Runner->LastError.IsEmpty());
        TestEqual(TEXT("Rebuild retains same skeletal actor"),Runner->FindNPC(TEXT("Heroine")),NPC);
        TestTrue(TEXT("Rebuild preserves previous movement endpoint"),NPC->GetActorLocation().Equals(FVector(100,0,0),.1));
        Runner->Tick(.05f);const auto BranchFirst=SampleBranchBones(Mesh);
        Runner->Tick(.1f);const auto BranchSecond=SampleBranchBones(Mesh);
        const double Sign=Answer==TEXT("Left")?1.:-1.;
        TestTrue(TEXT("Selected movement uses current endpoint plus offset"),NPC->GetActorLocation().Equals(FVector(100,Sign*50,0),.1));
        TestTrue(TEXT("Actual bone animation continues in selected sequence"),BranchBonesChanged(BranchFirst,BranchSecond));
        Runner->Tick(1.f);
        TestFalse(TEXT("Skeletal branch joins and finishes"),Runner->IsDirectorPlaying());
        TestNull(TEXT("Finished NPC no longer resolves"),Runner->FindNPC(TEXT("Heroine")));
        TestTrue(TEXT("Session-owned skeletal actor removed"),!IsValid(NPC)||NPC->IsActorBeingDestroyed());
    }
    Runner->StopDirector();
    // A bound skeletal actor must retain its original animation mode and world pose after cancellation.
    auto* Existing=World->SpawnActor<AActor>(Asset->Steps[1].ActorClass,FVector(300,20,10),FRotator::ZeroRotator);
    if(TestNotNull(TEXT("Existing skeletal actor"),Existing))
    {
        Existing->Tags.Add(TEXT("BranchSkeletalBound"));const FTransform OriginalTransform=Existing->GetActorTransform();
        auto* Mesh=Existing->FindComponentByClass<USkeletalMeshComponent>();
        if(TestNotNull(TEXT("Existing mesh"),Mesh))
        {
            Mesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);Mesh->PlayAnimation(Asset->Steps[2].Animation,true);
            const auto OriginalMode=Mesh->GetAnimationMode();
            Asset->Steps[1].Type=EDirectorNodeType::BindNPC;Asset->Steps[1].ActorSource=EDirectorActorSource::Tag;Asset->Steps[1].ActorTag=TEXT("BranchSkeletalBound");
            if(TestTrue(TEXT("Bound skeletal branch compiles"),FSceneDirectorCompiler::Compile(*Asset,Error))&&TestTrue(TEXT("Bound skeletal session starts"),Runner->PlayDirector()))
            {
                Runner->Tick(1.f);TestTrue(TEXT("Bound actor reaches choice"),Runner->IsWaitingForChoice());
                Runner->SelectDialogueChoice(TEXT("Left"));Runner->Tick(.15f);
                TestEqual(TEXT("Bound actor identity survives rebuild"),Runner->FindNPC(TEXT("Heroine")),Existing);
                Runner->StopDirector();
                TestTrue(TEXT("Bound actor survives cancellation"),IsValid(Existing)&&!Existing->IsActorBeingDestroyed());
                TestTrue(TEXT("Bound actor original transform restored"),Existing->GetActorTransform().Equals(OriginalTransform));
                TestTrue(TEXT("Bound actor original animation mode restored"),Mesh->GetAnimationMode()==OriginalMode);
            }
        }
    }
    Runner->StopDirector();GEngine->DestroyWorldContext(World);World->DestroyWorld(false);return true;
}
#endif
