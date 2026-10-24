#include "StardustChoiceWidget.h"
#include "ChoiceStardustStyle.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/RichTextBlock.h"
#include "Components/TextBlock.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/Image.h"
#include "Components/SizeBox.h"
#include "Engine/Font.h"
#include "UObject/ConstructorHelpers.h"
UStardustChoiceWidget::UStardustChoiceWidget(const FObjectInitializer& I):Super(I)
{
 static ConstructorHelpers::FObjectFinder<UTexture2D> T(TEXT("/Game/Constellation/UI/Dialogue/T_Choice_StardustAtlas"));Atlas=T.Object;
 static ConstructorHelpers::FObjectFinder<UTexture2D> L(TEXT("/Game/Constellation/UI/Dialogue/T_Choice_LockedAtlas"));LockedAtlas=L.Object;
}
void UStardustChoiceWidget::NativeConstruct()
{
 Super::NativeConstruct();
 if(!WidgetTree||!Atlas)return;
 auto* Root=Cast<UCanvasPanel>(WidgetTree->RootWidget);if(!Root)return;
 if(!Rows.IsEmpty()){RefreshChoiceVisuals();return;} // Re-add to viewport reuses the same skin and original buttons.
 UButton* Found[3];
 for(int32 I=0;I<3;++I){Found[I]=Cast<UButton>(WidgetTree->FindWidget(FName(*FString::Printf(TEXT("Choice_Button_%c"),'A'+I))));if(!Found[I])return;}
 if(auto* Old=WidgetTree->FindWidget(TEXT("HorizontalBox_41")))Old->SetVisibility(ESlateVisibility::Collapsed);
 auto* List=WidgetTree->ConstructWidget<UVerticalBox>();
 auto* Layout=Root->AddChildToCanvas(List);Layout->SetAnchors(FAnchors(.5f,.5f));Layout->SetAlignment(FVector2D(.5,.5));Layout->SetAutoSize(true);
 auto* Font=LoadObject<UFont>(nullptr,TEXT("/Engine/EngineFonts/Roboto.Roboto"));
 for(int32 I=0;I<3;++I)
 {
  auto* B=Found[I];B->RemoveFromParent();Buttons.Add(B);
  auto* Size=WidgetTree->ConstructWidget<USizeBox>();Size->SetWidthOverride(460);Size->SetMinDesiredHeight(72);auto* RowSlot=List->AddChildToVerticalBox(Size);RowSlot->SetPadding(FMargin(0,0,0,8));RowSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
  auto* Row=WidgetTree->ConstructWidget<UOverlay>();Rows.Add(Row);Size->AddChild(Row);
  auto AddImage=[&](int32 Part){auto* Image=WidgetTree->ConstructWidget<UImage>();Image->SetBrush(ChoiceStardust::Brush(Atlas,Part));Image->SetVisibility(ESlateVisibility::HitTestInvisible);auto* ImageSlot=Row->AddChildToOverlay(Image);ImageSlot->SetHorizontalAlignment(HAlign_Fill);ImageSlot->SetVerticalAlignment(VAlign_Fill);return Image;};
  auto* BG=AddImage(0);Backgrounds.Add(BG);CastChecked<UOverlaySlot>(BG->Slot)->SetPadding(FMargin(36,0,0,0));
  auto* LockedBG=AddImage(0);LockedBackgrounds.Add(LockedBG);LockedBG->SetBrush(ChoiceStardust::LockedBrush(LockedAtlas,0));CastChecked<UOverlaySlot>(LockedBG->Slot)->SetPadding(FMargin(36,0,0,0));
  auto* Indicator=AddImage(2);Cursors.Add(Indicator);auto* CS=CastChecked<UOverlaySlot>(Indicator->Slot);CS->SetHorizontalAlignment(HAlign_Left);CS->SetVerticalAlignment(VAlign_Center);
  auto* Star=AddImage(3);Stars.Add(Star);auto* SS=CastChecked<UOverlaySlot>(Star->Slot);SS->SetHorizontalAlignment(HAlign_Right);SS->SetVerticalAlignment(VAlign_Center);SS->SetPadding(FMargin(0,0,6,0));
  for(int32 Part=1;Part<=2;++Part){auto* Lock=AddImage(0);Lock->SetBrush(ChoiceStardust::LockedBrush(LockedAtlas,Part));auto* LS=CastChecked<UOverlaySlot>(Lock->Slot);LS->SetHorizontalAlignment(HAlign_Right);LS->SetVerticalAlignment(VAlign_Center);LS->SetPadding(FMargin(0,0,16,0));(Part==1?ClosedLocks:OpenLocks).Add(Lock);}
  auto* Text=Cast<URichTextBlock>(B->GetContent());Labels.Add(Text);
  auto* Content=WidgetTree->ConstructWidget<UVerticalBox>();B->ClearChildren();B->AddChild(Content);
  if(Text)Content->AddChildToVerticalBox(Text);
  auto* Reason=WidgetTree->ConstructWidget<UTextBlock>();Reasons.Add(Reason);Reason->SetFont(FSlateFontInfo(Font,16,FName("Regular")));Reason->SetColorAndOpacity(FSlateColor(FLinearColor(.4f,.42f,.43f)));Reason->SetAutoWrapText(true);Reason->SetWrapTextAt(326);Content->AddChildToVerticalBox(Reason);
  PreviousEnabled.Add(B->GetIsEnabled());UnlockElapsed.Add(-1.f);
  auto* BS=Row->AddChildToOverlay(B);BS->SetPadding(FMargin(36,0,0,0));BS->SetHorizontalAlignment(HAlign_Fill);BS->SetVerticalAlignment(VAlign_Fill);
  FButtonStyle Style=B->GetStyle();for(FSlateBrush* Brush:{&Style.Normal,&Style.Hovered,&Style.Pressed,&Style.Disabled})Brush->DrawAs=ESlateBrushDrawType::NoDrawType;Style.NormalPadding=FMargin(0);Style.PressedPadding=FMargin(0);B->SetStyle(Style);
  if(auto* ContentSlot=Cast<UButtonSlot>(B->GetContentSlot())){ContentSlot->SetPadding(FMargin(36,20,58,20));ContentSlot->SetHorizontalAlignment(HAlign_Left);ContentSlot->SetVerticalAlignment(VAlign_Center);}
  if(Text){Text->SetDefaultFont(FSlateFontInfo(Font,18,FName("Regular")));Text->SetDefaultColorAndOpacity(FSlateColor(FLinearColor(.94f,.89f,.77f)));Text->SetMinDesiredWidth(0);Text->SetMargin(FMargin(0));Text->SetAutoWrapText(true);Text->SetWrapTextAt(326);}
 }
 for(const auto& Entry:PendingEnabled){Buttons[Entry.Key]->SetIsEnabled(Entry.Value);PreviousEnabled[Entry.Key]=Entry.Value;Reasons[Entry.Key]->SetText(PendingReasons.FindRef(Entry.Key));}
 PendingEnabled.Reset();PendingReasons.Reset();
 RefreshChoiceVisuals();
}
void UStardustChoiceWidget::NativeTick(const FGeometry& G,float D)
{
 Super::NativeTick(G,D);Phase+=D;for(float& Elapsed:UnlockElapsed)if(Elapsed>=0.f){Elapsed+=D;if(Elapsed>=.9f)Elapsed=-1.f;}RefreshChoiceVisuals();
}
void UStardustChoiceWidget::RefreshChoiceVisuals()
{
 auto Visible=[](const UButton* B){return B->GetVisibility()!=ESlateVisibility::Collapsed&&B->GetVisibility()!=ESlateVisibility::Hidden;};
 for(int32 I=0;I<Buttons.Num();++I)if(Visible(Buttons[I])&&Buttons[I]->GetIsEnabled()&&Buttons[I]->HasKeyboardFocus())Active=I;
 for(int32 I=0;I<Buttons.Num();++I)if(Visible(Buttons[I])&&Buttons[I]->GetIsEnabled()&&Buttons[I]->IsHovered())Active=I;
 if(!Buttons.IsValidIndex(Active)||!Visible(Buttons[Active])||!Buttons[Active]->GetIsEnabled())
 {Active=INDEX_NONE;for(int32 I=0;I<Buttons.Num();++I)if(Visible(Buttons[I])&&Buttons[I]->GetIsEnabled()){Active=I;break;}}
 for(int32 I=0;I<Buttons.Num();++I)
 {
  const bool Enabled=Buttons[I]->GetIsEnabled();
  if(Enabled&&!PreviousEnabled[I])UnlockElapsed[I]=0.f;
  if(!Enabled)UnlockElapsed[I]=-1.f;
  PreviousEnabled[I]=Enabled;
  const bool Opening=UnlockElapsed[I]>=0.f;
  const float Progress=Opening?FMath::Clamp(UnlockElapsed[I]/.9f,0.f,1.f):1.f;
  const float Recovery=Enabled?Progress:0.f;
  LockedBackgrounds[I]->SetRenderOpacity(1.f-Recovery);
  LockedBackgrounds[I]->SetVisibility(Recovery<1.f?ESlateVisibility::HitTestInvisible:ESlateVisibility::Hidden);
  const float Open=FMath::Clamp(Progress*3.f,0.f,1.f);
  ClosedLocks[I]->SetVisibility(!Enabled||Opening?ESlateVisibility::HitTestInvisible:ESlateVisibility::Hidden);
  ClosedLocks[I]->SetRenderOpacity(Enabled?1.f-Open:1.f);
  OpenLocks[I]->SetVisibility(Opening?ESlateVisibility::HitTestInvisible:ESlateVisibility::Hidden);
  OpenLocks[I]->SetRenderOpacity(Open*(1.f-FMath::Clamp((Progress-.55f)/.45f,0.f,1.f)));
  OpenLocks[I]->SetRenderTranslation(FVector2D(0,-5.f*Progress));
  Reasons[I]->SetVisibility((!Enabled||Opening)&&!Reasons[I]->GetText().IsEmpty()?ESlateVisibility::HitTestInvisible:ESlateVisibility::Collapsed);Reasons[I]->SetRenderOpacity(1.f-Recovery);
  if(Labels[I])Labels[I]->SetDefaultColorAndOpacity(FSlateColor(FMath::Lerp(FLinearColor(.4f,.42f,.43f),FLinearColor(.94f,.89f,.77f),Recovery)));
  Rows[I]->GetParent()->SetVisibility(Visible(Buttons[I])?ESlateVisibility::SelfHitTestInvisible:ESlateVisibility::Collapsed);
  Backgrounds[I]->SetBrush(ChoiceStardust::Brush(Atlas,I==Active?1:0));
  auto V=I==Active?ESlateVisibility::HitTestInvisible:ESlateVisibility::Hidden;Cursors[I]->SetVisibility(V);Stars[I]->SetVisibility(V);Stars[I]->SetRenderOpacity(ChoiceStardust::Sparkle(Phase));
 }
}

bool UStardustChoiceWidget::SetChoiceAvailability(int32 Index,bool bEnabled,FText Reason)
{
 if(Index<0||Index>=3)return false;
 if(!Buttons.IsValidIndex(Index)){PendingEnabled.Add(Index,bEnabled);PendingReasons.Add(Index,Reason);return true;}
 if(!bEnabled)Reasons[Index]->SetText(Reason);Buttons[Index]->SetIsEnabled(bEnabled);RefreshChoiceVisuals();return true;
}
