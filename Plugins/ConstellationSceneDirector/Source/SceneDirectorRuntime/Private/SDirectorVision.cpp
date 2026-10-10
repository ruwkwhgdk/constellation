#include "SDirectorVision.h"
#include "Widgets/Layout/SBackgroundBlur.h"
#include "Widgets/SLeafWidget.h"
#include "Widgets/SOverlay.h"
#include "Rendering/DrawElements.h"
#include "Framework/Application/SlateApplication.h"
#include "Rendering/SlateRenderer.h"
#include "Styling/CoreStyle.h"
namespace
{
class SEyeSurface : public SLeafWidget
{
public:
 SLATE_BEGIN_ARGS(SEyeSurface){} SLATE_ATTRIBUTE(FDirectorVisionState,State) SLATE_END_ARGS()
 void Construct(const FArguments& Args){State=Args._State;SetVisibility(EVisibility::HitTestInvisible);}
 virtual FVector2D ComputeDesiredSize(float)const override{return FVector2D::ZeroVector;}
 virtual int32 OnPaint(const FPaintArgs&,const FGeometry& G,const FSlateRect&,FSlateWindowElementList& Out,int32 Layer,const FWidgetStyle&,bool)const override
 {
  const auto V=State.Get();const auto Size=G.GetLocalSize();const auto* Brush=FCoreStyle::Get().GetBrush("WhiteBrush");
  if(V.Haze>0){auto Tint=V.HazeColor;Tint.A=V.Haze;FSlateDrawElement::MakeBox(Out,Layer,G.ToPaintGeometry(),Brush,ESlateDrawEffect::None,Tint);}
  if(V.EyeOpen>=1)return Layer;
  if(V.EyeOpen<=0){FSlateDrawElement::MakeBox(Out,Layer+1,G.ToPaintGeometry(),Brush,ESlateDrawEffect::None,FLinearColor::Black);return Layer+1;}
  TArray<FSlateVertex> Vertices;TArray<SlateIndex> Indices;Vertices.Reserve(1024);Indices.Reserve(1536);
  const auto Transform=G.GetAccumulatedRenderTransform();
  auto Quad=[&](FVector2f A,FVector2f B,FVector2f C,FVector2f D,uint8 NearAlpha,uint8 FarAlpha)
  {
   SlateIndex I=Vertices.Num();
   Vertices.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(Transform,A,FVector2f(.5f,.5f),FColor(0,0,0,NearAlpha)));
   Vertices.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(Transform,B,FVector2f(.5f,.5f),FColor(0,0,0,NearAlpha)));
   Vertices.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(Transform,C,FVector2f(.5f,.5f),FColor(0,0,0,FarAlpha)));
   Vertices.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(Transform,D,FVector2f(.5f,.5f),FColor(0,0,0,FarAlpha)));
   Indices.Append({I,SlateIndex(I+1),SlateIndex(I+2),I,SlateIndex(I+2),SlateIndex(I+3)});
  };
  float H=Size.Y,W=Size.X,Feather=H*.016f*(1-V.EyeOpen);
  auto Edge=[&](float X){float N=X/W*2-1;return H*(1-V.EyeOpen)*(.5f+.16f*N*N);};
  for(int32 I=0;I<64;++I)
  {
   float X=W*I/64.f,Y=W*(I+1)/64.f,A=Edge(X),B=Edge(Y);
   Quad({X,0},{Y,0},{Y,B},{X,A},255,255);
   Quad({X,A},{Y,B},{Y,B+Feather},{X,A+Feather},255,0);
   Quad({X,H},{Y,H},{Y,H-B},{X,H-A},255,255);
   Quad({X,H-A},{Y,H-B},{Y,H-B-Feather},{X,H-A-Feather},255,0);
  }
  auto Handle=FSlateApplication::Get().GetRenderer()->GetResourceHandle(*Brush);
  FSlateDrawElement::MakeCustomVerts(Out,Layer+1,Handle,Vertices,Indices,nullptr,0,0);
  return Layer+1;
 }
 TAttribute<FDirectorVisionState> State;
};
}
void SDirectorVision::Construct(const FArguments& Args)
{
 State=Args._State;SetVisibility(EVisibility::HitTestInvisible);
 ChildSlot[SNew(SOverlay)
  +SOverlay::Slot()[SNew(SBackgroundBlur).BlurStrength_Lambda([this]{return State.Get().Blur*24.f;}).bApplyAlphaToBlur(false)]
  +SOverlay::Slot()[SNew(SEyeSurface).State(State)]];
}
