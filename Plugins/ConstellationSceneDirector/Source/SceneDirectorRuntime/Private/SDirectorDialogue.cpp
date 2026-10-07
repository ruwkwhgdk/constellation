#include "SDirectorDialogue.h"
#include "Engine/Texture2D.h"
#include "InputCoreTypes.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Text/SRichTextBlock.h"

void SDirectorDialogue::Construct(const FArguments& Args)
{
    Position=Args._Position;
    Choices=Args._Choices;
    Dialogue=Args._Dialogue; Waiting=Args._Waiting; Advance=Args._OnAdvance;
    BackgroundBrush.SetResourceObject(Args._Background);
    BackgroundBrush.ImageSize=FVector2D(910,185);
    BackgroundBrush.DrawAs=ESlateBrushDrawType::Box;
    BackgroundBrush.Margin=FMargin(.105f,.49f);
    ArrowBrush.SetResourceObject(Args._Continue);
    ArrowBrush.ImageSize=FVector2D(38,26);
    ArrowBrush.DrawAs=ESlateBrushDrawType::Image;
    SpeakerBrush.SetResourceObject(Args._SpeakerBackground);
    SpeakerBrush.ImageSize=FVector2D(187.5f,42.5f);
    SpeakerBrush.DrawAs=ESlateBrushDrawType::Box;
    SpeakerBrush.Margin=FMargin(.12f,.49f);
    const FLinearColor Cream(.88f,.85f,.76f,1);
    FTextBlockStyle Body=FTextBlockStyle().SetFont(FCoreStyle::GetDefaultFontStyle("BoldItalic",18)).SetColorAndOpacity(Cream);
    TextStyles=MakeShared<FSlateStyleSet>("DirectorDialogueLocal");
    TextStyles->Set("Default",Body);
    TextStyles->Set("teal",FTextBlockStyle(Body).SetColorAndOpacity(FLinearColor(.20f,.83f,.73f)));
    TextStyles->Set("red",FTextBlockStyle(Body).SetColorAndOpacity(FLinearColor(1,.16f,.18f)));
    SetVisibility(TAttribute<EVisibility>::CreateLambda([this]{return Dialogue.Get().IsEmpty()?EVisibility::Collapsed:EVisibility::Visible;}));
    ChildSlot.VAlign(VAlign_Bottom)
    [SNew(SScaleBox).VAlign(VAlign_Bottom).Stretch(EStretch::ScaleToFit).StretchDirection(EStretchDirection::DownOnly)
     [SNew(SBox).WidthOverride(910)
      [SNew(SVerticalBox)
       +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Right).Padding(0,0,0,12)
       [SAssignNew(ChoiceList,SDirectorChoices).Style(Args._ChoiceStyle).Options(Args._Choices).PromptId(Args._ChoicePrompt).CanChoose(true).OnChosen(Args._OnChoice)
        .Visibility_Lambda([this]{return Choices.Get(TArray<FDirectorChoice>()).IsEmpty()?EVisibility::Collapsed:EVisibility::Visible;})]
       +SVerticalBox::Slot().AutoHeight()
       [SNew(SOverlay)
       // Reserve headroom for the larger nameplate while keeping the body text below it.
       +SOverlay::Slot().Padding(0,36,0,0)
       [SNew(SBorder).BorderImage(&BackgroundBrush).BorderBackgroundColor(FLinearColor(1,1,1,.8f)).Padding(FMargin(145,28,120,46))
        [SNew(SBox).MinDesiredHeight(110)
         [SNew(SRichTextBlock).Text(Args._Dialogue).TextStyle(&TextStyles->GetWidgetStyle<FTextBlockStyle>("Default"))
          .DecoratorStyleSet(TextStyles.Get()).WrapTextAt(645).LineHeightPercentage(1.08f)]]]
       +SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Top).Padding(44,0,0,0)
       [SNew(SBorder).BorderImage(&SpeakerBrush).Padding(FMargin(40,12))
        .Visibility_Lambda([Speaker=Args._Speaker]{return Speaker.Get().ToString().TrimStartAndEnd().IsEmpty()?EVisibility::Collapsed:EVisibility::SelfHitTestInvisible;})
        [SNew(SBox).MinDesiredWidth(90).MinDesiredHeight(30).VAlign(VAlign_Center)
         [SNew(STextBlock).Justification(ETextJustify::Center).Text(Args._Speaker).Font(FCoreStyle::GetDefaultFontStyle("Italic",11)).ColorAndOpacity(Cream)
        .ShadowOffset(FVector2D(1,2)).ShadowColorAndOpacity(FLinearColor(0,0,0,.6f))]]]
       +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,6)
       [SAssignNew(Arrow,SImage).Image(&ArrowBrush)
        .Visibility_Lambda([this]{return Waiting.Get(false)&&Choices.Get(TArray<FDirectorChoice>()).IsEmpty()?EVisibility::HitTestInvisible:EVisibility::Hidden;})]
      ]]]];
}
void SDirectorDialogue::Tick(const FGeometry& Geometry,double CurrentTime,float DeltaTime)
{
    ChildSlot.VAlign(Position.Get()==EDirectorDialoguePosition::Top?VAlign_Top:(Position.Get()==EDirectorDialoguePosition::Center?VAlign_Center:VAlign_Bottom));
    SCompoundWidget::Tick(Geometry,CurrentTime,DeltaTime);
    if(!Waiting.Get(false)){ArrowTime=0;return;}
    ArrowTime+=DeltaTime;
    // Slow rise, soft return; a six-unit excursion at the reference canvas size.
    const float Rise=3.f*(1.f-FMath::Cos(float(ArrowTime)*2.f*PI/1.15f));
    Arrow->SetRenderTransform(FSlateRenderTransform(FVector2D(0,-Rise)));
}
FReply SDirectorDialogue::OnMouseButtonDown(const FGeometry&,const FPointerEvent& Event)
{
    if(Choices.Get(TArray<FDirectorChoice>()).IsEmpty() && Event.GetEffectingButton()==EKeys::LeftMouseButton && Waiting.Get(false) && Advance.IsBound())
    {Advance.Execute();return FReply::Handled();}
    return FReply::Unhandled();
}
