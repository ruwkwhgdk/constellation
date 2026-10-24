#include "PhoneMenuWidget.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Text/STextBlock.h"
#include "Styling/CoreStyle.h"

TSharedRef<SWidget> UPhoneMenuWidget::RebuildWidget()
{
 SetIsFocusable(true);Buttons.Reset();
 auto Grid=SNew(SUniformGridPanel).SlotPadding(8);
 for(int32 I=0;I<6;++I)
 {
  TSharedPtr<SButton> Button;
  Grid->AddSlot(I%2,I/2)
  [
   SAssignNew(Button,SButton).ContentPadding(FMargin(14,24))
   .OnClicked_Lambda([this,I](){SelectEntry(I);return FReply::Handled();})
   [SNew(STextBlock).Text(FText::FromString(FString::Printf(TEXT("메뉴 %02d"),I+1)))
    .Font(FCoreStyle::GetDefaultFontStyle("Regular",20)).Justification(ETextJustify::Center)]
  ];
  Buttons.Add(Button);
 }
 return SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("NoBrush")).Padding(0)
 .OnMouseButtonDown_Lambda([](const FGeometry&,const FPointerEvent&){return FReply::Handled();})
 .OnMouseButtonUp_Lambda([](const FGeometry&,const FPointerEvent&){return FReply::Handled();})
 [
  SNew(SHorizontalBox)
  +SHorizontalBox::Slot().FillWidth(.55f)[SNew(SBox)]
  +SHorizontalBox::Slot().FillWidth(.45f).Padding(14)
  [
   SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
   .BorderBackgroundColor(FLinearColor(.025f,.035f,.055f,.94f)).Padding(22)
   [
    SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight().Padding(0,8)[SNew(STextBlock).Text(FText::FromString(TEXT("핸드폰"))).Font(FCoreStyle::GetDefaultFontStyle("Bold",30))]
    +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,20)[SNew(STextBlock).Text(FText::FromString(TEXT("임시 메뉴")))]
    +SVerticalBox::Slot().AutoHeight()[Grid]
    +SVerticalBox::Slot().AutoHeight().Padding(8,20)[SAssignNew(Status,STextBlock).AutoWrapText(true).Text(FText::FromString(TEXT("메뉴를 선택해 주세요")))]
    +SVerticalBox::Slot().FillHeight(1)[SNew(SBox)]
    +SVerticalBox::Slot().AutoHeight()
    [SNew(SButton).ContentPadding(16).OnClicked_Lambda([this](){OnClose.ExecuteIfBound();return FReply::Handled();})
     [SNew(STextBlock).Text(FText::FromString(TEXT("닫기  ·  Esc / `"))).Justification(ETextJustify::Center)]]
   ]
  ]
 ];
}
void UPhoneMenuWidget::FocusFirst()
{if(Buttons.Num()&&FSlateApplication::IsInitialized())FSlateApplication::Get().SetKeyboardFocus(Buttons[0],EFocusCause::SetDirectly);}
void UPhoneMenuWidget::SelectEntry(int32 I)
{if(Status&&I>=0&&I<6)Status->SetText(FText::FromString(FString::Printf(TEXT("메뉴 %02d 선택됨 — 기능 준비 중"),I+1)));}
FReply UPhoneMenuWidget::NativeOnKeyDown(const FGeometry& Geometry,const FKeyEvent& E)
{
 if(E.GetKey()==EKeys::Escape||E.GetKey()==EKeys::Tilde)
 {if(!E.IsRepeat())OnClose.ExecuteIfBound();return FReply::Handled();}
 return Super::NativeOnKeyDown(Geometry,E);
}
