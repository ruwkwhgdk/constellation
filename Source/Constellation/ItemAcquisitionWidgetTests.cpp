#if WITH_DEV_AUTOMATION_TESTS
#include "ItemAcquisitionWidget.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Widgets/Text/STextBlock.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FItemAcquisitionSpriteFitTest,"Constellation.ItemAcquisition.SpriteFit",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FItemAcquisitionSpriteFitTest::RunTest(const FString&)
{
 for(const FVector2D Image : {FVector2D(80,1600),FVector2D(1800,90),FVector2D(64,64)})
 for(const float Scale : {.1f,.6f,1.f,4.f})
 {
  const FSlateRect R=UItemAcquisitionWidget::FitSprite(Image,FVector2D(300,224),Scale,FVector2D(10000,-10000));
  TestTrue(TEXT("Even extreme offsets leave complete sprite visible"),R.Left>=0 && R.Top>=0 && R.Right<=300.001 && R.Bottom<=224.001);
  TestTrue(TEXT("Sword/key/square preserve source aspect"),FMath::IsNearlyEqual((R.Right-R.Left)/(R.Bottom-R.Top),Image.X/Image.Y,.001));
 }
 TestEqual(TEXT("Missing image has no drawable rectangle"),UItemAcquisitionWidget::FitSprite(FVector2D(0,0),FVector2D(300,224),1,FVector2D::ZeroVector).Right,0.f);
 return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FItemAcquisitionTextLayoutTest,"Constellation.ItemAcquisition.TextLayout",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FItemAcquisitionTextLayoutTest::RunTest(const FString&)
{
 // CreateWidget performs UUserWidget::Initialize and creates its WidgetTree.
 // Bare NewObject crashes UUserWidget::OnWidgetRebuilt when TakeWidget runs.
 UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
 if(!TestNotNull(TEXT("Layout fixture world"),World))return false;
 ON_SCOPE_EXIT { World->DestroyWorld(false); };
 auto* Widget=CreateWidget<UItemAcquisitionWidget>(World);
 if(!TestNotNull(TEXT("Initialized layout fixture widget"),Widget))return false;
 FItemAcquisitionPresentation P;
 P.Name=FText::FromString(TEXT("시험 열쇠"));
 FString LongText;
 for(int32 N=0;N<40;++N) LongText+=TEXT("오래된 교실에서 발견한 열쇠에는 희미한 별빛이 남아 있다. ");
 P.Description=FText::FromString(LongText);
 Widget->SetPresentation(P,EKeys::Enter);
 const TSharedRef<SWidget> Root=Widget->TakeWidget();
 Root->SlatePrepass(1.f);
 bool bFoundBody=false,bFoundScroll=false;
 TFunction<void(const TSharedRef<SWidget>&)> Visit=[&](const TSharedRef<SWidget>& Node)
 {
  if(Node->GetTypeAsString()==TEXT("SScrollBox")) bFoundScroll=true;
  if(Node->GetTypeAsString()==TEXT("STextBlock"))
  {
   const auto Text=StaticCastSharedRef<STextBlock>(Node);
   if(Text->GetText().EqualTo(P.Description))
   {
    bFoundBody=true;
    // Compact 1028px card: 553px text column minus its scrollbar and padding.
    AddInfo(FString::Printf(TEXT("Description desired size: %.2f × %.2f; available content width: 541"),Text->GetDesiredSize().X,Text->GetDesiredSize().Y));
    TestTrue(TEXT("Long Korean description fits actual scroll content width"),Text->GetDesiredSize().X<=541);
    TestTrue(TEXT("Long description retains lines beyond visible scroll region"),Text->GetDesiredSize().Y>340);
   }
  }
  FChildren* Children=Node->GetChildren();
  for(int32 N=0;N<Children->Num();++N) Visit(Children->GetChildAt(N));
 };
 Visit(Root);
 TestTrue(TEXT("Payload text remains intact"),bFoundBody);
 TestTrue(TEXT("Extreme text has a scroll container"),bFoundScroll);
 return true;
}
#endif
