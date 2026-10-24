#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SDirectorChoices.h"
#include "SceneDirectorPlayer.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SWindow.h"
#include "Widgets/Layout/SBorder.h"
#include "Styling/CoreStyle.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Tests/AutomationCommon.h"

static TArray<FDirectorChoice> LockedReviewChoices()
{
    TArray<FDirectorChoice> Choices;
    FDirectorChoice C;C.Key=TEXT("Inspect");C.Text=FText::FromString(TEXT("주변을 살펴본다."));Choices.Add(C);
    C.Key=TEXT("Force");C.Text=FText::FromString(TEXT("문을 연다. (필요 스탯 : 힘 1)"));C.bEnabled=false;C.DisabledReason=FText::FromString(TEXT("힘이 부족합니다."));Choices.Add(C);
    C.Key=TEXT("Leave");C.Text=FText::FromString(TEXT("다른 길을 찾아본다."));C.bEnabled=true;C.DisabledReason=FText::GetEmpty();Choices.Add(C);
    return Choices;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorLockedChoiceTest,"Constellation.SceneDirector.LockedChoiceState",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorLockedChoiceTest::RunTest(const FString&)
{
    auto Choices=LockedReviewChoices();FGuid Prompt=FGuid::NewGuid();int32 Calls=0;
    auto W=SNew(SDirectorChoices).Style(GetDefault<ASceneDirectorPlayer>()->DialogueChoiceStyle).Options_Lambda([&]{return Choices;}).PromptId_Lambda([&]{return Prompt;}).CanChoose(true).OnChosen_Lambda([&](FName){++Calls;});
    TestFalse(TEXT("Locked click rejected"),W->Choose(1));
    W->MoveFocus(1);TestEqual(TEXT("Keyboard skips locked row"),W->GetFocusedIndex(),2);
    Choices[1].bEnabled=true;W->Refresh();
    TestEqual(TEXT("Unlock preserves current focus"),W->GetFocusedIndex(),2);
    TestEqual(TEXT("Unlock starts at zero"),W->GetUnlockProgress(TEXT("Force")),0.f);
    W->Tick(FGeometry(),0,.45f);TestEqual(TEXT("Unlock midpoint"),W->GetUnlockProgress(TEXT("Force")),.5f);
    Choices[1].Text=FText::FromString(TEXT("문을 연다. (필요 스탯 : 힘 1) "));W->Refresh();
    TestEqual(TEXT("Label refresh does not replay"),W->GetUnlockProgress(TEXT("Force")),.5f);
    W->Tick(FGeometry(),0,.45f);TestEqual(TEXT("Unlock completes in 0.9 seconds"),W->GetUnlockProgress(TEXT("Force")),1.f);
    Choices[1].bEnabled=false;W->Refresh();TestFalse(TEXT("Relock immediately rejects click"),W->Choose(1));
    Choices[1].bEnabled=true;W->Refresh();TestEqual(TEXT("Later unlock animates once again"),W->GetUnlockProgress(TEXT("Force")),0.f);
    TestTrue(TEXT("Unlocked row commits"),W->Choose(1));
    Choices[0].Text=FText::FromString(TEXT("둘러본다."));W->Refresh();
    TestTrue(TEXT("Same prompt changes retain committed guard"),W->IsCommitted());TestFalse(TEXT("No second commit"),W->Confirm());TestEqual(TEXT("One callback"),Calls,1);
    Prompt=FGuid::NewGuid();W->Refresh();TestFalse(TEXT("New prompt resets guard"),W->IsCommitted());
    TestEqual(TEXT("Initially enabled never animates"),W->GetUnlockProgress(TEXT("Force")),1.f);
    return true;
}
static TSharedPtr<SWindow> LockedCaptureWindow;
static TSharedPtr<SDirectorChoices> LockedCaptureWidget;
static TArray<FDirectorChoice> LockedCaptureChoices;
DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(FDirectorLockedCapture,FAutomationTestBase*,Test,int32,Stage);
bool FDirectorLockedCapture::Update()
{
    TArray<FColor> Pixels;FIntVector Size;
    if(Test->TestTrue(TEXT("Capture locked choices"),FSlateApplication::Get().TakeScreenshot(LockedCaptureWindow.ToSharedRef(),Pixels,Size)))
    {
        TArray64<uint8> PNG;FImageUtils::PNGCompressImageArray(Size.X,Size.Y,Pixels,PNG);
        const TCHAR* Name=Stage==0?TEXT("SceneDirector-choices-locked.png"):Stage==1?TEXT("SceneDirector-choices-unlocking.png"):TEXT("SceneDirector-choices-unlocked.png");
        Test->TestTrue(TEXT("Save locked choice capture"),FFileHelper::SaveArrayToFile(PNG,*(FPaths::ProjectSavedDir()/Name)));
    }
    if(Stage==0){LockedCaptureChoices[1].bEnabled=true;LockedCaptureWidget->Refresh();}
    if(Stage==2){LockedCaptureWindow->RequestDestroyWindow();LockedCaptureWindow.Reset();LockedCaptureWidget.Reset();LockedCaptureChoices.Reset();}
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorLockedChoiceCaptureTest,"Constellation.SceneDirector.LockedChoiceCapture",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorLockedChoiceCaptureTest::RunTest(const FString&)
{
    if(!FParse::Param(FCommandLine::Get(),TEXT("SceneDirectorLockedChoiceCapture")))return true;
    LockedCaptureChoices=LockedReviewChoices();
    LockedCaptureWindow=SNew(SWindow).Title(FText::FromString(TEXT("Locked Choice Review"))).ClientSize(FVector2D(660,400)).SizingRule(ESizingRule::FixedSize)
    [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(.035f,.05f,.075f)).Padding(40).HAlign(HAlign_Center).VAlign(VAlign_Center)
     [SAssignNew(LockedCaptureWidget,SDirectorChoices).Style(GetDefault<ASceneDirectorPlayer>()->DialogueChoiceStyle).Options_Lambda([]{return LockedCaptureChoices;}).PromptId(FGuid::NewGuid()).CanChoose(true)]];
    FSlateApplication::Get().AddWindow(LockedCaptureWindow.ToSharedRef());
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(.5f));
    ADD_LATENT_AUTOMATION_COMMAND(FDirectorLockedCapture(this,0));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(.35f));
    ADD_LATENT_AUTOMATION_COMMAND(FDirectorLockedCapture(this,1));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(.65f));
    ADD_LATENT_AUTOMATION_COMMAND(FDirectorLockedCapture(this,2));
    return true;
}
#endif
