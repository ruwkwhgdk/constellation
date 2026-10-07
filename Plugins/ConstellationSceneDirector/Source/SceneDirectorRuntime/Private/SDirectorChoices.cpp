#include "SDirectorChoices.h"
#include "Engine/Texture2D.h"
#include "InputCoreTypes.h"
#include "Styling/CoreStyle.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
void SDirectorChoices::Construct(const FArguments& Args)
{
    Options=Args._Options;PromptId=Args._PromptId;CanChoose=Args._CanChoose;Chosen=Args._OnChosen;
    auto Brush=[](FSlateBrush& B,UTexture2D* T,FVector2D Size,FMargin Margin)
    {B.SetResourceObject(T);B.ImageSize=Size;B.DrawAs=ESlateBrushDrawType::Box;B.Margin=Margin;};
    Brush(FocusBG,Args._Style.FocusedBG,FVector2D(360,70),FMargin(.11f,.49f));
    Brush(IdleBG,Args._Style.IdleBG,FVector2D(360,70),FMargin(.11f,.49f));
    Brush(FocusStroke,Args._Style.FocusedStroke,FVector2D(376,86),FMargin(.13f,.49f));
    Brush(IdleStroke,Args._Style.IdleStroke,FVector2D(354,64),FMargin(.11f,.49f));
    Cursor.SetResourceObject(Args._Style.Cursor);Cursor.ImageSize=FVector2D(26,40);Cursor.DrawAs=ESlateBrushDrawType::Image;
    ButtonStyle=FButtonStyle().SetNormal(FSlateNoResource()).SetHovered(FSlateNoResource()).SetPressed(FSlateNoResource()).SetDisabled(FSlateNoResource());
    ChildSlot[SAssignNew(Rows,SVerticalBox)];Refresh();
}
void SDirectorChoices::Refresh()
{
    const auto New=Options.Get(TArray<FDirectorChoice>());const FGuid NewId=PromptId.Get(FGuid());
    bool Changed=!bInitialized||NewId!=CurrentPrompt||New.Num()!=Current.Num();
    if(!Changed)for(int32 I=0;I<New.Num();++I)if(New[I].Key!=Current[I].Key||!New[I].Text.EqualTo(Current[I].Text)||New[I].bEnabled!=Current[I].bEnabled||!New[I].DisabledReason.EqualTo(Current[I].DisabledReason)){Changed=true;break;}
    if(!Changed)return;
    bInitialized=true;CurrentPrompt=NewId;Current=New;FocusedIndex=0;bCommitted=false;
    FString Error;if(!DirectorChoices::Validate(Current,Error))Current.Reset();
    FocusedIndex=Current.IndexOfByPredicate([](const FDirectorChoice& C){return C.bEnabled;});
    Rebuild();
}
void SDirectorChoices::Rebuild()
{
    Rows->ClearChildren();
    for(int32 I=0;I<Current.Num();++I)
    {
        Rows->AddSlot().AutoHeight().Padding(0,0,0,0)
        [SNew(SBox).WidthOverride(402)
         [SNew(SOverlay)
          // BG has a 3px inset relative to the idle outline; focused glow adds 8px outside BG.
          +SOverlay::Slot().Padding(26,8,8,8)
          [SNew(SImage).Image_Lambda([this,I]{return FocusedIndex==I?&FocusBG:&IdleBG;})]
          +SOverlay::Slot().Padding(18,0,0,0)
          [SNew(SImage).Image(&FocusStroke).Visibility_Lambda([this,I]{return FocusedIndex==I?EVisibility::HitTestInvisible:EVisibility::Hidden;})]
          +SOverlay::Slot().Padding(29,11,11,11)
          [SNew(SImage).Image(&IdleStroke).Visibility_Lambda([this,I]{return FocusedIndex!=I?EVisibility::HitTestInvisible:EVisibility::Hidden;})]
          +SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Center).Padding(1,1,0,0)
          [SNew(SImage).Image(&Cursor).ColorAndOpacity(FLinearColor(0,0,0,.8f))
           .Visibility_Lambda([this,I]{return FocusedIndex==I?EVisibility::HitTestInvisible:EVisibility::Hidden;})]
          +SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Center)
          [SNew(SImage).Image(&Cursor).Visibility_Lambda([this,I]{return FocusedIndex==I?EVisibility::HitTestInvisible:EVisibility::Hidden;})]
          +SOverlay::Slot().Padding(26,8,8,8)
          [SNew(SButton).ButtonStyle(&ButtonStyle).IsFocusable(false).ContentPadding(FMargin(22,12)).HAlign(HAlign_Left).VAlign(VAlign_Center)
           .IsEnabled_Lambda([this,I]{return Current[I].bEnabled&&CanChoose.Get(false)&&!bCommitted;})
           .OnHovered_Lambda([this,I]{if(Current[I].bEnabled&&!bCommitted&&CanChoose.Get(false))FocusedIndex=I;})
           .OnClicked_Lambda([this,I]{Choose(I);return FReply::Handled();})
           [SNew(STextBlock).Text(Current[I].bEnabled||Current[I].DisabledReason.IsEmpty()?Current[I].Text:FText::Format(FText::FromString(TEXT("{0}\n{1}")),Current[I].Text,Current[I].DisabledReason)).Font(FCoreStyle::GetDefaultFontStyle("BoldItalic",16))
            .ColorAndOpacity(Current[I].bEnabled?FLinearColor(.88f,.85f,.76f):FLinearColor(.4f,.4f,.4f)).WrapTextAt(304)]]]];
    }
}
void SDirectorChoices::Tick(const FGeometry& G,double T,float D){SCompoundWidget::Tick(G,T,D);Refresh();}
void SDirectorChoices::MoveFocus(int32 Direction)
{
    Refresh();if(bCommitted||!CanChoose.Get(false)||Current.IsEmpty())return;
    for(int32 Count=0;Count<Current.Num();++Count){FocusedIndex=(FocusedIndex+(Direction<0?-1:1)+Current.Num())%Current.Num();if(Current[FocusedIndex].bEnabled)break;}
}
bool SDirectorChoices::Confirm(){return Choose(FocusedIndex);}
bool SDirectorChoices::Choose(int32 Index)
{
    Refresh();if(bCommitted||!CanChoose.Get(false)||!Current.IsValidIndex(Index)||!Current[Index].bEnabled)return false;
    FocusedIndex=Index;
    // Preview has no execution callback; keep it interactive after clicking.
    if(!Chosen.IsBound())return true;
    bCommitted=true;const FName Key=Current[Index].Key;
    Chosen.ExecuteIfBound(Key);return true;
}
FReply SDirectorChoices::OnKeyDown(const FGeometry&,const FKeyEvent& Event)
{
    if(Event.GetKey()==EKeys::Up){MoveFocus(-1);return FReply::Handled();}
    if(Event.GetKey()==EKeys::Down){MoveFocus(1);return FReply::Handled();}
    if(Event.GetKey()==EKeys::Enter){if(!Event.IsRepeat())Confirm();return FReply::Handled();}
    if(Event.GetKey()==EKeys::SpaceBar)return FReply::Handled();
    return FReply::Unhandled();
}
