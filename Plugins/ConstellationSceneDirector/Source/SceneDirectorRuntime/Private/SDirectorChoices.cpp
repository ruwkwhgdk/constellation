#include "SDirectorChoices.h"
#include "ChoiceStardustStyle.h"
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
    bStardust=Args._Style.FocusedBG&&Args._Style.FocusedBG->GetName()==TEXT("T_Choice_StardustAtlas");
    if(bStardust){IdleBG=ChoiceStardust::Brush(Args._Style.IdleBG,0);FocusBG=ChoiceStardust::Brush(Args._Style.FocusedBG,1);Cursor=ChoiceStardust::Brush(Args._Style.Cursor,2);Star=ChoiceStardust::Brush(Args._Style.Cursor,3);}
    LockedBG=ChoiceStardust::LockedBrush(Args._Style.LockedAtlas,0);
    ClosedLock=ChoiceStardust::LockedBrush(Args._Style.LockedAtlas,1);
    OpenLock=ChoiceStardust::LockedBrush(Args._Style.LockedAtlas,2);
    ButtonStyle=FButtonStyle().SetNormal(FSlateNoResource()).SetHovered(FSlateNoResource()).SetPressed(FSlateNoResource()).SetDisabled(FSlateNoResource());
    ChildSlot[SAssignNew(Rows,SVerticalBox)];Refresh();
}
void SDirectorChoices::Refresh()
{
    auto New=Options.Get(TArray<FDirectorChoice>());const FGuid NewId=PromptId.Get(FGuid());
    // Keep a display snapshot so edits to a referenced row are detected on refresh.
    for(auto& Choice:New){Choice.Text=Choice.ResolveText();Choice.DisabledReason=Choice.ResolveDisabledReason();}
    bool Changed=!bInitialized||NewId!=CurrentPrompt||New.Num()!=Current.Num();
    if(!Changed)for(int32 I=0;I<New.Num();++I)if(New[I].Key!=Current[I].Key||!New[I].Text.EqualTo(Current[I].Text)||New[I].bEnabled!=Current[I].bEnabled||!New[I].DisabledReason.EqualTo(Current[I].DisabledReason)){Changed=true;break;}
    if(!Changed)return;
    const bool NewPrompt=!bInitialized||NewId!=CurrentPrompt;
    const FName FocusKey=Current.IsValidIndex(FocusedIndex)?Current[FocusedIndex].Key:NAME_None;
    if(NewPrompt){UnlockElapsed.Reset();UnlockReasons.Reset();bCommitted=false;}
    else for(const auto& C:New)
    {
        const auto* Old=Current.FindByPredicate([&](const FDirectorChoice& O){return O.Key==C.Key;});
        if(!C.bEnabled){UnlockElapsed.Remove(C.Key);UnlockReasons.Remove(C.Key);}
        else if(Old&&!Old->bEnabled){UnlockElapsed.Add(C.Key,0.f);UnlockReasons.Add(C.Key,Old->DisabledReason);}
    }
    bInitialized=true;CurrentPrompt=NewId;Current=New;
    FString Error;if(!DirectorChoices::Validate(Current,Error))Current.Reset();
    FocusedIndex=NewPrompt?INDEX_NONE:Current.IndexOfByPredicate([&](const FDirectorChoice& C){return C.Key==FocusKey&&C.bEnabled;});
    if(FocusedIndex==INDEX_NONE)FocusedIndex=Current.IndexOfByPredicate([](const FDirectorChoice& C){return C.bEnabled;});
    Rebuild();
}
void SDirectorChoices::Rebuild()
{
    Rows->ClearChildren();
    for(int32 I=0;I<Current.Num();++I)
    {
        if(bStardust)
        {
         Rows->AddSlot().AutoHeight().Padding(0,0,0,8)
         [SNew(SBox).WidthOverride(460).MinDesiredHeight(72)
          [SNew(SOverlay)
           +SOverlay::Slot().Padding(36,0,0,0)
           [SNew(SImage).Image_Lambda([this,I]{return FocusedIndex==I?&FocusBG:&IdleBG;})
            .ColorAndOpacity_Lambda([this,I]{return FMath::Lerp(FLinearColor(.3f,.35f,.46f),FLinearColor::White,Current[I].bEnabled?GetUnlockProgress(Current[I].Key):0.f);}).Visibility(EVisibility::HitTestInvisible)]
           +SOverlay::Slot().Padding(36,0,0,0)
           [SNew(SImage).Image(&LockedBG).ColorAndOpacity_Lambda([this,I]{return FLinearColor(1,1,1,Current[I].bEnabled?1.f-GetUnlockProgress(Current[I].Key):1.f);}).Visibility(EVisibility::HitTestInvisible)]
           +SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Center)
           [SNew(SImage).Image(&Cursor).Visibility_Lambda([this,I]{return FocusedIndex==I?EVisibility::HitTestInvisible:EVisibility::Hidden;})]
           +SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Center).Padding(0,0,6,0)
           [SNew(SImage).Image(&Star).ColorAndOpacity_Lambda([this]{return FLinearColor(1,1,1,ChoiceStardust::Sparkle(SparkleTime));})
            .Visibility_Lambda([this,I]{return FocusedIndex==I?EVisibility::HitTestInvisible:EVisibility::Hidden;})]
           +SOverlay::Slot().Padding(36,0,0,0)
           [SNew(SButton).ButtonStyle(&ButtonStyle).IsFocusable(false).ContentPadding(FMargin(36,20,44,20)).HAlign(HAlign_Left).VAlign(VAlign_Center)
            .IsEnabled_Lambda([this,I]{return Current[I].bEnabled&&CanChoose.Get(false)&&!bCommitted;})
            .OnHovered_Lambda([this,I]{if(Current[I].bEnabled&&!bCommitted&&CanChoose.Get(false))FocusedIndex=I;})
            .OnClicked_Lambda([this,I]{Choose(I);return FReply::Handled();})
            [SNew(SVerticalBox)
             +SVerticalBox::Slot().AutoHeight()
             [SNew(STextBlock).Text(Current[I].Text).Font(FCoreStyle::GetDefaultFontStyle("Regular",18))
              .ColorAndOpacity_Lambda([this,I]{return FMath::Lerp(FLinearColor(.46f,.49f,.57f),FLinearColor(.94f,.89f,.77f),Current[I].bEnabled?GetUnlockProgress(Current[I].Key):0.f);}).WrapTextAt(330)]
             +SVerticalBox::Slot().AutoHeight()
             [SNew(STextBlock).Text_Lambda([this,I]{return Current[I].bEnabled?UnlockReasons.FindRef(Current[I].Key):Current[I].DisabledReason;})
              .Font(FCoreStyle::GetDefaultFontStyle("Regular",14)).WrapTextAt(330)
              .ColorAndOpacity_Lambda([this,I]{return FLinearColor(.46f,.49f,.57f,Current[I].bEnabled?1.f-GetUnlockProgress(Current[I].Key):1.f);})
              .Visibility_Lambda([this,I]{return (!Current[I].bEnabled&&!Current[I].DisabledReason.IsEmpty())||(Current[I].bEnabled&&GetUnlockProgress(Current[I].Key)<1.f&&!UnlockReasons.FindRef(Current[I].Key).IsEmpty())?EVisibility::HitTestInvisible:EVisibility::Collapsed;})]]]
           +SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Center).Padding(0,0,12,0)
           [SNew(SImage).Image(&ClosedLock).ColorAndOpacity_Lambda([this,I]{const float P=Current[I].bEnabled?GetUnlockProgress(Current[I].Key):0.f;return FLinearColor(1,1,1,1.f-FMath::Clamp(P/.35f,0.f,1.f));}).Visibility(EVisibility::HitTestInvisible)]
           +SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Center).Padding(0,0,12,0)
           [SNew(SImage).Image(&OpenLock).ColorAndOpacity_Lambda([this,I]{const float P=Current[I].bEnabled?GetUnlockProgress(Current[I].Key):0.f;return FLinearColor(1,1,1,FMath::Clamp(P/.35f,0.f,1.f)*(1.f-FMath::Clamp((P-.4f)/.6f,0.f,1.f)));}).Visibility(EVisibility::HitTestInvisible)]]];
         continue;
        }
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
float SDirectorChoices::GetUnlockProgress(FName Key) const
{const float* Time=UnlockElapsed.Find(Key);return Time?FMath::Clamp(*Time/.9f,0.f,1.f):1.f;}
void SDirectorChoices::Tick(const FGeometry& G,double T,float D)
{SCompoundWidget::Tick(G,T,D);SparkleTime+=D;for(auto& Pair:UnlockElapsed)Pair.Value=FMath::Min(.9f,Pair.Value+FMath::Max(0.f,D));Refresh();}
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
