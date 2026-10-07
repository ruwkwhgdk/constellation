#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorPlayer.h"
#include "SceneDirectorGraph.h"
#include "SceneDirectorTestFixture.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "Tracks/MovieScene3DTransformTrack.h"
#include "Sections/MovieScene3DTransformSection.h"
#include "Tracks/MovieSceneSpawnTrack.h"
#include "Sections/MovieSceneSpawnSection.h"
#include "Tracks/MovieSceneSubTrack.h"
#include "Sections/MovieSceneSubSection.h"
#include "Tracks/MovieSceneEventTrack.h"
#include "Channels/MovieSceneDoubleChannel.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "SceneDirectorLibrary.h"
#include "Conditions/MovieSceneGroupCondition.h"
#include "Bindings/MovieSceneSpawnableActorBinding.h"
#include "MovieSceneBindingReferences.h"
#include "Tracks/MovieSceneSkeletalAnimationTrack.h"
#include "Sections/MovieSceneSkeletalAnimationSection.h"
#include "Tracks/MovieSceneFloatTrack.h"
#include "Sections/MovieSceneFloatSection.h"
namespace
{
ULevelSequence* SourceFixture()
{
    auto* S=NewObject<ULevelSequence>();S->Initialize();auto* M=S->GetMovieScene();M->SetTickResolutionDirectly(FFrameRate(6000,1));M->SetDisplayRate(FFrameRate(24,1));M->SetPlaybackRange(6000,12000);
    auto* Template=NewObject<ACameraActor>(S);FGuid ID=M->AddSpawnable(TEXT("Actor"),*Template);
    auto* Spawn=M->AddTrack<UMovieSceneSpawnTrack>(ID);auto* SpawnSection=CastChecked<UMovieSceneSpawnSection>(Spawn->CreateNewSection());SpawnSection->SetRange(TRange<FFrameNumber>(6000,18000));SpawnSection->GetChannel().SetDefault(true);Spawn->AddSection(*SpawnSection);
    auto* T=M->AddTrack<UMovieScene3DTransformTrack>(ID);T->SetPropertyNameAndPath(TEXT("Transform"),TEXT("Transform"));auto* Sec=CastChecked<UMovieScene3DTransformSection>(T->CreateNewSection());Sec->SetRange(TRange<FFrameNumber>(6000,18000));auto Ch=Sec->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>();
    for(int32 I=0;I<9;++I)Ch[I]->SetDefault(I>=6?1:0);Ch[0]->AddLinearKey(6000,0);Ch[0]->AddLinearKey(18000,200);T->AddSection(*Sec);
    const FGuid Component=M->AddPossessable(TEXT("CameraComponent"),UCameraComponent::StaticClass());M->FindPossessable(Component)->SetParent(ID,M);
    auto* FOV=M->AddTrack<UMovieSceneFloatTrack>(Component);FOV->SetPropertyNameAndPath(TEXT("FieldOfView"),TEXT("FieldOfView"));auto* F=CastChecked<UMovieSceneFloatSection>(FOV->CreateNewSection());F->SetRange(TRange<FFrameNumber>(6000,18000));F->GetChannel().AddLinearKey(6000,60);F->GetChannel().AddLinearKey(18000,100);FOV->AddSection(*F);
    return S;
}
USceneDirectorAsset* ReuseFixture()
{
    auto* A=NewObject<USceneDirectorAsset>();A->Steps.SetNum(5);auto& S=A->Steps;
    S[0].Type=EDirectorNodeType::Start;S[1].Type=EDirectorNodeType::SpawnNPC;S[1].Role=TEXT("Hero");S[1].ActorClass=ACameraActor::StaticClass();S[1].Transform.SetLocation(FVector(5,0,0));
    S[2].Type=EDirectorNodeType::Sequence;S[2].SourceSequence=SourceFixture();DirectorSequence::RefreshRoles(S[2]);S[2].SequenceRoles[0].Target=EDirectorSequenceTarget::NPC;S[2].SequenceRoles[0].Key=TEXT("Hero");
    S[3].Type=EDirectorNodeType::Wait;S[3].Duration=.5f;S[4].Type=EDirectorNodeType::End;
    for(int32 I=0;I<4;++I)S[I].NextNodes={S[I+1].Id};return A;
}
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorSequenceCompileTest,"Constellation.SceneDirector.SequenceCompile",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorSequenceCompileTest::RunTest(const FString&)
{
    auto* A=ReuseFixture();FString Error;auto* Source=A->Steps[2].SourceSequence.Get();const FGuid Original=Source->GetMovieScene()->GetSpawnable(0).GetGuid();
    TestTrue(TEXT("Reuse compiles"),FSceneDirectorCompiler::Compile(*A,Error));if(!Error.IsEmpty())AddInfo(Error);
    TestEqual(TEXT("Source retains spawnable"),Source->GetMovieScene()->GetSpawnableCount(),1);TestEqual(TEXT("Original GUID unchanged"),Source->GetMovieScene()->GetSpawnable(0).GetGuid(),Original);
    auto* T=A->GeneratedSequence->GetMovieScene()->FindTrack<UMovieSceneSubTrack>();TestNotNull(TEXT("Generated native subsequence"),T);if(!T)return false;
    auto* Sec=CastChecked<UMovieSceneSubSection>(T->GetAllSections()[0]);TestTrue(TEXT("Source cloned not mutated"),Sec->GetSequence()!=Source);TestEqual(TEXT("Two second source duration"),Sec->GetExclusiveEndFrame().Value,60);
    A->Steps[2].SequenceSpeed=2;TestTrue(TEXT("Double speed compiles"),FSceneDirectorCompiler::Compile(*A,Error));TestEqual(TEXT("Automatic speed duration"),A->Cues[2].EndFrame-A->Cues[2].StartFrame,30);
    auto* Previous=A->GeneratedSequence.Get();Source->GetMovieScene()->AddTrack<UMovieSceneEventTrack>();TestFalse(TEXT("Event tracks explicitly rejected"),FSceneDirectorCompiler::Compile(*A,Error));TestEqual(TEXT("Failed compile keeps last output"),A->GeneratedSequence.Get(),Previous);
    A=ReuseFixture();A->Steps[2].SequenceRoles[0].Key=TEXT("Missing");TestFalse(TEXT("Unknown role rejected"),FSceneDirectorCompiler::Compile(*A,Error));
    A=ReuseFixture();auto* SourceTrack=A->Steps[2].SourceSequence->GetMovieScene()->FindTrack<UMovieScene3DTransformTrack>(A->Steps[2].SequenceRoles[0].Binding);
    SourceTrack->ConditionContainer.Condition=NewObject<UMovieSceneGroupCondition>(SourceTrack);TestFalse(TEXT("Track condition rejected without evaluation"),FSceneDirectorCompiler::Compile(*A,Error));SourceTrack->ConditionContainer.Condition=nullptr;
    SourceTrack->GetAllSections()[0]->ConditionContainer.Condition=NewObject<UMovieSceneGroupCondition>(SourceTrack);TestFalse(TEXT("Section condition rejected"),FSceneDirectorCompiler::Compile(*A,Error));SourceTrack->GetAllSections()[0]->ConditionContainer.Condition=nullptr;
    SourceTrack->FindOrAddTrackRowMetadata(0).ConditionContainer.Condition=NewObject<UMovieSceneGroupCondition>(SourceTrack);TestFalse(TEXT("Row condition rejected"),FSceneDirectorCompiler::Compile(*A,Error));
    A=ReuseFixture();A->Steps[2].SequenceSpeed=0;TestFalse(TEXT("Zero speed rejected"),FSceneDirectorCompiler::Compile(*A,Error));
    A=ReuseFixture();auto* G=NewObject<USceneDirectorGraph>();G->Asset=A;G->Load();G->Sync();TestTrue(TEXT("Graph roundtrip preserves sequence"),G->Asset->Steps[2].SourceSequence!=nullptr);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorSequenceRuntimeTest,"Constellation.SceneDirector.SequenceRuntime",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorSequenceRuntimeTest::RunTest(const FString&)
{
    auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());auto* R=W->SpawnActor<ASceneDirectorPlayer>();R->bAutoPlay=false;FString Error;
    // Include a cue so the graph uses the deterministic manual clock.
    auto* A=ReuseFixture();A->Steps[3].Type=EDirectorNodeType::GameplayReturn;R->Director=A;
    if(!TestTrue(TEXT("Compile playback"),FSceneDirectorCompiler::Compile(*A,Error))){AddError(Error);GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return false;}
    TestTrue(TEXT("Play"),R->PlayDirector());auto* NPC=R->FindNPC(TEXT("Hero"));TestNotNull(TEXT("Shared target exists"),NPC);R->Tick(1);
    if(NPC)TestTrue(TEXT("Nonzero source start and 6000 tick rate evaluate midpoint"),NPC->GetActorLocation().Equals(FVector(100,0,0),.1));TestEqual(TEXT("Same NPC instance"),R->FindNPC(TEXT("Hero")),NPC);
    if(auto* Camera=Cast<ACameraActor>(NPC))TestTrue(TEXT("Child component binding evaluates FOV"),FMath::IsNearlyEqual(Camera->GetCameraComponent()->FieldOfView,80.f,.1f));
    R->Tick(1.1f);if(NPC)TestTrue(TEXT("Source end restores parent graph pose"),NPC->GetActorLocation().Equals(FVector(5,0,0),.1));R->StopDirector();
    A->Steps[2].SequenceSpeed=2;FSceneDirectorCompiler::Compile(*A,Error);R->PlayDirector();NPC=R->FindNPC(TEXT("Hero"));R->Tick(.5f);if(NPC)TestTrue(TEXT("Double speed midpoint"),NPC->GetActorLocation().Equals(FVector(100,0,0),.1));R->StopDirector();
    A=ReuseFixture();A->Steps[3].Type=EDirectorNodeType::GameplayReturn;A->Steps[2].SourceSequence->GetMovieScene()->SetPlaybackRange(6000,6300);R->Director=A;
    auto* LockedMovie=A->Steps[2].SourceSequence->GetMovieScene();LockedMovie->SetReadOnly(true);auto* LockedSection=LockedMovie->FindTrack<UMovieScene3DTransformTrack>(A->Steps[2].SequenceRoles[0].Binding)->GetAllSections()[0];LockedSection->SetIsLocked(true);
    TestTrue(TEXT("Fractional duration compiles"),FSceneDirectorCompiler::Compile(*A,Error));R->PlayDirector();NPC=R->FindNPC(TEXT("Hero"));R->Tick(1.04f);if(NPC)TestTrue(TEXT("Frame inside original range evaluates"),NPC->GetActorLocation().Equals(FVector(104,0,0),.1));R->Tick(.02f);if(NPC)TestTrue(TEXT("Rounded tail never evaluates outside original source range"),NPC->GetActorLocation().Equals(FVector(5,0,0),.1));R->StopDirector();
    TestTrue(TEXT("Original remains read only and locked"),LockedMovie->IsReadOnly()&&LockedSection->IsLocked());
    // A skipped branch must not install/evaluate its clip.
    A=ReuseFixture();A->Steps.SetNum(8);auto& S=A->Steps;S[5].Type=EDirectorNodeType::Dialogue;S[5].Role=TEXT("Hero");S[5].DialogueText=FText::FromString(TEXT("Play clip?"));S[5].Duration=.1f;
    FDirectorChoice Yes;Yes.Key=TEXT("Play");Yes.Text=FText::FromString(TEXT("Play"));FDirectorChoice No;No.Key=TEXT("Skip");No.Text=FText::FromString(TEXT("Skip"));S[5].Choices={Yes,No};S[5].ChoiceTargets.Add(Yes.Key,S[2].Id);S[5].ChoiceTargets.Add(No.Key,S[6].Id);
    S[6].Type=EDirectorNodeType::Wait;S[6].Duration=2;S[6].NextNodes={S[7].Id};S[7].Type=EDirectorNodeType::Hub;S[7].NextNodes={S[3].Id};S[1].NextNodes={S[5].Id};S[2].NextNodes={S[7].Id};R->Director=A;
    TestTrue(TEXT("Branched reuse compiles"),FSceneDirectorCompiler::Compile(*A,Error));
    for(FName Choice:{FName(TEXT("Play")),FName(TEXT("Skip"))})
    {
        R->PlayDirector();R->Tick(10);NPC=R->FindNPC(TEXT("Hero"));TestTrue(TEXT("Waiting before clip"),R->IsWaitingForChoice());if(NPC)TestTrue(TEXT("Clip not evaluated before choice"),NPC->GetActorLocation().Equals(FVector(5,0,0),.1));
        R->SelectDialogueChoice(Choice);R->Tick(1);if(NPC)TestTrue(TEXT("Only selected clip evaluates"),NPC->GetActorLocation().Equals(FVector(Choice==TEXT("Play")?100:5,0,0),.1));R->StopDirector();
    }
    GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorSequenceSkeletalTest,"Constellation.SceneDirector.SequenceSkeletal",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorSequenceSkeletalTest::RunTest(const FString&)
{
    auto* A=USceneDirectorLibrary::CreateSequenceExample();if(!TestNotNull(TEXT("Saved reusable character example"),A))return false;
    A=DuplicateObject<USceneDirectorAsset>(A,GetTransientPackage());
    auto* Clip=A->Steps.FindByPredicate([](const FDirectorStep& S){return S.Type==EDirectorNodeType::Sequence&&S.SourceSequence;});if(!TestNotNull(TEXT("Reusable clip"),Clip))return false;
    Clip->SourceSequence=DuplicateObject<ULevelSequence>(Clip->SourceSequence,A);
    auto* Run=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_Run_Soft.AS_player_heroine_new_Run_Soft"));
    for(const auto& B:static_cast<const UMovieScene*>(Clip->SourceSequence->GetMovieScene())->GetBindings())for(auto* T:B.GetTracks())for(auto* Sec:T->GetAllSections())if(auto* Anim=Cast<UMovieSceneSkeletalAnimationSection>(Sec)){Anim->Params.Animation=Run;Anim->Params.PlayRate.Set(1.0);}
    FString Error;TestTrue(TEXT("Dynamic animation copy compiles"),FSceneDirectorCompiler::Compile(*A,Error));
    auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());auto* R=W->SpawnActor<ASceneDirectorPlayer>();R->bAutoPlay=false;R->Director=A;
    TestTrue(TEXT("Example starts"),R->PlayDirector());auto* NPC=R->FindNPC(TEXT("Hero"));auto* Mesh=NPC?NPC->FindComponentByClass<USkeletalMeshComponent>():nullptr;
    if(TestNotNull(TEXT("Shared heroine mesh"),Mesh))
    {
        R->Tick(.2f);Mesh->TickAnimation(0,false);Mesh->RefreshBoneTransforms();const auto First=Mesh->GetComponentSpaceTransforms();
        R->Tick(.5f);Mesh->TickAnimation(0,false);Mesh->RefreshBoneTransforms();const auto Second=Mesh->GetComponentSpaceTransforms();bool Changed=false;
        for(int32 I=0;I<FMath::Min(First.Num(),Second.Num());++I)if(!First[I].Equals(Second[I],.0001f)){Changed=true;break;}
        TestTrue(TEXT("Imported skeletal track evaluates actual bones"),Changed);TestEqual(TEXT("Same actor after clip"),R->FindNPC(TEXT("Hero")),NPC);
        R->Tick(4);TestTrue(TEXT("Continues into click dialogue"),R->IsWaitingForDialogue());R->AdvanceDialogue();R->Tick(10);TestFalse(TEXT("Example finishes"),R->IsDirectorPlaying());
    }
    R->StopDirector();GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorSequenceSourceTest,"Constellation.SceneDirector.SequenceSourceValidation",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorSequenceSourceTest::RunTest(const FString&)
{
    FString Error;auto* A=ReuseFixture();auto* M=A->Steps[2].SourceSequence->GetMovieScene();auto* Other=NewObject<ACameraActor>(A->Steps[2].SourceSequence);M->AddSpawnable(TEXT("Other"),*Other);DirectorSequence::RefreshRoles(A->Steps[2]);
    for(auto& Role:A->Steps[2].SequenceRoles){Role.Target=EDirectorSequenceTarget::NPC;Role.Key=Role.Label==TEXT("Actor")?FName(TEXT("Hero")):FName(TEXT("hero"));}
    TestFalse(TEXT("Duplicate role check uses case-insensitive FName"),FSceneDirectorCompiler::Compile(*A,Error));
    auto* Source=NewObject<ULevelSequence>();Source->Initialize();M=Source->GetMovieScene();M->SetTickResolutionDirectly(FFrameRate(30,1));M->SetPlaybackRange(0,60);
    auto* Template=NewObject<ASkeletalMeshActor>(Source);Template->GetSkeletalMeshComponent()->SetSkeletalMeshAsset(LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/SK_player_heroine_new_RunPreview.SK_player_heroine_new_RunPreview")));
    FGuid ID=M->AddSpawnable(TEXT("HandAuthoredActor"),*Template);M->FindSpawnable(ID)->SetSpawnOwnership(ESpawnOwnership::External);
    auto* Spawn=M->AddTrack<UMovieSceneSpawnTrack>(ID);auto* SpawnSec=CastChecked<UMovieSceneSpawnSection>(Spawn->CreateNewSection());SpawnSec->SetRange(TRange<FFrameNumber>(0,60));SpawnSec->GetChannel().SetDefault(true);Spawn->AddSection(*SpawnSec);
    auto* AnimTrack=M->AddTrack<UMovieSceneSkeletalAnimationTrack>(ID);auto* Anim=CastChecked<UMovieSceneSkeletalAnimationSection>(AnimTrack->CreateNewSection());Anim->Params.Animation=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_Run_Soft.AS_player_heroine_new_Run_Soft"));Anim->SetRange(TRange<FFrameNumber>(0,60));AnimTrack->AddSection(*Anim);
    A=NewObject<USceneDirectorAsset>();A->Steps.SetNum(3);A->Steps[0].Type=EDirectorNodeType::Start;A->Steps[1].Type=EDirectorNodeType::Sequence;A->Steps[1].SourceSequence=Source;A->Steps[2].Type=EDirectorNodeType::End;A->Steps[0].NextNodes={A->Steps[1].Id};A->Steps[1].NextNodes={A->Steps[2].Id};
    TestTrue(TEXT("Legacy source validates assigned template mesh, not empty class default"),FSceneDirectorCompiler::Compile(*A,Error));
    if(A->GeneratedSequence){auto* Sub=A->GeneratedSequence->GetMovieScene()->FindTrack<UMovieSceneSubTrack>();auto* Copy=Cast<ULevelSequence>(CastChecked<UMovieSceneSubSection>(Sub->GetAllSections()[0])->GetSequence());TestTrue(TEXT("Copy owns original actor only within subsection"),Copy->GetMovieScene()->GetSpawnable(0).GetSpawnOwnership()==ESpawnOwnership::InnerSequence);}
    TestTrue(TEXT("Original ownership stays unchanged"),M->FindSpawnable(ID)->GetSpawnOwnership()==ESpawnOwnership::External);
    const FMovieSceneBinding Saved=*M->FindBinding(ID);M->RemoveSpawnable(ID);FMovieScenePossessable Possess(TEXT("NativeSpawnable"),ASkeletalMeshActor::StaticClass());Possess.SetGuid(ID);M->AddPossessable(Possess,Saved);
    auto* Native=NewObject<UMovieSceneSpawnableActorBinding>(M);Native->SetObjectTemplate(Template);Source->UMovieSceneSequence::GetBindingReferences()->AddBinding(ID,Native);
    TestTrue(TEXT("Modern native spawnable actor template supported"),FSceneDirectorCompiler::Compile(*A,Error));return true;
}
#endif
