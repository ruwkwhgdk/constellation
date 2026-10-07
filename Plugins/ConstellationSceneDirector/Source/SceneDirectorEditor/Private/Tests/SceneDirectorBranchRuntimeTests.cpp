#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorPlayer.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorBranching.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/LocalPlayer.h"
#include "Camera/CameraActor.h"
#include "GameFramework/PlayerController.h"
static USceneDirectorAsset* BranchRuntimeFixture()
{
    auto* A=NewObject<USceneDirectorAsset>();A->Steps.SetNum(16);
    auto& S=A->Steps;
    S[0].Type=EDirectorNodeType::Start;
    S[1].Type=EDirectorNodeType::SpawnNPC;S[1].Role=TEXT("Lead");S[1].ActorClass=ACameraActor::StaticClass();
    S[2].Type=EDirectorNodeType::CinematicMode;
    S[3].Type=EDirectorNodeType::CameraMove;S[3].CameraKey=TEXT("Main");S[3].Duration=.3f;S[3].Destination.Value=FVector(100,0,120);
    S[4].Type=EDirectorNodeType::Dialogue;S[4].Role=TEXT("Lead");S[4].Duration=.1f;S[4].DialogueText=FText::FromString(TEXT("도와줄까?"));
    FDirectorChoice Yes;Yes.Key=TEXT("Yes");Yes.Text=FText::FromString(TEXT("도와준다"));FDirectorChoice No;No.Key=TEXT("No");No.Text=FText::FromString(TEXT("거절한다"));S[4].Choices={Yes,No};
    S[4].ChoiceTargets.Add(Yes.Key,S[5].Id);S[4].ChoiceTargets.Add(No.Key,S[6].Id);
    S[5].Type=S[6].Type=EDirectorNodeType::SetBool;S[5].BoolKey=S[6].BoolKey=TEXT("Accepted");S[5].BoolValue=true;S[6].BoolValue=false;
    S[7].Type=EDirectorNodeType::Condition;S[7].BoolKey=TEXT("Accepted");S[7].TrueTarget=S[8].Id;S[7].FalseTarget=S[9].Id;
    S[8].Type=S[9].Type=EDirectorNodeType::SpawnNPC;S[8].Role=TEXT("AcceptedNPC");S[9].Role=TEXT("DeclinedNPC");S[8].ActorClass=S[9].ActorClass=ACameraActor::StaticClass();
    S[10].Type=S[11].Type=EDirectorNodeType::Dialogue;S[10].Role=S[11].Role=TEXT("Lead");S[10].Duration=S[11].Duration=.2f;
    S[10].DialogueText=FText::FromString(TEXT("고마워!"));S[11].DialogueText=FText::FromString(TEXT("다음에 보자."));
    S[12].Type=EDirectorNodeType::Hub;S[13].Type=EDirectorNodeType::Wait;S[13].Duration=.1f;
    S[14].Type=EDirectorNodeType::GameplayReturn;S[14].Duration=.1f;S[15].Type=EDirectorNodeType::End;
    for(int32 I=0;I<4;++I)S[I].NextNodes={S[I+1].Id};
    S[5].NextNodes=S[6].NextNodes={S[7].Id};S[8].NextNodes={S[10].Id};S[9].NextNodes={S[11].Id};
    S[10].NextNodes=S[11].NextNodes={S[12].Id};S[12].NextNodes={S[13].Id};S[13].NextNodes={S[14].Id};S[14].NextNodes={S[15].Id};
    FDirectorBoolEntry Flag;Flag.Key=TEXT("Accepted");Flag.Value=false;A->BoolVariables.Add(Flag);return A;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorBranchRuntimeTest,"Constellation.SceneDirector.BranchRuntime",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorBranchRuntimeTest::RunTest(const FString&)
{
    UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());
    auto* PC=W->SpawnActor<APlayerController>();
    // Camera-cut playback resolves the first local player through GameInstance, not just World's controller list.
    auto* GI=NewObject<UGameInstance>(GEngine);W->SetGameInstance(GI);
    auto* LocalPlayer=NewObject<ULocalPlayer>(GEngine);LocalPlayer->PlayerController=PC;PC->Player=LocalPlayer;
    GI->AddLocalPlayer(LocalPlayer,FPlatformUserId::CreateFromInternalId(0));
    auto Cleanup=[&]() { LocalPlayer->PlayerController=nullptr;PC->Player=nullptr;GI->RemoveLocalPlayer(LocalPlayer);W->SetGameInstance(nullptr);GEngine->DestroyWorldContext(W);W->DestroyWorld(false); };
    auto* OriginalCamera=W->SpawnActor<ACameraActor>();PC->SetViewTarget(OriginalCamera);
    auto* Runner=W->SpawnActor<ASceneDirectorPlayer>();Runner->bAutoPlay=false;Runner->Director=BranchRuntimeFixture();FString Error;
    if(!TestTrue(TEXT("All branches compile"),FSceneDirectorCompiler::Compile(*Runner->Director,Error))){AddError(Error);Cleanup();return false;}
    for(const FName Answer:{FName(TEXT("Yes")),FName(TEXT("No"))})
    {
        const bool Accepted=Answer==TEXT("Yes");
        if(!TestTrue(TEXT("Start branch session"),Runner->PlayDirector())){AddError(Runner->LastError);break;}
        Runner->Tick(1);TestTrue(TEXT("Choice boundary waits after hitch"),Runner->IsWaitingForChoice());
        AActor* Lead=Runner->FindNPC(TEXT("Lead"));AActor* Camera=Runner->FindCamera(TEXT("Main"));
        TestNotNull(TEXT("Session NPC exists"),Lead);TestNotNull(TEXT("Session camera exists"),Camera);
        TestEqual(TEXT("Shot held while awaiting choice"),PC->GetViewTarget(),Camera);
        const FVector Pose=Camera?Camera->GetActorLocation():FVector::ZeroVector;
        TestTrue(TEXT("Pre-choice camera move completed"),Pose.Equals(FVector(100,0,120),.1));
        TestNull(TEXT("True branch not spawned before choice"),Runner->FindNPC(TEXT("AcceptedNPC")));
        TestNull(TEXT("False branch not spawned before choice"),Runner->FindNPC(TEXT("DeclinedNPC")));
        Runner->AdvanceDialogue();TestTrue(TEXT("Ordinary advance cannot skip choice"),Runner->IsWaitingForChoice());
        TestTrue(TEXT("Select answer"),Runner->SelectDialogueChoice(Answer));Runner->Tick(.01f);
        TestTrue(TEXT("Runtime rebuild succeeds"),Runner->LastError.IsEmpty());
        TestEqual(TEXT("Same NPC instance after decision"),Runner->FindNPC(TEXT("Lead")),Lead);
        TestEqual(TEXT("Same camera instance after decision"),Runner->FindCamera(TEXT("Main")),Camera);
        TestEqual(TEXT("Shot held after sequence replacement"),PC->GetViewTarget(),Camera);
        if(Camera)TestTrue(TEXT("Camera pose survives sequence replacement"),Camera->GetActorLocation().Equals(Pose,.1));
        TestNotNull(TEXT("Chosen path spawns NPC"),Runner->FindNPC(Accepted?TEXT("AcceptedNPC"):TEXT("DeclinedNPC")));
        TestNull(TEXT("Unchosen path does not spawn NPC"),Runner->FindNPC(Accepted?TEXT("DeclinedNPC"):TEXT("AcceptedNPC")));
        TestEqual(TEXT("Only chosen setter runs"),Runner->BoolValues.FindRef(TEXT("Accepted")),Accepted);
        TestEqual(TEXT("Selected condition dialogue"),Runner->CurrentDialogue.ToString(),Accepted?FString(TEXT("고마워!")):FString(TEXT("다음에 보자.")));
        TestTrue(TEXT("Input stays locked across decision"),PC->IsMoveInputIgnored());
        Runner->Tick(2);TestFalse(TEXT("Join completes without waiting skipped path"),Runner->IsDirectorPlaying());
        TestFalse(TEXT("Movement unlocked on finish"),PC->IsMoveInputIgnored());TestEqual(TEXT("Camera restored on finish"),PC->GetViewTarget(),static_cast<AActor*>(OriginalCamera));
        TestTrue(TEXT("Owned NPC cleaned"),!IsValid(Lead)||Lead->IsActorBeingDestroyed());
    }
    TestTrue(TEXT("Restart for cancellation"),Runner->PlayDirector());Runner->Tick(1);Runner->StopDirector();
    TestFalse(TEXT("Choice stop clears pending"),Runner->IsWaitingForChoice());TestFalse(TEXT("Choice stop restores input"),PC->IsMoveInputIgnored());
    Runner->InitialBoolOverrides.Add(TEXT("Missing"),true);TestFalse(TEXT("Unknown initial override rejected"),Runner->PlayDirector());Runner->InitialBoolOverrides.Reset();
    // Nested choices keep earlier decisions, completed controls and spawned actors.
    Runner->Director=BranchRuntimeFixture();auto& Nested=Runner->Director->Steps[12];
    Nested.Type=EDirectorNodeType::Dialogue;Nested.Role=TEXT("Lead");Nested.Duration=.1f;Nested.DialogueText=FText::FromString(TEXT("어디로 갈까?"));
    FDirectorChoice Left;Left.Key=TEXT("Left");Left.Text=FText::FromString(TEXT("왼쪽"));FDirectorChoice Right;Right.Key=TEXT("Right");Right.Text=FText::FromString(TEXT("오른쪽"));
    Nested.Choices={Left,Right};Nested.ChoiceTargets.Add(Left.Key,Runner->Director->Steps[13].Id);Nested.ChoiceTargets.Add(Right.Key,Runner->Director->Steps[13].Id);Nested.NextNodes.Reset();
    TestTrue(TEXT("Nested choices compile"),FSceneDirectorCompiler::Compile(*Runner->Director,Error));
    TestTrue(TEXT("Nested session starts"),Runner->PlayDirector());Runner->Tick(1);Runner->SelectDialogueChoice(TEXT("Yes"));Runner->Tick(1);
    TestTrue(TEXT("Wait at second choice"),Runner->IsWaitingForChoice());TestEqual(TEXT("Second prompt shown"),Runner->CurrentDialogue.ToString(),FString(TEXT("어디로 갈까?")));
    AActor* AcceptedNPC=Runner->FindNPC(TEXT("AcceptedNPC"));TestNotNull(TEXT("First branch NPC retained at next decision"),AcceptedNPC);
    Runner->SelectDialogueChoice(TEXT("Right"));Runner->Tick(.01f);TestEqual(TEXT("First branch NPC retained after next decision"),Runner->FindNPC(TEXT("AcceptedNPC")),AcceptedNPC);
    TestTrue(TEXT("Earlier setter state retained"),Runner->BoolValues.FindRef(TEXT("Accepted")));Runner->Tick(2);TestFalse(TEXT("Nested branch completes"),Runner->IsDirectorPlaying());
    TestFalse(TEXT("Cinematic lock not double-applied"),PC->IsMoveInputIgnored());
    // Initial Bool overrides choose routes before the first question.
    Runner->Director=BranchRuntimeFixture();auto& InitialCondition=Runner->Director->Steps[4];
    InitialCondition.Type=EDirectorNodeType::Condition;InitialCondition.Choices.Reset();InitialCondition.ChoiceTargets.Reset();InitialCondition.BoolKey=TEXT("Accepted");InitialCondition.TrueTarget=Runner->Director->Steps[5].Id;InitialCondition.FalseTarget=Runner->Director->Steps[6].Id;
    TestTrue(TEXT("Initial condition graph compiles"),FSceneDirectorCompiler::Compile(*Runner->Director,Error));
    Runner->InitialBoolOverrides.Add(TEXT("Accepted"),true);TestTrue(TEXT("Override true starts"),Runner->PlayDirector());Runner->Tick(.31f);
    TestNotNull(TEXT("Override selected true path"),Runner->FindNPC(TEXT("AcceptedNPC")));TestNull(TEXT("Override skipped false path"),Runner->FindNPC(TEXT("DeclinedNPC")));Runner->StopDirector();Runner->InitialBoolOverrides.Reset();
    // Binding and failure rollback cross a decision without losing the original pose.
    auto* Existing=W->SpawnActor<ACameraActor>();Existing->Tags.Add(TEXT("BranchLead"));Existing->SetActorLocation(FVector(777,10,20));const FTransform OriginalPose=Existing->GetActorTransform();
    Runner->Director=BranchRuntimeFixture();Runner->Director->Steps[1].Type=EDirectorNodeType::BindNPC;Runner->Director->Steps[1].ActorSource=EDirectorActorSource::Tag;Runner->Director->Steps[1].ActorTag=TEXT("BranchLead");
    Runner->Director->Steps[8].Type=EDirectorNodeType::BindNPC;Runner->Director->Steps[8].ActorSource=EDirectorActorSource::Tag;Runner->Director->Steps[8].ActorTag=TEXT("MissingBranchActor");
    TestTrue(TEXT("Missing runtime-only binding compiles structurally"),FSceneDirectorCompiler::Compile(*Runner->Director,Error));
    TestTrue(TEXT("Binding session starts"),Runner->PlayDirector());Runner->Tick(1);TestEqual(TEXT("Uses real bound actor"),Runner->FindNPC(TEXT("Lead")),static_cast<AActor*>(Existing));
    Runner->SelectDialogueChoice(TEXT("Yes"));Runner->Tick(.01f);TestFalse(TEXT("Missing chosen actor stops safely"),Runner->IsDirectorPlaying());TestFalse(TEXT("Failure explains missing actor"),Runner->LastError.IsEmpty());
    TestTrue(TEXT("Bound actor survives and restores pose"),IsValid(Existing)&&Existing->GetActorTransform().Equals(OriginalPose));TestFalse(TEXT("Failure restores input"),PC->IsMoveInputIgnored());TestEqual(TEXT("Failure restores camera"),PC->GetViewTarget(),static_cast<AActor*>(OriginalCamera));
    Cleanup();return true;
}
#endif
