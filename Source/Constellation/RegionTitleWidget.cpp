#include "RegionTitleWidget.h"

#include "Engine/Font.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"
#include "UObject/ConstructorHelpers.h"
#include "UObject/UnrealType.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SLeafWidget.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
 // Ornaments remain resolution-independent and have separate reveal clocks from the live text.
 class SRegionOrnament : public SLeafWidget
 {
 public:
  SLATE_BEGIN_ARGS(SRegionOrnament) : _Divider(false) {}
   SLATE_ARGUMENT(bool,Divider)
   SLATE_ATTRIBUTE(float,StarsOpacity)
   SLATE_ATTRIBUTE(float,LinesOpacity)
  SLATE_END_ARGS()
  void Construct(const FArguments& Args)
  {
   bDivider=Args._Divider;StarsOpacity=Args._StarsOpacity;LinesOpacity=Args._LinesOpacity;
   SetVisibility(EVisibility::HitTestInvisible);
  }
  virtual FVector2D ComputeDesiredSize(float) const override { return bDivider?FVector2D(320,24):FVector2D(600,90); }
  virtual bool ComputeVolatility() const override { return true; }
  virtual int32 OnPaint(const FPaintArgs& Args,const FGeometry& Geometry,const FSlateRect& CullingRect,
   FSlateWindowElementList& Elements,int32 Layer,const FWidgetStyle& Style,bool bParentEnabled) const override
  {
   const FVector2f Size=Geometry.GetLocalSize();
   const FLinearColor Tint=Style.GetColorAndOpacityTint();
   auto Line=[&](FVector2f A,FVector2f B,FLinearColor Color,float Width=1.f)
   {
    TArray<FVector2f> Points{A,B};
    FSlateDrawElement::MakeLines(Elements,Layer,Geometry.ToPaintGeometry(),Points,ESlateDrawEffect::None,Color*Tint,true,Width);
   };
   const FLinearColor Gold(.88f,.70f,.36f,LinesOpacity.Get(0));
   if(bDivider)
   {
    const FVector2f Center=Size*.5f;
    Line(FVector2f(0,Center.Y),Center-FVector2f(18,0),Gold*.7f);
    Line(Center+FVector2f(18,0),FVector2f(Size.X,Center.Y),Gold*.7f);
    const FVector2f Corners[]={Center+FVector2f(0,-6),Center+FVector2f(6,0),Center+FVector2f(0,6),Center+FVector2f(-6,0)};
    for(int32 Index=0;Index<4;++Index)Line(Corners[Index],Corners[(Index+1)%4],Gold,1.2f);
    return Layer;
   }
   const FVector2f Positions[]={FVector2f(.09f,.38f),FVector2f(.29f,.72f),FVector2f(.53f,.50f),FVector2f(.73f,.53f),FVector2f(.89f,.13f)};
   for(int32 Index=0;Index<4;++Index)
   {
    const FVector2f Start=Positions[Index]*Size,End=Positions[Index+1]*Size;
    const FVector2f Direction=(End-Start).GetSafeNormal();const float Length=(End-Start).Size();
    for(float Distance=14;Distance<Length-14;Distance+=14)
     Line(Start+Direction*Distance,Start+Direction*FMath::Min(Distance+9,Length-14),Gold*.65f,.8f);
   }
   for(int32 Index=0;Index<5;++Index)
   {
    const FVector2f Center=Positions[Index]*Size;
    const float Radius=Index==2?22.f:Index==1||Index==3?9.f:5.f;
    const FLinearColor Star=Index==2?FLinearColor(1.f,.91f,.66f,StarsOpacity.Get(0)):FLinearColor(.91f,.76f,.47f,StarsOpacity.Get(0));
    Line(Center-FVector2f(Radius,0),Center+FVector2f(Radius,0),Star,Index==2?1.8f:1.2f);
    Line(Center-FVector2f(0,Radius),Center+FVector2f(0,Radius),Star,Index==2?1.8f:1.2f);
    const FVector2f Diagonal(Radius*.43f,Radius*.43f);
    Line(Center-Diagonal,Center+Diagonal,Star,1.f);
    Line(Center-FVector2f(Diagonal.X,-Diagonal.Y),Center+FVector2f(Diagonal.X,-Diagonal.Y),Star,1.f);
    const float Core=Index==2?3.f:1.5f;
    FSlateDrawElement::MakeBox(Elements,Layer+1,Geometry.ToPaintGeometry(FVector2f(Core*2),FSlateLayoutTransform(Center-FVector2f(Core))),
     FCoreStyle::Get().GetBrush("WhiteBrush"),ESlateDrawEffect::None,Star*Tint);
   }
   return Layer+1;
  }
 private:
  bool bDivider=false;
  TAttribute<float> StarsOpacity,LinesOpacity;
 };
}

