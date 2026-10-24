#include "ItemAcquisitionWidget.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "Engine/Font.h"
#include "Engine/Texture2D.h"
#include "Framework/Application/SlateApplication.h"
#include "Rendering/DrawElements.h"
#include "Rendering/SlateRenderer.h"
#include "Styling/CoreStyle.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "UObject/ConstructorHelpers.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SLeafWidget.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
class SRelicArt : public SLeafWidget
{
public:
 SLATE_BEGIN_ARGS(SRelicArt) : _Sprite(false), _Keycap(false), _Brush(nullptr) {}
  SLATE_ARGUMENT(bool, Sprite)
  SLATE_ARGUMENT(bool, Keycap)
  SLATE_ARGUMENT(const FSlateBrush*, Brush)
  SLATE_ATTRIBUTE(float, Opacity)
  SLATE_ATTRIBUTE(float, Scale)
  SLATE_ATTRIBUTE(FVector2D, Offset)
 SLATE_END_ARGS()
 void Construct(const FArguments& A) { bSprite=A._Sprite; bKeycap=A._Keycap; Brush=A._Brush; Opacity=A._Opacity; Scale=A._Scale; Offset=A._Offset; SetVisibility(EVisibility::HitTestInvisible); }
 FVector2D ComputeDesiredSize(float) const override { return bKeycap?FVector2D(42,32):FVector2D(300,240); }
 bool ComputeVolatility() const override { return true; }
 int32 OnPaint(const FPaintArgs&,const FGeometry& G,const FSlateRect&,FSlateWindowElementList& E,int32 L,const FWidgetStyle& Style,bool) const override
 {
  const FVector2f S=G.GetLocalSize();
  const FLinearColor Tint=Style.GetColorAndOpacityTint()*FLinearColor(1,1,1,Opacity.Get(1));
  if(bKeycap)
  {
   TArray<FVector2f> Outline;
   const FVector2f Centers[4]={{6.7f,6.7f},{S.X-6.7f,6.7f},{S.X-6.7f,S.Y-6.7f},{6.7f,S.Y-6.7f}};
   for(int32 Corner=0;Corner<4;++Corner)for(int32 Step=0;Step<=8;++Step)
   {
    const float Angle=FMath::DegreesToRadians(180.f+Corner*90.f+Step*90.f/8.f);
    Outline.Add(Centers[Corner]+FVector2f(FMath::Cos(Angle),FMath::Sin(Angle))*6.f);
   }
   const FVector2f First=Outline[0];Outline.Add(First);
   FSlateDrawElement::MakeLines(E,L,G.ToPaintGeometry(),Outline,ESlateDrawEffect::None,FLinearColor::FromSRGBColor(FColor(191,160,106))*Tint,true,1.3f);
   return L;
  }
  // Dedicated designer textures contain the complete art: no extra tint/fill/frame.
  if(!bSprite&&Brush&&Brush->GetResourceObject())
  {
   FSlateDrawElement::MakeBox(E,L,G.ToPaintGeometry(),Brush,ESlateDrawEffect::None,Tint);
   return L;
  }
  if(bSprite)
  {
   if(Brush && Brush->GetResourceObject())
   {
    const FSlateRect R=UItemAcquisitionWidget::FitSprite(FVector2D(Brush->ImageSize),FVector2D(S),Scale.Get(1),Offset.Get(FVector2D::ZeroVector));
    FSlateDrawElement::MakeBox(E,L+1,G.ToPaintGeometry(FVector2f(R.Right-R.Left,R.Bottom-R.Top),FSlateLayoutTransform(FVector2f(R.Left,R.Top))),Brush,ESlateDrawEffect::None,Tint);
   }
   return L+1;
  }
  return L;
 }
private:
 bool bSprite=false,bKeycap=false; const FSlateBrush* Brush=nullptr;
 TAttribute<float> Opacity,Scale; TAttribute<FVector2D> Offset;
};
}

