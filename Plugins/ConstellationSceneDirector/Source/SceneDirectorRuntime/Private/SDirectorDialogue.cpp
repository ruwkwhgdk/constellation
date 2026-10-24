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
    bHasCustomPrepass=true;
    Position=Args._Position;
    Choices=Args._Choices;
    Dialogue=Args._Dialogue; Waiting=Args._Waiting; Advance=Args._OnAdvance;
    CharacterInterval=Args._CharacterInterval;RevealDuration=Args._RevealDuration;Prompt=Args._ChoicePrompt;TextTick=Args._OnTextTick;
    RefreshDialogue();
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
    // UVs select independently usable artwork; custom legacy textures keep their original brushes.
    const bool bMural=Args._Background && Args._Background->GetFName()==TEXT("T_Dialogue_QuietNebulaAtlas");
    auto AtlasRegion=[](FSlateBrush& Brush,UTexture2D* Texture,FVector2D Min,FVector2D Max)
    {
        if(Texture && Texture->GetFName()==TEXT("T_Dialogue_QuietNebulaAtlas"))
        {
            Brush.DrawAs=ESlateBrushDrawType::Image;
            Brush.SetUVRegion(FBox2f(FVector2f(Min.X/1536.f,Min.Y/1024.f),FVector2f(Max.X/1536.f,Max.Y/1024.f)));
        }
    };
    AtlasRegion(BackgroundBrush,Args._Background,{32,185},{1504,504});
    AtlasRegion(SpeakerBrush,Args._SpeakerBackground,{35,562},{552,675});
    AtlasRegion(ArrowBrush,Args._Continue,{648,682},{888,934});
    if(bMural){ArrowBrush.ImageSize=FVector2D(76,80);SpeakerBrush.ImageSize=FVector2D(182,40);}
    const FLinearColor Cream(.88f,.85f,.76f,1);
    FTextBlockStyle Body=FTextBlockStyle().SetFont(FCoreStyle::GetDefaultFontStyle(bMural?"Regular":"BoldItalic",18)).SetColorAndOpacity(Cream);
    TextStyles=MakeShared<FSlateStyleSet>("DirectorDialogueLocal");
    TextStyles->Set("Default",Body);
    TextStyles->Set("teal",FTextBlockStyle(Body).SetColorAndOpacity(FLinearColor(.20f,.83f,.73f)));
    TextStyles->Set("red",FTextBlockStyle(Body).SetColorAndOpacity(FLinearColor(1,.16f,.18f)));
    SetVisibility(TAttribute<EVisibility>::CreateLambda([this]{return Dialogue.Get().IsEmpty()?EVisibility::Collapsed:EVisibility::Visible;}));
    ChildSlot.VAlign(VAlign_Bottom)
    [SNew(SScaleBox).VAlign(VAlign_Bottom).Stretch(EStretch::ScaleToFit).StretchDirection(EStretchDirection::DownOnly)
     [SNew(SBox).WidthOverride(910)
      [SNew(SOverlay)
       // Options must not change the dialogue body's scale or bottom anchor.
       +SOverlay::Slot().VAlign(VAlign_Bottom).HAlign(HAlign_Right).Padding(0,0,0,230)
       [SAssignNew(ChoiceList,SDirectorChoices).Style(Args._ChoiceStyle).Options(Args._Choices).PromptId(Args._ChoicePrompt).CanChoose(Args._Waiting).OnChosen(Args._OnChoice)
        .Visibility_Lambda([this]{return Choices.Get(TArray<FDirectorChoice>()).IsEmpty()?EVisibility::Collapsed:EVisibility::Visible;})]
       +SOverlay::Slot().VAlign(VAlign_Bottom)
       [SNew(SOverlay)
       // Reserve headroom for the larger nameplate while keeping the body text below it.
       +SOverlay::Slot().Padding(0,bMural?18:36,0,0)
       [SNew(SBorder).BorderImage(&BackgroundBrush).BorderBackgroundColor(FLinearColor(1,1,1,bMural?1.f:.8f)).Padding(bMural?FMargin(116,42,105,42):FMargin(145,28,120,46))
        [SNew(SBox).MinDesiredHeight(bMural?100:110).VAlign(VAlign_Center)
         [SNew(SOverlay)
          // Measure the entire localized line so revealing it cannot resize the dialogue box.
          +SOverlay::Slot()[SNew(SRichTextBlock).Text(Args._Dialogue).Visibility(EVisibility::Hidden)
           .TextStyle(&TextStyles->GetWidgetStyle<FTextBlockStyle>("Default")).DecoratorStyleSet(TextStyles.Get()).WrapTextAt(bMural?689:645).LineHeightPercentage(1.08f)]
          +SOverlay::Slot()[SNew(SRichTextBlock).Text_Lambda([this]{return Reveal.GetText();})
           .TextStyle(&TextStyles->GetWidgetStyle<FTextBlockStyle>("Default")).DecoratorStyleSet(TextStyles.Get()).WrapTextAt(bMural?689:645).LineHeightPercentage(1.08f)]]]]
       +SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Top).Padding(bMural?104:44,0,0,0)
       [SNew(SBorder).BorderImage(&SpeakerBrush).Padding(bMural?FMargin(20,6):FMargin(40,12))
        .Visibility_Lambda([Speaker=Args._Speaker]{return Speaker.Get().ToString().TrimStartAndEnd().IsEmpty()?EVisibility::Collapsed:EVisibility::SelfHitTestInvisible;})
        [SNew(SBox).MinDesiredWidth(bMural?142:90).MinDesiredHeight(bMural?24:30).VAlign(VAlign_Center)
         [SNew(STextBlock).Justification(ETextJustify::Center).Text(Args._Speaker).Font(FCoreStyle::GetDefaultFontStyle(bMural?"Regular":"Italic",bMural?14:11)).ColorAndOpacity(Cream)
        .ShadowOffset(FVector2D(1,2)).ShadowColorAndOpacity(FLinearColor(0,0,0,.6f))]]]
       +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,bMural?-44:6)
       [SAssignNew(Arrow,SImage).Image(&ArrowBrush)
        .Visibility_Lambda([this]{return Waiting.Get(false)&&!Reveal.IsRevealing()&&Choices.Get(TArray<FDirectorChoice>()).IsEmpty()?EVisibility::HitTestInvisible:EVisibility::Hidden;})]
      ]]]];
}
bool SDirectorDialogue::CustomPrepass(float LayoutScaleMultiplier)
{
    RefreshDialogue();
    ChildSlot.VAlign(Position.Get()==EDirectorDialoguePosition::Top?VAlign_Top:(Position.Get()==EDirectorDialoguePosition::Center?VAlign_Center:VAlign_Bottom));
    // Choice rows otherwise rebuild in Tick, after the panel was measured with no rows.
    // Populate them before child prepass so the first visible frame has its final size.
    ChoiceList->Refresh();
    return true;
}
void SDirectorDialogue::RefreshDialogue()
{
    const FText Text=Dialogue.Get(FText::GetEmpty());
    const FGuid Id=Prompt.Get(FGuid());
    // A timed cue may keep its last line visible after its prompt ID is cleared.
    // Only an actual new cue (or changed localized text) should restart typing.
    if((Id.IsValid()&&Id!=LastPrompt)||!LastDialogue.IdenticalTo(Text))
    {
        LastPrompt=Id;LastDialogue=Text;
        Reveal.Reset(Text,CharacterInterval.Get(0.f),RevealDuration.Get(0.f));
    }
    LastPrompt=Id;
}
bool SDirectorDialogue::FinishReveal()
{
    RefreshDialogue();return Reveal.Finish();
}
void SDirectorDialogue::Tick(const FGeometry& Geometry,double CurrentTime,float DeltaTime)
{
    RefreshDialogue();
    if(Reveal.Advance(DeltaTime))TextTick.ExecuteIfBound();
    SCompoundWidget::Tick(Geometry,CurrentTime,DeltaTime);
    if(!Waiting.Get(false)){ArrowTime=0;return;}
    ArrowTime+=DeltaTime;
    // Slow rise, soft return; a six-unit excursion at the reference canvas size.
    const float Rise=3.f*(1.f-FMath::Cos(float(ArrowTime)*2.f*PI/1.15f));
    Arrow->SetRenderTransform(FSlateRenderTransform(FVector2D(0,-Rise)));
}
FReply SDirectorDialogue::OnMouseButtonDown(const FGeometry&,const FPointerEvent& Event)
{
    if(Event.GetEffectingButton()==EKeys::LeftMouseButton&&FinishReveal())return FReply::Handled();
    if(Choices.Get(TArray<FDirectorChoice>()).IsEmpty() && Event.GetEffectingButton()==EKeys::LeftMouseButton && Waiting.Get(false) && Advance.IsBound())
    {Advance.Execute();return FReply::Handled();}
    return FReply::Unhandled();
}
