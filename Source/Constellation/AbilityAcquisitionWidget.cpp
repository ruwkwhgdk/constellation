#include "AbilityAcquisitionWidget.h"
#include "AbilityAcquisitionArt.h"
#include "AbilityAcquisitionModel.h"
#include "Engine/Texture2D.h"
#include "Engine/Font.h"
#include "Rendering/DrawElements.h"
#include "Framework/Application/SlateApplication.h"
#include "Fonts/FontMeasure.h"
#include "Widgets/Layout/SBox.h"
#include "Styling/CoreStyle.h"
TSharedRef<SWidget> UAbilityAcquisitionWidget::RebuildWidget(){return SNew(SBox);}
int32 UAbilityAcquisitionWidget::NativePaint(const FPaintArgs& Args,const FGeometry& G,const FSlateRect& Cull,FSlateWindowElementList& Out,int32 Layer,const FWidgetStyle& Style,bool Enabled)const
{
 if(!Art||!Art->IsReady())return Layer;
 using namespace AbilityAcquisition;
 const float Scale=FMath::Min(G.GetLocalSize().X/1920.f,G.GetLocalSize().Y/1080.f);
 const FGeometry C=G.MakeChild(FVector2D(1920,1080),FSlateLayoutTransform(Scale,(G.GetLocalSize()-FVector2D(1920,1080)*Scale)*.5));
 FSlateDrawElement::MakeBox(Out,Layer++,G.ToPaintGeometry(),FCoreStyle::Get().GetBrush("WhiteBrush"),ESlateDrawEffect::None,FLinearColor(0,0,0,ExitOpacity));
 auto Image=[&](UTexture2D* T,FVector2D P,FVector2D Size,float Alpha){if(!T||Alpha<=0)return;FSlateBrush B;B.SetResourceObject(T);B.ImageSize=FVector2f(Size);B.DrawAs=ESlateBrushDrawType::Image;FSlateDrawElement::MakeBox(Out,Layer++,C.ToPaintGeometry(Size,FSlateLayoutTransform(P)),&B,ESlateDrawEffect::None,FLinearColor(1,1,1,Alpha*ExitOpacity));};
 auto Text=[&](const FString& S,float Baseline,int32 Size,FLinearColor Color,float Alpha,bool Title=false){if(Alpha<=0)return;Size=FMath::RoundToInt(Size*.75f);FSlateFontInfo Font=FCoreStyle::GetDefaultFontStyle("Regular",Size);if(Title&&Art->TitleFont)Font=FSlateFontInfo(Art->TitleFont,Size);const FVector2D Ext=FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(S,Font);Color.A=Alpha*ExitOpacity;FSlateDrawElement::MakeText(Out,Layer++,C.ToPaintGeometry(Ext,FSlateLayoutTransform(FVector2D(960-Ext.X*.5,Baseline-Ext.Y))),S,Font,ESlateDrawEffect::None,Color);};
 Image(Art->Emblem,{640,250},{640,580},Fade(Elapsed,.35,1.55)*(1-Fade(Elapsed,2.25,2.9)));
 const float Reveal=Fade(Elapsed,2.9,4),Ignition=Fade(Elapsed,4,4.65),Words=Reveal*Fade(Elapsed,4.8,5.8);
 Image(Art->Background,{0,0},{1920,1080},Reveal);
 for(int32 I=0;I<7;I++)if(!(OwnedMask&(1<<I))||I==Slot)Image(Art->Dormant[I],Position(I)-FVector2D(110,110),{220,220},Reveal*(I==Slot?1-Ignition:1));
 Text(TEXT("C O R O N A   B O R E A L I S"),70,19,FLinearColor(FColor(201,181,134)),Reveal,true);
 for(int32 I=0;I<6;I++){Image(Art->Lines[I],{0,0},{1920,1080},Reveal);if((OwnedMask&(1<<Link(I)))&&(OwnedMask&(1<<Link(I+1))))Image(Art->LitLines[I],{0,0},{1920,1080},Reveal*((Link(I)==Slot||Link(I+1)==Slot)?Fade(Elapsed,4,5.3):1));}
 for(int32 I=0;I<7;I++)if(OwnedMask&(1<<I)){const float Pop=I==Slot?1+.12f*FMath::Sin(Fade(Elapsed,4,5.3)*PI):1;const FVector2D Size=FVector2D(220,220)*Pop;Image(I==Slot?Art->NewStars[I]:Art->Stars[I],Position(I)-Size*.5,Size,Reveal*(I==Slot?Ignition:1));}
 static const TCHAR* Titles[]={TEXT("α CrB"),TEXT("β CrB"),TEXT("γ CrB")};Text(Titles[FMath::Clamp(Slot,0,2)],145,58,FLinearColor(FColor(243,226,183)),Words,true);
 const FLinearColor Divider(0.52f,0.43f,0.25f,Words*.55f*ExitOpacity);
 for(const FVector2D P:{FVector2D(770,838),FVector2D(1000,838)})FSlateDrawElement::MakeBox(Out,Layer++,C.ToPaintGeometry(FVector2D(150,1),FSlateLayoutTransform(P)),FCoreStyle::Get().GetBrush("WhiteBrush"),ESlateDrawEffect::None,Divider);
 FSlateDrawElement::MakeBox(Out,Layer++,C.ToPaintGeometry(FVector2D(5,5),FSlateLayoutTransform(FVector2D(957.5,836))),FCoreStyle::Get().GetBrush("WhiteBrush"),ESlateDrawEffect::None,Divider);
 FString Body=Art->Description(Slot).ToString().Replace(TEXT("\\n"),TEXT("\n"));TArray<FString> Lines;Body.ParseIntoArrayLines(Lines,false);for(int32 I=0;I<Lines.Num();I++)Text(Lines[I],896+43*I,25,FLinearColor(FColor(236,226,201)),Words);
 if(Elapsed>=6.2)Text(TEXT("Press Any Key"),1010,22,FLinearColor(FColor(216,199,153)),.4f+.6f*(.5f+.5f*FMath::Cos(Elapsed*2.4)),true);
 return Layer;
}
