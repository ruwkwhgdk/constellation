#include "InteractionPromptWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Engine/Texture2D.h"

void UInteractionPromptWidget::SetBackgroundTexture(UTexture2D* Texture)
{
    if(Background) Background->SetBrushFromTexture(Texture);
}
void UInteractionPromptWidget::SetKeyBackgroundTexture(UTexture2D* Texture)
{
    if(KeyBackground)
    {
        KeyBackground->SetBrushFromTexture(Texture);
        KeyBackground->SetVisibility(Texture ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    }
}
void UInteractionPromptWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    SetIsFocusable(false);
    UCanvasPanel* Canvas=WidgetTree->ConstructWidget<UCanvasPanel>(); WidgetTree->RootWidget=Canvas;
    UCanvasPanel* Row=WidgetTree->ConstructWidget<UCanvasPanel>();
    UCanvasPanelSlot* RowSlot=Canvas->AddChildToCanvas(Row);
    RowSlot->SetAnchors(FAnchors(.60f,.55f)); RowSlot->SetAlignment(FVector2D(0,.5)); RowSlot->SetSize(FVector2D(404,81));
    Background=WidgetTree->ConstructWidget<UImage>();
    UCanvasPanelSlot* BackgroundSlot=Row->AddChildToCanvas(Background);
    BackgroundSlot->SetPosition(FVector2D(44,0)); BackgroundSlot->SetSize(FVector2D(360,81));
    KeyBackground=WidgetTree->ConstructWidget<UImage>();
    UCanvasPanelSlot* KeyBackgroundSlot=Row->AddChildToCanvas(KeyBackground);
    KeyBackgroundSlot->SetPosition(FVector2D(0,20.5f)); KeyBackgroundSlot->SetSize(FVector2D(40,40));
    KeyBackground->SetVisibility(ESlateVisibility::Collapsed);
    auto Label=[this,Row](FVector2D Position,FVector2D Size,int32 FontSize,ETextJustify::Type Justify)
    {
        UTextBlock* Text=WidgetTree->ConstructWidget<UTextBlock>();
        FSlateFontInfo Font=Text->GetFont(); Font.Size=FontSize; Font.TypefaceFontName=TEXT("Bold"); Text->SetFont(Font);
        Text->SetColorAndOpacity(FLinearColor(.91f,.88f,.78f,1)); Text->SetJustification(Justify);
        Text->SetShadowColorAndOpacity(FLinearColor::Black); Text->SetShadowOffset(FVector2D(1,2));
        UCanvasPanelSlot* Slot=Row->AddChildToCanvas(Text); Slot->SetPosition(Position); Slot->SetSize(Size);
        return Text;
    };
    KeyLabel=Label(FVector2D(0,25),FVector2D(40,38),22,ETextJustify::Center);
    KeyLabel->SetColorAndOpacity(FLinearColor(.025f,.025f,.02f,1));
    KeyLabel->SetShadowOffset(FVector2D::ZeroVector);
    ActionLabel=Label(FVector2D(77,24),FVector2D(290,40),23,ETextJustify::Left);
    SetVisibility(ESlateVisibility::Collapsed);
}
void UInteractionPromptWidget::SetPrompt(const FText& Key,const FText& Action)
{
    if(!KeyLabel || !ActionLabel) return;
    KeyLabel->SetText(Key); ActionLabel->SetText(Action);
    SetVisibility(Key.IsEmpty() || Action.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
}
