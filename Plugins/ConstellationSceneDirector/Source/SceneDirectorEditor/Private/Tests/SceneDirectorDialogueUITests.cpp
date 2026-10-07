#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorPlayer.h"
#include "SDirectorDialogue.h"
#include "Engine/Texture2D.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SWindow.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SBoxPanel.h"
#include "Styling/CoreStyle.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Tests/AutomationCommon.h"
static TSharedPtr<SWindow> DialogueReviewWindow;
static TSharedPtr<SDirectorDialogue> DialoguePreviewWidget;
static bool bKoreanDialogue=false;
DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(FDialogueUICapture,FAutomationTestBase*,Test,FString,Name);
bool FDialogueUICapture::Update()
{
    TArray<FColor> Pixels;FIntVector Size;
    if(Test->TestTrue(TEXT("Dialogue UI capture"),FSlateApplication::Get().TakeScreenshot(DialogueReviewWindow.ToSharedRef(),Pixels,Size)))
    {
        TArray64<uint8> PNG;FImageUtils::PNGCompressImageArray(Size.X,Size.Y,Pixels,PNG);
        Test->TestTrue(TEXT("Save dialogue UI"),FFileHelper::SaveArrayToFile(PNG,*(FPaths::ProjectSavedDir()/Name)));
    }
    if(Name.EndsWith(TEXT("raised.png"))) bKoreanDialogue=true;
    if(Name.EndsWith(TEXT("korean.png")) && FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorChoiceCapture")))DialoguePreviewWidget->MoveChoice(1);
    else if(Name.EndsWith(TEXT("korean.png"))||Name.EndsWith(TEXT("choices-focus.png")))
    {DialogueReviewWindow->RequestDestroyWindow();DialogueReviewWindow.Reset();DialoguePreviewWidget.Reset();}
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorDialogueUITest,"Constellation.SceneDirector.DialogueUI",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorDialogueUITest::RunTest(const FString&)
{
    const auto* Defaults=GetDefault<ASceneDirectorPlayer>();
    if(!TestNotNull(TEXT("Background is a hard referenced asset"),Defaults->DialogueBackground.Get())||!TestNotNull(TEXT("Continue is a hard referenced asset"),Defaults->DialogueContinue.Get()))return false;
    if(!TestNotNull(TEXT("Speaker background hard reference"),Defaults->DialogueSpeakerBackground.Get()))return false;
    TestEqual(TEXT("Speaker UI texture group"),Defaults->DialogueSpeakerBackground->LODGroup,TEXTUREGROUP_UI);
    TestEqual(TEXT("UI texture group"),Defaults->DialogueBackground->LODGroup,TEXTUREGROUP_UI);
    TestEqual(TEXT("Continue texture group"),Defaults->DialogueContinue->LODGroup,TEXTUREGROUP_UI);
    auto Empty=SNew(SDirectorDialogue).Background(Defaults->DialogueBackground).Continue(Defaults->DialogueContinue).SpeakerBackground(Defaults->DialogueSpeakerBackground).Dialogue(FText::GetEmpty()).Waiting(false);
    Empty->SlatePrepass();
    TestTrue(TEXT("No empty dialogue panel"),Empty->GetVisibility()==EVisibility::Collapsed);
    if(!FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorDialogueCapture")))return true;
    bKoreanDialogue=false;
    TArray<FDirectorChoice> ReviewChoices;
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorChoiceCapture")))
    {
        for(const TCHAR* Label:{TEXT("First Option"),TEXT("Second Option"),TEXT("Third Option"),TEXT("Cancel Option")})
        {FDirectorChoice C;C.Text=FText::FromString(Label);ReviewChoices.Add(C);}
    }
    DialogueReviewWindow=SNew(SWindow).Title(FText::FromString(TEXT("Dialogue UI Review"))).ClientSize(FVector2D(1060,800)).SizingRule(ESizingRule::FixedSize)
    [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(.75f,.73f,.67f)).Padding(35)
     [SAssignNew(DialoguePreviewWidget,SDirectorDialogue).Background(Defaults->DialogueBackground).Continue(Defaults->DialogueContinue).SpeakerBackground(Defaults->DialogueSpeakerBackground)
      .ChoiceStyle(Defaults->DialogueChoiceStyle)
      .Choices_Lambda([ReviewChoices]{auto Result=ReviewChoices;if(bKoreanDialogue&&!Result.IsEmpty())
       {Result[0].Text=FText::FromString(TEXT("함께 가자."));Result[1].Text=FText::FromString(TEXT("이곳에서 무슨 일이 있었는지 자세하게 이야기해 줄래?"));Result[2].Text=FText::FromString(TEXT("다른 길을 찾아보자."));Result[3].Text=FText::FromString(TEXT("다음에 다시 이야기하자."));}return Result;})
      .ChoicePrompt(FGuid::NewGuid())
      .Position_Lambda([]{return FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorRefactorCapture"))&&bKoreanDialogue?EDirectorDialoguePosition::Center:EDirectorDialoguePosition::Bottom;})
      .Speaker_Lambda([]{if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorRefactorCapture")))return FText::GetEmpty();return FText::FromString(bKoreanDialogue?TEXT("여행자"):TEXT("Cree"));})
      .Dialogue_Lambda([]{if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorRefactorCapture")))return FText::FromString(bKoreanDialogue?TEXT("진행 상황이 저장되고 플레이어의 HP가 전부 회복되었습니다."):TEXT("낯익은 얼굴을 하고 있는 석상이 보인다."));return FText::FromString(bKoreanDialogue?
        TEXT("이 <teal>오래된 열쇠</>로 문을 열 수 있을 것 같아.\n먼저 <red>계단 아래</>를 살펴보자."):
        TEXT("If I give you this <teal>goat butter</>, will you make some <teal>salmon meunière</> for Genli? She should be in the <red>kitchen</>."));}).Waiting(true)]];
    FSlateApplication::Get().AddWindow(DialogueReviewWindow.ToSharedRef());
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(.5f));
    ADD_LATENT_AUTOMATION_COMMAND(FDialogueUICapture(this,TEXT("SceneDirector-dialogue.png")));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(.45f));
    ADD_LATENT_AUTOMATION_COMMAND(FDialogueUICapture(this,TEXT("SceneDirector-dialogue-raised.png")));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(.2f));
    ADD_LATENT_AUTOMATION_COMMAND(FDialogueUICapture(this,TEXT("SceneDirector-dialogue-korean.png")));
    if(FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorChoiceCapture")))
    {
        ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(.2f));
        ADD_LATENT_AUTOMATION_COMMAND(FDialogueUICapture(this,TEXT("SceneDirector-choices-focus.png")));
    }
    return true;
}
#endif
