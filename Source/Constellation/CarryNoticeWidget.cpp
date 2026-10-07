#include "CarryNoticeWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "TimerManager.h"
void UCarryNoticeWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(); WidgetTree->RootWidget = Canvas;
    Label = WidgetTree->ConstructWidget<UTextBlock>(); Label->SetJustification(ETextJustify::Center);
    FSlateFontInfo Font = Label->GetFont(); Font.Size = 22; Label->SetFont(Font);
    Label->SetShadowColorAndOpacity(FLinearColor::Black); Label->SetShadowOffset(FVector2D(1,2));
    UCanvasPanelSlot* CanvasSlot = Canvas->AddChildToCanvas(Label);
    CanvasSlot->SetAnchors(FAnchors(.5f,.78f)); CanvasSlot->SetAlignment(FVector2D(.5f,.5f)); CanvasSlot->SetAutoSize(true);
    SetVisibility(ESlateVisibility::Collapsed);
}
void UCarryNoticeWidget::ShowMessage(const FText& Message,float Duration)
{
    if (!Label) return;
    Label->SetText(Message); SetVisibility(ESlateVisibility::HitTestInvisible);
    GetWorld()->GetTimerManager().SetTimer(HideTimer, FTimerDelegate::CreateWeakLambda(this,[this]()
    { SetVisibility(ESlateVisibility::Collapsed); }),Duration,false);
}
