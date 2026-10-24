#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorPlayer.h"
#include "SDirectorDialogue.h"
#include "StardustChoiceWidget.h"
#include "Components/Button.h"
#include "Engine/Texture2D.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SWindow.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SBoxPanel.h"
#include "Styling/CoreStyle.h"
#include "ImageUtils.h"
#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/RichTextBlock.h"
#include "Components/Image.h"
#include "UObject/StrongObjectPtr.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Tests/AutomationCommon.h"
static TSharedPtr<SWindow> DialogueReviewWindow;
static TSharedPtr<SDirectorDialogue> DialoguePreviewWidget;
static bool bKoreanDialogue=false;
static TStrongObjectPtr<UUserWidget> LegacyDialogueReview;
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorDialogueFirstChoiceLayoutTest,"Constellation.SceneDirector.DialogueFirstChoiceLayout",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorDialogueFirstChoiceLayoutTest::RunTest(const FString&)
{
    TArray<FDirectorChoice> Choices;
    auto Dialogue=SNew(SDirectorDialogue).Background(nullptr).Continue(nullptr).SpeakerBackground(nullptr).Dialogue(FText::FromString(TEXT("…")))
        .Choices_Lambda([&Choices]{return Choices;}).ChoicePrompt(FGuid::NewGuid()).Waiting(true);
    Dialogue->SlatePrepass();
    const float EmptyHeight=Dialogue->GetDesiredSize().Y;
    FDirectorChoice Choice;Choice.Key=TEXT("Inspect");Choice.Text=FText::FromString(TEXT("Inspect the locker"));Choices.Add(Choice);
    // Choices become available at the click-wait boundary. Their rows must be measured
    // before the first paint, without depending on a widget Tick after the prepass.
    Dialogue->SlatePrepass();
    const float FirstChoiceHeight=Dialogue->GetDesiredSize().Y;
    TestTrue(TEXT("First choice prepass includes the new rows"),FirstChoiceHeight>EmptyHeight+40.f);
    Dialogue->SlatePrepass();
    TestEqual(TEXT("Choice panel height is stable on its first visible frame"),Dialogue->GetDesiredSize().Y,FirstChoiceHeight);
    return true;
}
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
    {DialogueReviewWindow->RequestDestroyWindow();DialogueReviewWindow.Reset();DialoguePreviewWidget.Reset();LegacyDialogueReview.Reset();}
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
    if(FParse::Param(FCommandLine::Get(),TEXT("LegacyDialogueCapture")))
    {
        UClass* Class=LoadClass<UUserWidget>(nullptr,TEXT("/Game/Constellation/UI/Widgets/WBP_Dialogue.WBP_Dialogue_C"));
        if(!TestNotNull(TEXT("Legacy widget class"),Class))return false;
        LegacyDialogueReview.Reset(NewObject<UUserWidget>(GetTransientPackage(),Class));LegacyDialogueReview->Initialize();
        DialogueReviewWindow->SetContent(LegacyDialogueReview->TakeWidget());
        auto* Name=Cast<URichTextBlock>(LegacyDialogueReview->WidgetTree->FindWidget(TEXT("Name")));
        auto* Body=Cast<URichTextBlock>(LegacyDialogueReview->WidgetTree->FindWidget(TEXT("Description")));
        auto* Background=Cast<UImage>(LegacyDialogueReview->WidgetTree->FindWidget(TEXT("Background")));
        TestTrue(TEXT("Legacy atlas brush UV serialized"),Background&&FBox2f(Background->GetBrush().GetUVRegion()).bIsValid);
        if(Name)Name->SetText(FText::FromString(TEXT("<Name>이름</>")));
        if(Body)Body->SetText(FText::FromString(TEXT("세상에서 살아남기 위해선,\n그 세상에 맞는 모습으로 자신을 변화시킬 필요가 있다.")));
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("LegacyChoiceCapture")))
    {
        UClass* Class=LoadClass<UUserWidget>(nullptr,TEXT("/Game/Constellation/UI/Widgets/WBP_Choice.WBP_Choice_C"));
        if(!TestTrue(TEXT("Legacy choices use the Stardust skin"),Class&&Class->IsChildOf(UStardustChoiceWidget::StaticClass())))return false;
        LegacyDialogueReview.Reset(NewObject<UUserWidget>(GetTransientPackage(),Class));LegacyDialogueReview->Initialize();
        DialogueReviewWindow->SetContent(LegacyDialogueReview->TakeWidget());
        const TCHAR* Labels[]={TEXT("함께 가자."),TEXT("이곳에서 무슨 일이 있었는지 자세하게 이야기해 줄래?"),TEXT("다른 길을 찾아보자.")};
        for(int32 I=0;I<3;++I)
        {
            auto* Text=Cast<URichTextBlock>(LegacyDialogueReview->WidgetTree->FindWidget(FName(*FString::Printf(TEXT("Choice_Text_%c"),'A'+I))));
            TestNotNull(TEXT("Original choice text retained"),Text);if(Text)Text->SetText(FText::FromString(Labels[I]));
            auto* Button=Cast<UButton>(LegacyDialogueReview->WidgetTree->FindWidget(FName(*FString::Printf(TEXT("Choice_Button_%c"),'A'+I))));
            TestNotNull(TEXT("Original choice button retained"),Button);
            if(Button){Button->SetVisibility(ESlateVisibility::Visible);TestTrue(TEXT("Original choice callback retained"),Button->OnClicked.IsBound());}
        }
    }
    if(auto* Skin=Cast<UStardustChoiceWidget>(LegacyDialogueReview.Get()))Skin->RefreshChoiceVisuals();
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