TArray<TWeakObjectPtr<URegionTitleWidget>> URegionTitleWidget::ActivePresentations;

URegionTitleWidget::URegionTitleWidget(const FObjectInitializer& ObjectInitializer):Super(ObjectInitializer)
{
 static ConstructorHelpers::FObjectFinder<UTexture2D> Texture(TEXT("/Game/Constellation/UI/RegionTitle/T_RegionNebula.T_RegionNebula"));
 static ConstructorHelpers::FObjectFinder<UFont> Font(TEXT("/Game/Constellation/UI/RegionTitle/F_RegionMyeongjo.F_RegionMyeongjo"));
 NebulaTexture=Texture.Object;
 TitleFont=Font.Succeeded()?FSlateFontInfo(Font.Object,120,FName("Regular")):FCoreStyle::GetDefaultFontStyle("Regular",120);
 SubtitleFont=Font.Succeeded()?FSlateFontInfo(Font.Object,34,FName("Regular")):FCoreStyle::GetDefaultFontStyle("Regular",34);
 SetIsFocusable(false);
}

TSharedRef<SWidget> URegionTitleWidget::RebuildWidget()
{
 Super::RebuildWidget(); // Preserve the Blueprint tree, variable bindings, and its Construct event.
 NebulaBrush.SetResourceObject(NebulaTexture);NebulaBrush.DrawAs=ESlateBrushDrawType::Image;NebulaBrush.ImageSize=FVector2f(1000,540);
 const FLinearColor Ivory(1.f,.90f,.66f),SubtitleGold(.91f,.79f,.55f);
 return SNew(SOverlay).Visibility(EVisibility::HitTestInvisible)
 + SOverlay::Slot().Padding(32,0,32,90)
 [SNew(SScaleBox).Stretch(EStretch::ScaleToFit).StretchDirection(EStretchDirection::DownOnly).HAlign(HAlign_Center).VAlign(VAlign_Center)
  [SNew(SBox).WidthOverride(1000).HeightOverride(540)
   [SNew(SOverlay)
    + SOverlay::Slot()
     [SNew(SImage).Image(&NebulaBrush).ColorAndOpacity_Lambda([this]{return FLinearColor(1,1,1,FMath::Clamp(NebulaOpacity,0.f,1.f)*GetTextOpacity());})]
    + SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
     [SNew(SVerticalBox)
      + SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)
       [SNew(SBox).WidthOverride(600).HeightOverride(90)
        [SNew(SRegionOrnament).StarsOpacity_Lambda([this]{return GetStarsOpacity();}).LinesOpacity_Lambda([this]{return GetTextOpacity();})]]
      + SVerticalBox::Slot().AutoHeight().Padding(0,26,0,0)
       [SNew(SBox).WidthOverride(920).HeightOverride(150)
        [SNew(SScaleBox).Stretch(EStretch::ScaleToFit).StretchDirection(EStretchDirection::DownOnly).HAlign(HAlign_Center).VAlign(VAlign_Center)
         [SNew(STextBlock).Text_Lambda([this]{return GetRegionTitleText();}).Font_Lambda([this]{return TitleFont;})
          .ColorAndOpacity_Lambda([this,Ivory]{FLinearColor Color=Ivory;Color.A=GetTextOpacity();return Color;})
          .ShadowOffset(FVector2D(0,2)).ShadowColorAndOpacity_Lambda([this]{return FLinearColor(.003f,.005f,.009f,.85f*GetTextOpacity());}).Justification(ETextJustify::Center)]]]
      + SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)
       [SNew(SBox).WidthOverride(320).HeightOverride_Lambda([this]{return FMath::Max(0.f,TitleSubtitleGap);})
        [SNew(SOverlay)+SOverlay::Slot().VAlign(VAlign_Center)
         [SNew(SRegionOrnament).Divider(true).LinesOpacity_Lambda([this]{return GetTextOpacity();})]]]
      + SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)
       [SNew(SBox).WidthOverride(900).HeightOverride(54)
        [SNew(SScaleBox).Stretch(EStretch::ScaleToFit).StretchDirection(EStretchDirection::DownOnly).HAlign(HAlign_Center).VAlign(VAlign_Center)
         [SNew(STextBlock).Text_Lambda([this]{return GetRegionSubtitleText();}).Font_Lambda([this]{return SubtitleFont;})
          .ColorAndOpacity_Lambda([this,SubtitleGold]{FLinearColor Color=SubtitleGold;Color.A=GetTextOpacity();return Color;})
          .ShadowOffset(FVector2D(0,2)).ShadowColorAndOpacity_Lambda([this]{return FLinearColor(.003f,.005f,.009f,.85f*GetTextOpacity());}).Justification(ETextJustify::Center)]]]
     ]
   ]
  ]
 ];
}