UItemAcquisitionWidget::UItemAcquisitionWidget(const FObjectInitializer& O):Super(O)
{
 static ConstructorHelpers::FObjectFinder<UTexture2D> Texture(TEXT("/Game/Constellation/UI/ItemAcquisition/RelicArt/T_RelicPanel.T_RelicPanel"));
 static ConstructorHelpers::FObjectFinder<UTexture2D> Halo(TEXT("/Game/Constellation/UI/ItemAcquisition/RelicArt/T_RelicHalo.T_RelicHalo"));
 static ConstructorHelpers::FObjectFinder<UTexture2D> Divider(TEXT("/Game/Constellation/UI/ItemAcquisition/RelicArt/T_RelicDivider.T_RelicDivider"));
 static ConstructorHelpers::FObjectFinder<UFont> Font(TEXT("/Game/Constellation/UI/RegionTitle/F_RegionMyeongjo.F_RegionMyeongjo"));
 NebulaTexture=Texture.Object; HaloTexture=Halo.Object; DividerTexture=Divider.Object; TitleFont=Font.Object; SetIsFocusable(false);
}

FSlateRect UItemAcquisitionWidget::FitSprite(FVector2D Image,FVector2D Well,float Scale,FVector2D Offset)
{
 if(Image.X<=0 || Image.Y<=0 || Well.X<=0 || Well.Y<=0) return FSlateRect(0,0,0,0);
 const FVector2D Size=Image*FMath::Min(Well.X/Image.X,Well.Y/Image.Y)*FMath::Clamp(Scale,.1f,1.f);
 const FVector2D Margin=(Well-Size)*.5;
 const FVector2D TopLeft=Margin+FVector2D(FMath::Clamp(Offset.X,-Margin.X,Margin.X),FMath::Clamp(Offset.Y,-Margin.Y,Margin.Y));
 return FSlateRect(TopLeft.X,TopLeft.Y,TopLeft.X+Size.X,TopLeft.Y+Size.Y);
}

void UItemAcquisitionWidget::SetPresentation(const FItemAcquisitionPresentation& P,FKey Key)
{
 Presentation=P; ConfirmLabel=Key.GetDisplayName(); SpriteBrush.SetResourceObject(P.Sprite);
 SpriteBrush.DrawAs=ESlateBrushDrawType::Image;
 SpriteBrush.ImageSize=P.Sprite?FVector2f(P.Sprite->GetSizeX(),P.Sprite->GetSizeY()):FVector2f(1,1);
 if(DescriptionScroll)DescriptionScroll->SetScrollOffset(0.f);
 InvalidateLayoutAndVolatility();
}
void UItemAcquisitionWidget::SetPresentationOpacity(float Panel,float Text)
{
 PanelOpacity=FMath::Clamp(Panel,0.f,1.f); TextOpacity=FMath::Clamp(Text,0.f,1.f);
 InvalidateLayoutAndVolatility();
}

void UItemAcquisitionWidget::ScrollDescription(float PixelDelta)
{
 if(DescriptionScroll && FMath::IsFinite(PixelDelta))
  DescriptionScroll->SetScrollOffset(FMath::Clamp(DescriptionScroll->GetScrollOffset()+PixelDelta,0.f,FMath::Max(0.f,DescriptionScroll->GetScrollOffsetOfEnd())));
}

void UItemAcquisitionWidget::ReleaseSlateResources(bool bReleaseChildren)
{
 Super::ReleaseSlateResources(bReleaseChildren);
 DescriptionScroll.Reset();
}

