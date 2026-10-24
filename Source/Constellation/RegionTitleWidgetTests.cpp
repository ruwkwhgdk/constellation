#if WITH_DEV_AUTOMATION_TESTS
#include "RegionTitleWidget.h"
#include "TutorialPromptTestTypes.h"
#include "Misc/AutomationTest.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRegionTitleLifecycleTest,"Constellation.RegionTitle.Lifecycle",
 EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRegionTitleLifecycleTest::RunTest(const FString&)
{
 UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
 if(!TestNotNull(TEXT("Region title test world"),World))return false;
 auto* PC=World->SpawnActor<ATutorialPromptTestController>();
 if(!TestNotNull(TEXT("Region title controller"),PC)){World->DestroyWorld(false);return false;}
 auto* Player=NewObject<ULocalPlayer>(GEngine);Player->PlayerController=PC;PC->Player=Player;World->AddController(PC);
 PC->bShowMouseCursor=true;
 auto MakeWidget=[World,PC]()
 {
  auto* Widget=NewObject<URegionTitleWidget>(World);Widget->SetOwningPlayer(PC);return Widget;
 };
 auto* First=MakeWidget();
 First->SetRegionText(FText::FromString(TEXT("<RegionTitle_Name>폐교</>")),FText::FromString(TEXT("<RegionTitle_Desc>텅 빈 교실</>")));
 TestEqual(TEXT("Known title RichText wrapper removed"),First->GetRegionTitleText().ToString(),FString(TEXT("폐교")));
 TestEqual(TEXT("Known subtitle RichText wrapper removed"),First->GetRegionSubtitleText().ToString(),FString(TEXT("텅 빈 교실")));
 First->SetRegionText(FText::FromString(TEXT("<Other>Literal</>")),FText::GetEmpty());
 TestEqual(TEXT("Unrelated markup not rewritten"),First->GetRegionTitleText().ToString(),FString(TEXT("<Other>Literal</>")));
 TestTrue(TEXT("Empty subtitle stays empty"),First->GetRegionSubtitleText().IsEmpty());
 First->NativeConstruct();
 TestFalse(TEXT("Region overlay cannot take focus"),First->IsFocusable());
 TestEqual(TEXT("Region overlay ignores hit tests"),First->GetVisibility(),ESlateVisibility::HitTestInvisible);
 TestFalse(TEXT("Region key event is unhandled"),First->NativeOnKeyDown(FGeometry(),FKeyEvent(EKeys::W,FModifierKeysState(),0,false,0,0)).IsEventHandled());
 TestFalse(TEXT("Region pointer event is unhandled"),First->NativeOnMouseButtonDown(FGeometry(),FPointerEvent()).IsEventHandled());
 TestEqual(TEXT("Stars start invisible"),First->GetStarsOpacity(),0.f);
 First->AdvancePresentation(.2f);
 TestTrue(TEXT("Stars reveal before text"),FMath::IsNearlyEqual(First->GetStarsOpacity(),.5f,1.e-4f)&&First->GetTextOpacity()==0.f);
 First->AdvancePresentation(.2f);TestEqual(TEXT("Stars fully visible at 0.4 seconds"),First->GetStarsOpacity(),1.f);
 First->AdvancePresentation(.25f);TestTrue(TEXT("Text fades in from 0.4 to 0.9 seconds"),FMath::IsNearlyEqual(First->GetTextOpacity(),.5f,1.e-4f));
 First->AdvancePresentation(.25f);TestTrue(TEXT("Text fully visible at 0.9 seconds"),FMath::IsNearlyEqual(First->GetTextOpacity(),1.f,1.e-4f));
 First->AdvancePresentation(2.3f);TestTrue(TEXT("Presentation holds through 3.2 seconds"),FMath::IsNearlyEqual(First->GetTextOpacity(),1.f,1.e-4f));
 First->AdvancePresentation(.4f);TestTrue(TEXT("All layers fade together"),FMath::IsNearlyEqual(First->GetTextOpacity(),.5f,1.e-4f)&&FMath::IsNearlyEqual(First->GetStarsOpacity(),.5f,1.e-4f));
 First->AdvancePresentation(.41f);TestTrue(TEXT("Presentation ends at four seconds"),First->IsPresentationFinished());
 TestFalse(TEXT("Finished presentation has no timer"),World->GetTimerManager().IsTimerActive(First->PresentationTimer));
 First->NativeConstruct();First->AdvancePresentation(1.f);
 auto* Second=MakeWidget();Second->NativeConstruct();
 TestTrue(TEXT("Latest region replaces earlier region for same player"),First->IsPresentationFinished());
 First->AdvancePresentation(20);First->NativeDestruct();
 TestFalse(TEXT("Earlier instance cannot finish replacement"),Second->IsPresentationFinished());
 TestTrue(TEXT("Replacement retains its own timer"),World->GetTimerManager().IsTimerActive(Second->PresentationTimer));
 Second->NativeDestruct();Second->AdvancePresentation(20);
 TestFalse(TEXT("External removal cancels timer"),World->GetTimerManager().IsTimerActive(Second->PresentationTimer));
 Second->NativeConstruct();TestEqual(TEXT("Re-added instance restarts timeline"),Second->GetStarsOpacity(),0.f);
 Second->NativeDestruct();
 TestEqual(TEXT("No region lifecycle changes input mode"),PC->InputModeCalls,0);
 TestTrue(TEXT("No region lifecycle changes cursor"),PC->bShowMouseCursor!=0);
 World->DestroyWorld(false);return true;
}
#endif
