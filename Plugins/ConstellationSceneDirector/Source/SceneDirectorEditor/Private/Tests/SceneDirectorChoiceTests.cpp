#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorChoice.h"
#include "SDirectorChoices.h"
#include "Widgets/Input/SButton.h"
#include "SceneDirectorPlayer.h"
#include "SceneDirectorCompiler.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/Texture2D.h"
#include "Camera/CameraActor.h"
static TArray<FDirectorChoice> MakeChoices()
{
    TArray<FDirectorChoice> Result;
    for(int32 I=0;I<4;++I){FDirectorChoice C;C.Key=FName(*FString::Printf(TEXT("Option_%d"),I));C.Text=FText::FromString(FString::Printf(TEXT("선택지 %d"),I+1));Result.Add(C);}return Result;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorChoicesTest,"Constellation.SceneDirector.ChoiceValidationAndInput",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorChoicesTest::RunTest(const FString&)
{
    FString Error;auto Choices=MakeChoices();TestTrue(TEXT("Four choices accepted"),DirectorChoices::Validate(Choices,Error));
    Choices.Add(FDirectorChoice());TestFalse(TEXT("Fifth rejected"),DirectorChoices::Validate(Choices,Error));Choices.Pop();
    Choices[3].Key=Choices[0].Key;TestFalse(TEXT("Duplicate result key rejected"),DirectorChoices::Validate(Choices,Error));Choices=MakeChoices();
    Choices[2].Text=FText::FromString(TEXT(" \n "));TestFalse(TEXT("Blank option rejected"),DirectorChoices::Validate(Choices,Error));
    Choices=MakeChoices();Choices.SetNum(1);TestTrue(TEXT("One choice allowed"),DirectorChoices::Validate(Choices,Error));
    Choices.Reset();TestTrue(TEXT("Zero is ordinary dialogue"),DirectorChoices::Validate(Choices,Error));Choices=MakeChoices();
    const auto* Defaults=GetDefault<ASceneDirectorPlayer>();const auto& Style=Defaults->DialogueChoiceStyle;
    for(UTexture2D* T:{Style.FocusedBG.Get(),Style.FocusedStroke.Get(),Style.IdleBG.Get(),Style.IdleStroke.Get(),Style.Cursor.Get(),Style.LockedAtlas.Get()})
    {if(!TestNotNull(TEXT("Choice texture hard reference"),T))return false;TestEqual(TEXT("Choice UI group"),T->LODGroup,TEXTUREGROUP_UI);}
    int32 Calls=0;FName Chosen;FGuid Prompt=FGuid::NewGuid();bool Ready=false;
    auto Widget=SNew(SDirectorChoices).Style(Style).Options_Lambda([&]{return Choices;}).PromptId_Lambda([&]{return Prompt;}).CanChoose_Lambda([&]{return Ready;})
        .OnChosen_Lambda([&](FName Key){++Calls;Chosen=Key;});
    TestFalse(TEXT("Cannot select before ready"),Widget->Confirm());Ready=true;
    Widget->MoveFocus(-1);TestEqual(TEXT("Up wraps to fourth"),Widget->GetFocusedIndex(),3);
    Widget->MoveFocus(1);TestEqual(TEXT("Down wraps to first"),Widget->GetFocusedIndex(),0);
    TArray<TSharedRef<SWidget>> ChoiceButtons;
    TFunction<void(TSharedRef<SWidget>)> FindButtons=[&](TSharedRef<SWidget> Node)
    {if(Node->GetType()==FName(TEXT("SButton")))ChoiceButtons.Add(Node);auto* Children=Node->GetChildren();for(int32 I=0;I<Children->Num();++I)FindButtons(Children->GetChildAt(I));};
    FindButtons(Widget);
    TestEqual(TEXT("One hover target per choice"),ChoiceButtons.Num(),4);
    if(ChoiceButtons.Num()==4){ChoiceButtons[1]->OnMouseEnter(FGeometry(),FPointerEvent());TestEqual(TEXT("Mouse hover transfers active cursor and star"),Widget->GetFocusedIndex(),1);}
    TestFalse(TEXT("Invalid row rejected"),Widget->Choose(4));TestTrue(TEXT("Select third"),Widget->Choose(2));
    TestEqual(TEXT("Stable key delivered"),Chosen,Choices[2].Key);TestFalse(TEXT("Duplicate confirm ignored"),Widget->Confirm());TestEqual(TEXT("Only one callback"),Calls,1);
    Prompt=FGuid::NewGuid();Widget->Refresh();TestFalse(TEXT("Same options new prompt resets latch"),Widget->IsCommitted());
    Widget->MoveFocus(1);TestTrue(TEXT("Second prompt works"),Widget->Confirm());TestEqual(TEXT("Second prompt one result"),Calls,2);
    auto Preview=SNew(SDirectorChoices).Style(Style).Options(Choices).CanChoose(true);
    Preview->Choose(0);Preview->MoveFocus(1);
    TestEqual(TEXT("Preview remains interactive after click"),Preview->GetFocusedIndex(),1);
    TestFalse(TEXT("Preview does not latch a selection"),Preview->IsCommitted());
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorChoiceRuntimeTest,"Constellation.SceneDirector.ChoiceRuntime",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorChoiceRuntimeTest::RunTest(const FString&)
{
    UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());
    auto* Asset=NewObject<USceneDirectorAsset>();Asset->Steps.SetNum(4);
    Asset->Steps[0].Type=EDirectorNodeType::Start;
    Asset->Steps[1].Type=EDirectorNodeType::SpawnNPC;Asset->Steps[1].ActorClass=ACameraActor::StaticClass();
    Asset->Steps[2].Type=EDirectorNodeType::Dialogue;Asset->Steps[2].Duration=.1f;Asset->Steps[2].DialogueText=FText::FromString(TEXT("어떻게 할까?"));Asset->Steps[2].Choices=MakeChoices();
    Asset->Steps[3].Type=EDirectorNodeType::End;
    for(int32 I=0;I<3;++I)Asset->Steps[I].NextNodes={Asset->Steps[I+1].Id};
    FString Error;bool Compiled=FSceneDirectorCompiler::Compile(*Asset,Error);TestTrue(TEXT("Choice graph compiles"),Compiled);
    if(Compiled)
    {
        auto* Player=W->SpawnActor<ASceneDirectorPlayer>();Player->bAutoPlay=false;Player->Director=Asset;
        TestTrue(TEXT("Play choices"),Player->PlayDirector());TestFalse(TEXT("Early selection rejected"),Player->SelectDialogueChoice(TEXT("Option_0")));
        Player->Tick(5);TestTrue(TEXT("Timed dialogue with options waits"),Player->IsWaitingForChoice());
        Player->AdvanceDialogue();TestTrue(TEXT("Normal advance cannot skip choice"),Player->IsWaitingForChoice());
        TestFalse(TEXT("Unknown choice rejected"),Player->SelectDialogueChoice(TEXT("Unknown")));
        const FGuid Prompt=Player->ChoicePrompt;
        TestTrue(TEXT("Runtime relock"),Player->SetChoiceAvailability(TEXT("Option_2"),false,FText::FromString(TEXT("힘이 부족합니다."))));
        TestFalse(TEXT("Locked choice rejected by player"),Player->SelectDialogueChoice(TEXT("Option_2")));
        TestTrue(TEXT("Runtime unlock"),Player->SetChoiceAvailability(TEXT("Option_2"),true,FText::GetEmpty()));
        TestEqual(TEXT("Availability retains prompt identity"),Player->ChoicePrompt,Prompt);
        TestTrue(TEXT("Authored availability unchanged"),Asset->Steps[2].Choices[2].bEnabled);
        TestTrue(TEXT("Valid choice resumes"),Player->SelectDialogueChoice(TEXT("Option_2")));
        TestFalse(TEXT("Repeated result ignored"),Player->SelectDialogueChoice(TEXT("Option_2")));
        Player->Tick(.1f);TestFalse(TEXT("End reached after selection"),Player->IsDirectorPlaying());TestEqual(TEXT("Result retained"),Player->LastChoiceKey,FName(TEXT("Option_2")));
        TestTrue(TEXT("Replay"),Player->PlayDirector());TestTrue(TEXT("Replay clears result"),Player->LastChoiceKey.IsNone());Player->Tick(1);Player->StopDirector();TestTrue(TEXT("Stop clears options"),Player->CurrentChoices.IsEmpty());
    }
    GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorChoiceAvailabilityBranchTest,"Constellation.SceneDirector.ChoiceAvailabilityBranch",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorChoiceAvailabilityBranchTest::RunTest(const FString&)
{
    UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());
    auto* Asset=NewObject<USceneDirectorAsset>();Asset->Steps.SetNum(4);
    Asset->Steps[0].Type=EDirectorNodeType::Start;
    Asset->Steps[1].Type=EDirectorNodeType::SpawnNPC;Asset->Steps[1].ActorClass=ACameraActor::StaticClass();
    auto& Prompt=Asset->Steps[2];Prompt.Type=EDirectorNodeType::Dialogue;Prompt.Duration=.1f;Prompt.DialogueText=FText::FromString(TEXT("어떻게 할까?"));Prompt.Choices=MakeChoices();
    Prompt.Choices.SetNum(3);Prompt.Choices[1].bEnabled=false;Prompt.Choices[2].bEnabled=false;
    Asset->Steps[3].Type=EDirectorNodeType::End;
    Asset->Steps[0].NextNodes={Asset->Steps[1].Id};Asset->Steps[1].NextNodes={Prompt.Id};
    Prompt.ChoiceTargets.Add(Prompt.Choices[0].Key,Asset->Steps[3].Id);Prompt.ChoiceTargets.Add(Prompt.Choices[1].Key,Asset->Steps[3].Id);
    FString Error;const bool Compiled=FSceneDirectorCompiler::Compile(*Asset,Error);TestTrue(TEXT("Connected and unconnected locked choices compile"),Compiled);
    if(Compiled)
    {
        auto* Player=W->SpawnActor<ASceneDirectorPlayer>();Player->bAutoPlay=false;Player->Director=Asset;
        TestFalse(TEXT("Inactive prompt availability rejected"),Player->SetChoiceAvailability(TEXT("Option_1"),true,FText::GetEmpty()));
        TestTrue(TEXT("Play branching choice"),Player->PlayDirector());Player->Tick(5);
        TestFalse(TEXT("Last enabled choice cannot be locked"),Player->SetChoiceAvailability(TEXT("Option_0"),false,FText::GetEmpty()));
        TestFalse(TEXT("Cannot unlock missing branch destination"),Player->SetChoiceAvailability(TEXT("Option_2"),true,FText::GetEmpty()));
        TestTrue(TEXT("Connected branch unlocks"),Player->SetChoiceAvailability(TEXT("Option_1"),true,FText::GetEmpty()));
        TestFalse(TEXT("Authored locked state unchanged"),Asset->Steps[2].Choices[1].bEnabled);
        TestTrue(TEXT("Select newly unlocked branch"),Player->SelectDialogueChoice(TEXT("Option_1")));
        Player->Tick(.2f);TestTrue(TEXT("Branch replay accepts session availability"),Player->LastError.IsEmpty());
        TestEqual(TEXT("Unlocked branch result retained"),Player->LastChoiceKey,FName(TEXT("Option_1")));
        Player->StopDirector();TestTrue(TEXT("Replay initial state"),Player->PlayDirector());Player->Tick(5);
        TestFalse(TEXT("Replay restores authored lock"),Player->SelectDialogueChoice(TEXT("Option_1")));Player->StopDirector();
    }
    GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
#endif