FText URegionTitleWidget::ReadRegionText(FName PropertyName,const FText& Fallback,const TCHAR* MarkupTag) const
{
 const FTextProperty* Property=FindFProperty<FTextProperty>(GetClass(),PropertyName);
 const FText Text=Property?Property->GetPropertyValue_InContainer(this):Fallback;
 const FString String=Text.ToString(),Prefix=FString::Printf(TEXT("<%s>"),MarkupTag);
 // Existing triggers wrap localized display strings for the old RichText widgets.
 // Strip only those known outer wrappers; ordinary text and localization remain live.
 if(String.StartsWith(Prefix)&&String.EndsWith(TEXT("</>")))return FText::FromString(String.Mid(Prefix.Len(),String.Len()-Prefix.Len()-3));
 return Text;
}
FText URegionTitleWidget::GetRegionTitleText() const { return ReadRegionText(TEXT("RegionTitleName"),FallbackTitle,TEXT("RegionTitle_Name")); }
FText URegionTitleWidget::GetRegionSubtitleText() const { return ReadRegionText(TEXT("RegionTitleDesc"),FallbackSubtitle,TEXT("RegionTitle_Desc")); }
void URegionTitleWidget::SetRegionText(const FText& Title,const FText& Subtitle)
{
 FallbackTitle=Title;FallbackSubtitle=Subtitle;
 if(FTextProperty* Property=FindFProperty<FTextProperty>(GetClass(),TEXT("RegionTitleName")))Property->SetPropertyValue_InContainer(this,Title);
 if(FTextProperty* Property=FindFProperty<FTextProperty>(GetClass(),TEXT("RegionTitleDesc")))Property->SetPropertyValue_InContainer(this,Subtitle);
}
float URegionTitleWidget::GetFadeOutOpacity() const
{
 return bFinished?0.f:1.f-FMath::Clamp((Elapsed-3.2f)/.8f,0.f,1.f);
}
float URegionTitleWidget::GetStarsOpacity() const { return FMath::Clamp(Elapsed/.4f,0.f,1.f)*GetFadeOutOpacity(); }
float URegionTitleWidget::GetTextOpacity() const { return FMath::Clamp((Elapsed-.4f)/.5f,0.f,1.f)*GetFadeOutOpacity(); }

void URegionTitleWidget::NativeConstruct()
{
 Super::NativeConstruct();
 UnregisterPresentation();Elapsed=0;bFinished=false;bActive=true;
 SetIsFocusable(false);SetVisibility(ESlateVisibility::HitTestInvisible);
 const auto Snapshot=ActivePresentations;
 for(const auto& Weak:Snapshot)if(auto* Other=Weak.Get())
  if(Other!=this&&Other->GetWorld()==GetWorld()&&Other->GetOwningPlayer()==GetOwningPlayer())Other->FinishPresentation();
 ActivePresentations.AddUnique(this);
 if(UWorld* World=GetWorld())
 {
  World->GetTimerManager().ClearTimer(PresentationTimer);LastTickTime=World->GetTimeSeconds();
  World->GetTimerManager().SetTimer(PresentationTimer,this,&URegionTitleWidget::TickPresentation,1.f/60.f,true);
 }
}
void URegionTitleWidget::TickPresentation()
{
 if(UWorld* World=GetWorld())
 {
  const double Now=World->GetTimeSeconds();const float Delta=FMath::Max(0.0,Now-LastTickTime);LastTickTime=Now;
  AdvancePresentation(Delta);
 }
}
void URegionTitleWidget::AdvancePresentation(float DeltaSeconds)
{
 if(!bActive||bFinished)return;
 Elapsed+=FMath::Max(0.f,DeltaSeconds);
 if(Elapsed>=4.f)FinishPresentation();
}
void URegionTitleWidget::FinishPresentation()
{
 if(bFinished)return;
 bFinished=true;
 if(UWorld* World=GetWorld())World->GetTimerManager().ClearTimer(PresentationTimer);
 UnregisterPresentation();RemoveFromParent();
}
void URegionTitleWidget::UnregisterPresentation()
{
 bActive=false;
 ActivePresentations.RemoveAll([this](const auto& Weak){return !Weak.IsValid()||Weak.Get()==this;});
}
void URegionTitleWidget::NativeDestruct()
{
 if(UWorld* World=GetWorld())World->GetTimerManager().ClearTimer(PresentationTimer);
 bFinished=true;UnregisterPresentation();Super::NativeDestruct();
}