TSharedRef<SWidget> UItemAcquisitionWidget::RebuildWidget()
{
 NebulaBrush.SetResourceObject(NebulaTexture); NebulaBrush.DrawAs=ESlateBrushDrawType::Image;
 NebulaBrush.SetUVRegion(FBox2f(FVector2f(8.f/2048,72.f/768),FVector2f(2042.f/2048,690.f/768)));
 HaloBrush.SetResourceObject(HaloTexture); HaloBrush.DrawAs=ESlateBrushDrawType::Image;
 DividerBrush.SetResourceObject(DividerTexture); DividerBrush.DrawAs=ESlateBrushDrawType::Image;
 DividerBrush.SetUVRegion(FBox2f(FVector2f(120.f/1717,420.f/916),FVector2f(1600.f/1717,500.f/916)));
 FSlateFontInfo Heading=TitleFont?FSlateFontInfo(TitleFont,42,FName("Regular")):FCoreStyle::GetDefaultFontStyle("Regular",42);
 Heading.OutlineSettings.OutlineSize=1;
 Heading.OutlineSettings.OutlineColor=FLinearColor(.92f,.85f,.74f);
 const FSlateFontInfo Body=FCoreStyle::GetDefaultFontStyle("Regular",22);
 auto TextTint=[this]{return FSlateColor(FLinearColor(.92f,.85f,.74f,TextOpacity));};
 return SNew(SOverlay)
 +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center).Padding(32)
 [SNew(SScaleBox).Stretch(EStretch::ScaleToFit).StretchDirection(EStretchDirection::DownOnly)
  [SNew(SBox).WidthOverride(1028).HeightOverride(390)
   [SNew(SOverlay)
    +SOverlay::Slot()[SNew(SRelicArt).Brush(&NebulaBrush).Opacity_Lambda([this]{return PanelOpacity;})]
    +SOverlay::Slot().Padding(70,55,678,55)
       [SNew(SRelicArt).Brush(&HaloBrush).Opacity_Lambda([this]{return PanelOpacity*.22f;})]
    +SOverlay::Slot().Padding(60,18,668,20)
       [SNew(SRelicArt).Sprite(true).Brush(&SpriteBrush).Opacity_Lambda([this]{return PanelOpacity;})
        .Scale_Lambda([this]{return Presentation.SpriteScale;}).Offset_Lambda([this]{return Presentation.SpriteOffset;})]
    +SOverlay::Slot().Padding(410,76,65,74)
      [SNew(SVerticalBox)
       +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text_Lambda([this]{return Presentation.Name;}).Font(Heading).WrapTextAt(553).WrappingPolicy(ETextWrappingPolicy::AllowPerCharacterWrapping).ColorAndOpacity_Lambda(TextTint)]
       +SVerticalBox::Slot().AutoHeight().Padding(2,24,160,22)
            [SNew(SBox).HeightOverride(24)[SNew(SRelicArt).Brush(&DividerBrush).Opacity_Lambda([this]{return TextOpacity;})]]
       +SVerticalBox::Slot().FillHeight(1)
        [SAssignNew(DescriptionScroll,SScrollBox).ScrollBarThickness(FVector2f(8,8)).ScrollBarPadding(FMargin(2))
         +SScrollBox::Slot()[SNew(STextBlock).Text_Lambda([this]{return Presentation.Description;}).Font(Body).WrapTextAt(535).WrappingPolicy(ETextWrappingPolicy::AllowPerCharacterWrapping).LineHeightPercentage(1.3f).ColorAndOpacity_Lambda([this]{return FSlateColor(FLinearColor(.70f,.74f,.79f,TextOpacity));})]]
      ]
    +SOverlay::Slot().Padding(410,0,0,33).HAlign(HAlign_Left).VAlign(VAlign_Bottom)
     [SNew(STextBlock).Text_Lambda([this]{return Presentation.Quantity>1?FText::Format(NSLOCTEXT("ItemAcquisition","Quantity","× {0}"),FText::AsNumber(Presentation.Quantity)):FText::GetEmpty();}).Font(FCoreStyle::GetDefaultFontStyle("Regular",15)).ColorAndOpacity_Lambda(TextTint)]
    +SOverlay::Slot().Padding(0,0,65,34).HAlign(HAlign_Right).VAlign(VAlign_Bottom)
     [SNew(SBox).WidthOverride(58).HeightOverride(48)
          [SNew(SOverlay)
           +SOverlay::Slot()[SNew(SRelicArt).Keycap(true).Opacity_Lambda([this]{return TextOpacity;})]
           +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
            [SNew(STextBlock).Text_Lambda([this]{return ConfirmLabel;}).Font(FCoreStyle::GetDefaultFontStyle("Regular",20)).ColorAndOpacity_Lambda(TextTint)]]]
   ]
  ]
 ];
}
