#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../SceneDirectorNodeMenu.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorConversationMenuTest,"Constellation.SceneDirector.ConversationNodes",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorConversationMenuTest::RunTest(const FString&)
{
    TestEqual(TEXT("All conversation and branch nodes"),DirectorNodeMenuEntries().Num(),28);
    return true;
}
#endif
#if WITH_DEV_AUTOMATION_TESTS
#include "SceneDirectorCompiler.h"
#include "SceneDirectorPlayer.h"
#include "LevelSequence.h"
#include "LevelSequenceActor.h"
#include "LevelSequencePlayer.h"
#include "EngineUtils.h"
#include "MovieScene.h"
#include "Tracks/MovieSceneCameraCutTrack.h"
#include "Sections/MovieSceneCameraCutSection.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/HUD.h"
#include "Camera/CameraActor.h"
#include "Camera/PlayerCameraManager.h"
static USceneDirectorAsset* ConversationFixture()
{
    auto* A=NewObject<USceneDirectorAsset>();
    for(auto Type:{EDirectorNodeType::Start,EDirectorNodeType::BindNPC,EDirectorNodeType::CinematicMode,EDirectorNodeType::CameraPreset,EDirectorNodeType::Dialogue,EDirectorNodeType::CameraSwitch,EDirectorNodeType::GameplayReturn,EDirectorNodeType::End})
    {FDirectorStep S;S.Type=Type;S.Role=TEXT("Lead");S.ActorClass=ACameraActor::StaticClass();S.Duration=.3f;A->Steps.Add(S);}
    for(int32 I=0;I<A->Steps.Num()-1;++I)A->Steps[I].NextNodes={A->Steps[I+1].Id};
    A->Steps[1].ActorSource=EDirectorActorSource::Tag;A->Steps[1].ActorTag=TEXT("ConversationLead");
    A->Steps[3].CameraKey=TEXT("ShotA");A->Steps[3].bWaitForCompletion=false;
    A->Steps[4].DialogueText=FText::FromString(TEXT("이제 이야기를 시작해 볼까요?"));A->Steps[4].DialogueAdvance=EDirectorDialogueAdvance::Click;
    A->Steps[5].CameraKey=TEXT("ShotB");A->Steps[5].BlendSeconds=.15f;
    FDirectorCameraEntry C;C.Key=TEXT("ShotB");C.Transform.SetLocation(FVector(200,100,170));A->Cameras.Add(C);
    return A;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorConversationScheduleTest,"Constellation.SceneDirector.ConversationSchedule",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorConversationScheduleTest::RunTest(const FString&)
{
    auto* A=ConversationFixture();FDirectorSchedule P;FString Error;
    if(!TestTrue(TEXT("Conversation schedule"),FSceneDirectorCompiler::Schedule(*A,P,Error))){AddError(Error);return false;}
    TestEqual(TEXT("Dialogue follows nonblocking shot immediately"),P.StartFrames[4],0);
    TestEqual(TEXT("Switch waits for dialogue"),P.StartFrames[5],9);
    TestTrue(TEXT("Preset generates an offset viewpoint"),P.ToPoses[3].GetLocation().Size()>100);
    if(!TestTrue(TEXT("Compile conversation"),FSceneDirectorCompiler::Compile(*A,Error))){AddError(Error);return false;}
    TestEqual(TEXT("Serialized cue count"),A->Cues.Num(),8);
    auto* Cuts=CastChecked<UMovieSceneCameraCutTrack>(A->GeneratedSequence->GetMovieScene()->GetCameraCutTrack());
    TestTrue(TEXT("Camera track blends"),Cuts->bCanBlend);
    TestEqual(TEXT("Switch has ease-in duration"),Cuts->GetAllSections()[1]->Easing.GetEaseInDuration(),5);
    auto* Framing=ConversationFixture();FDirectorStep Foreground=Framing->Steps[1];Foreground.Id=FGuid::NewGuid();Foreground.Role=TEXT("Foreground");Foreground.ActorTag=TEXT("Foreground");Foreground.Transform.SetLocation(FVector(100,0,0));
    Foreground.NextNodes=Framing->Steps[1].NextNodes;Framing->Steps[1].NextNodes={Foreground.Id};
    auto* ForegroundProfile=NewObject<USceneDirectorCharacterProfile>();ForegroundProfile->AimHeight=100;Foreground.Profile=ForegroundProfile;Framing->Steps.Add(Foreground);
    Framing->Steps[3].Framing=EDirectorFraming::OverShoulder;Framing->Steps[3].TargetRole=Foreground.Role;
    TestTrue(TEXT("Mixed-height over-shoulder compiles"),FSceneDirectorCompiler::Schedule(*Framing,P,Error));
    const FVector ForePoint(100,0,100);const FVector Direction=(FVector(0,0,150)-ForePoint).GetSafeNormal();
    const FVector Expected=ForePoint-Direction*90+FVector::CrossProduct(FVector::UpVector,Direction)*45;
    TestTrue(TEXT("Foreground uses own profile height"),P.ToPoses[3].GetLocation().Equals(Expected,.01));
    A->Steps[4].DialogueText=FText::GetEmpty();TestFalse(TEXT("Empty dialogue rejected"),FSceneDirectorCompiler::Schedule(*A,P,Error));
    A->Steps[4].DialogueText=FText::FromString(TEXT("대사"));A->Steps[4].DialogueAdvance=EDirectorDialogueAdvance::Voice;
    TestFalse(TEXT("Voice mode requires voice"),FSceneDirectorCompiler::Schedule(*A,P,Error));
    A->Steps[4].Type=EDirectorNodeType::Expression;
    TestFalse(TEXT("Expression requires a configured character profile"),FSceneDirectorCompiler::Schedule(*A,P,Error));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorConversationRuntimeTest,"Constellation.SceneDirector.ConversationRuntime",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorConversationRuntimeTest::RunTest(const FString&)
{
    UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());
    auto* PC=W->SpawnActor<APlayerController>();if(!PC->PlayerCameraManager){PC->PlayerCameraManager=W->SpawnActor<APlayerCameraManager>();PC->PlayerCameraManager->InitializeFor(PC);}
    PC->ClientSetHUD(AHUD::StaticClass());if(PC->GetHUD())PC->GetHUD()->bShowHUD=false;
    auto* OriginalCamera=W->SpawnActor<ACameraActor>();PC->SetViewTarget(OriginalCamera);
    auto* Existing=W->SpawnActor<ACameraActor>();Existing->Tags.Add(TEXT("ConversationLead"));Existing->SetActorLocation(FVector(900,100,50));const auto OriginalPose=Existing->GetActorTransform();
    auto* Runner=W->SpawnActor<ASceneDirectorPlayer>();Runner->bAutoPlay=false;Runner->Director=ConversationFixture();FString Error;
    if(!TestTrue(TEXT("Compile runtime fixture"),FSceneDirectorCompiler::Compile(*Runner->Director,Error))){AddError(Error);return false;}
    PC->SetIgnoreMoveInput(true); // A pre-existing independent lock must remain after our lock is released.
    TestTrue(TEXT("Start conversation"),Runner->PlayDirector());
    TestEqual(TEXT("Uses actual existing actor"),Runner->FindNPC(TEXT("Lead")),static_cast<AActor*>(Existing));
    TestTrue(TEXT("Look input locked"),PC->IsLookInputIgnored());
    Runner->Tick(5.f);
    TestTrue(TEXT("Large hitch stops at dialogue boundary"),Runner->IsWaitingForDialogue());
    TestFalse(TEXT("Dialogue remains visible"),Runner->CurrentDialogue.IsEmpty());
    Runner->Tick(10.f);TestTrue(TEXT("No advance while waiting"),Runner->IsDirectorPlaying());
    Runner->AdvanceDialogue();Runner->Tick(.1f);TestFalse(TEXT("Continue releases wait"),Runner->IsWaitingForDialogue());
    TestFalse(TEXT("Held dialogue stays across camera transition"),Runner->CurrentDialogue.IsEmpty());
    Runner->Tick(1.f);TestFalse(TEXT("Natural finish"),Runner->IsDirectorPlaying());
    TestTrue(TEXT("Bound actor survives"),IsValid(Existing));TestTrue(TEXT("Original transform restored"),Existing->GetActorTransform().Equals(OriginalPose));
    TestTrue(TEXT("Original input lock remains"),PC->IsMoveInputIgnored());TestFalse(TEXT("Our look lock released"),PC->IsLookInputIgnored());
    if(PC->GetHUD())TestFalse(TEXT("Original hidden HUD preserved"),PC->GetHUD()->bShowHUD);
    TestEqual(TEXT("Camera restored"),PC->GetViewTarget(),static_cast<AActor*>(OriginalCamera));
    TestTrue(TEXT("Replay"),Runner->PlayDirector());Runner->StopDirector();TestFalse(TEXT("Early stop restores input"),PC->IsLookInputIgnored());
    Runner->Director->Steps[3].Duration=1024;Runner->Director->Steps[4].Duration=1024;
    TestTrue(TEXT("Long dialogue compiles"),FSceneDirectorCompiler::Compile(*Runner->Director,Error));
    TestTrue(TEXT("Long dialogue starts"),Runner->PlayDirector());Runner->Tick(2000);
    TestTrue(TEXT("Long dialogue waits"),Runner->IsWaitingForDialogue());TestNull(TEXT("No next camera evaluated across long wait boundary"),Runner->FindCamera(TEXT("ShotB")));Runner->StopDirector();
    Runner->Director=ConversationFixture();
    FDirectorStep Reenter;Reenter.Type=EDirectorNodeType::CinematicMode;FDirectorStep Shot;Shot.Type=EDirectorNodeType::CameraSwitch;Shot.CameraKey=TEXT("ShotA");Shot.Duration=.3f;Shot.BlendSeconds=0;
    Reenter.NextNodes={Shot.Id};Shot.NextNodes={Runner->Director->Steps[7].Id};Runner->Director->Steps[6].NextNodes={Reenter.Id};Runner->Director->Steps.Add(Reenter);Runner->Director->Steps.Add(Shot);
    TestTrue(TEXT("Reentry graph compiles"),FSceneDirectorCompiler::Compile(*Runner->Director,Error));TestTrue(TEXT("Reentry starts"),Runner->PlayDirector());Runner->Tick(.31f);Runner->AdvanceDialogue();Runner->Tick(.32f);
    for(TActorIterator<ALevelSequenceActor> It(W);It;++It)TestTrue(TEXT("Return disables sequence camera"),It->GetSequencePlayer()->GetDisableCameraCuts());
    Runner->Tick(.32f);
    for(TActorIterator<ALevelSequenceActor> It(W);It;++It)TestFalse(TEXT("Reenter enables sequence camera"),It->GetSequencePlayer()->GetDisableCameraCuts());
    Runner->StopDirector();
    auto* Duplicate=W->SpawnActor<ACameraActor>();Duplicate->Tags=Existing->Tags;
    TestFalse(TEXT("Duplicate Actor tags rejected"),Runner->PlayDirector());Duplicate->Destroy();Existing->Tags.Reset();
    TestFalse(TEXT("Missing existing actor rejected"),Runner->PlayDirector());
    GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
#endif
#if WITH_DEV_AUTOMATION_TESTS
#include "SceneDirectorTestFixture.h"
#include "SceneDirectorPerformance.h"
#include "Animation/MorphTarget.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorExpressionSampleTest,"Constellation.SceneDirector.ExpressionSampleRestore",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorExpressionSampleTest::RunTest(const FString&)
{
    auto* Fixture=MakeAnimationTestAsset();if(!TestNotNull(TEXT("Character fixture"),Fixture))return false;
    auto* DefaultMesh=AActor::GetActorClassDefaultComponent<USkeletalMeshComponent>(Fixture->Steps[1].ActorClass);
    auto* Source=DefaultMesh->GetSkeletalMeshAsset();AddInfo(FString::Printf(TEXT("Heroine source morph count: %d"),Source->GetMorphTargets().Num()));
    auto* Copy=DuplicateObject<USkeletalMesh>(Source,GetTransientPackage());
    auto* Morph=NewObject<UMorphTarget>(Copy,TEXT("DirectorTestSmile"));FMorphTargetLODModel LOD;FMorphTargetDelta Delta;Delta.SourceIdx=0;Delta.PositionDelta=FVector3f(.1f,0,0);Delta.TangentZDelta=FVector3f::ZeroVector;LOD.Vertices.Add(Delta);LOD.NumVertices=1;LOD.NumBaseMeshVerts=1;Morph->GetMorphLODModels().Add(LOD);Copy->RegisterMorphTarget(Morph,false);Copy->InitMorphTargets();
    auto* Profile=NewObject<USceneDirectorCharacterProfile>();FDirectorExpressionPreset Smile;Smile.Morphs.Add(TEXT("DirectorTestSmile"),.9f);Profile->Expressions.Add(TEXT("Smile"),Smile);
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);World->InitializeActorsForPlay(FURL());
    auto* Actor=World->SpawnActor<ASkeletalMeshActor>();auto* Mesh=Actor->GetSkeletalMeshComponent();Mesh->SetSkeletalMeshAsset(Copy);Mesh->SetMorphTarget(TEXT("DirectorTestSmile"),.2f);
    FDirectorCue NPC;NPC.Step.Type=EDirectorNodeType::SpawnNPC;NPC.Step.Role=TEXT("Lead");NPC.Step.Profile=Profile;
    FDirectorCue Cue;Cue.Step.Type=EDirectorNodeType::Expression;Cue.Step.Role=TEXT("Lead");Cue.Step.ExpressionKey=TEXT("Smile");Cue.Step.Strength=.5f;Cue.Step.BlendSeconds=.2f;Cue.EndFrame=60;
    TArray<FDirectorCue> Cues{NPC,Cue};FString Error;FDirectorPerformance Sampler;
    auto Resolve=[Actor](FName)->AActor*{return Actor;};
    if(!TestTrue(TEXT("Sample expression"),Sampler.Evaluate(Cues,30,Resolve,Error))){AddError(Error);Sampler.Reset();GEngine->DestroyWorldContext(World);World->DestroyWorld(false);return false;}
    TestTrue(TEXT("Blend from original morph weight"),FMath::IsNearlyEqual(Mesh->GetMorphTarget(TEXT("DirectorTestSmile")),.55f));
    Sampler.Evaluate(Cues,0,Resolve,Error);TestTrue(TEXT("Backward scrub returns to initial weight"),FMath::IsNearlyEqual(Mesh->GetMorphTarget(TEXT("DirectorTestSmile")),.2f));
    Sampler.Evaluate(Cues,30,Resolve,Error);Sampler.Reset();TestTrue(TEXT("Stop restores expression"),FMath::IsNearlyEqual(Mesh->GetMorphTarget(TEXT("DirectorTestSmile")),.2f));
    Cue.Step.ExpressionKey=TEXT("Missing");Cues[1]=Cue;TestFalse(TEXT("Missing preset rejected at runtime"),Sampler.Evaluate(Cues,30,Resolve,Error));Sampler.Reset();
    GEngine->DestroyWorldContext(World);World->DestroyWorld(false);return true;
}
#endif
