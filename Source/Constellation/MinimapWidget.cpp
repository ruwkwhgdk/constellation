#include "MinimapWidget.h"
#include "MinimapWorldSubsystem.h"
#include "Engine/Font.h"
#include "Engine/World.h"
#include "Framework/Application/SlateApplication.h"
#include "Fonts/FontMeasure.h"
#include "Rendering/DrawElements.h"
#include "Rendering/SlateRenderer.h"
#include "Styling/CoreStyle.h"
#include "UObject/ConstructorHelpers.h"
#include "Widgets/SLeafWidget.h"
#include "Widgets/SOverlay.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#endif

namespace MinimapPaint
{
 constexpr int32 CircleSegments=96;
 FVector2f Project(FVector2D Delta,float NorthYaw,float Scale)
 {
  const double A=FMath::DegreesToRadians(NorthYaw),C=FMath::Cos(A),S=FMath::Sin(A);
  return FVector2f((-Delta.X*S+Delta.Y*C)*Scale,-(Delta.X*C+Delta.Y*S)*Scale);
 }
 TArray<FVector2f> Circle(float Radius)
 {
  TArray<FVector2f> Result;Result.Reserve(CircleSegments);
  for(int32 I=0;I<CircleSegments;++I){const float A=2*PI*I/CircleSegments;Result.Add(FVector2f(FMath::Cos(A),FMath::Sin(A))*Radius);}
  return Result;
 }
 // Convex polygon clipping against an inscribed 96-sided circle. Every output vertex
 // stays within the true radius; unlike a rectangular Slate clip, corners cannot leak.
 TArray<FVector2f> ClipCircle(TArray<FVector2f> Polygon,float Radius)
 {
  const float Inner=Radius*FMath::Cos(PI/CircleSegments);
  bool bInside=true;for(const auto& P:Polygon)bInside&=P.SizeSquared()<=Inner*Inner;
  if(bInside)return Polygon;
  for(int32 I=0;I<CircleSegments&&!Polygon.IsEmpty();++I)
  {
   const float A=2*PI*(I+.5f)/CircleSegments;
   const FVector2f Normal(FMath::Cos(A),FMath::Sin(A));
   TArray<FVector2f> Next;Next.Reserve(Polygon.Num()+1);
   FVector2f Previous=Polygon.Last();float PreviousDistance=FVector2f::DotProduct(Previous,Normal)-Inner;
   for(const FVector2f Current:Polygon)
   {
    const float Distance=FVector2f::DotProduct(Current,Normal)-Inner;
    if((Distance<=0)!=(PreviousDistance<=0))Next.Add(Previous+(Current-Previous)*(PreviousDistance/(PreviousDistance-Distance)));
    if(Distance<=0)Next.Add(Current);
    Previous=Current;PreviousDistance=Distance;
   }
   Polygon=MoveTemp(Next);
  }
  return Polygon;
 }

 class SMinimap : public SLeafWidget
 {
 public:
  SLATE_BEGIN_ARGS(SMinimap){} SLATE_ARGUMENT(TWeakObjectPtr<UMinimapWidget>,Owner) SLATE_END_ARGS()
  void Construct(const FArguments& Args){Owner=Args._Owner;SetVisibility(EVisibility::HitTestInvisible);}
  virtual bool ComputeVolatility()const override{return true;}
  virtual FVector2D ComputeDesiredSize(float)const override
  {const auto* W=Owner.Get();const float D=W?FMath::Clamp(W->Diameter,180.f,360.f):250;return FVector2D(D+32,D+40);}
  virtual int32 OnPaint(const FPaintArgs&,const FGeometry& Geometry,const FSlateRect&,FSlateWindowElementList& Elements,int32 Layer,const FWidgetStyle& Style,bool)const override
  {
   const auto* W=Owner.Get();const auto* World=W?W->GetWorld():nullptr;
   const auto* Sub=World?World->GetSubsystem<UMinimapWorldSubsystem>():nullptr;
   const auto* Region=Sub?Sub->GetRegion():nullptr;const auto* Floor=Sub?Sub->GetFloor():nullptr;
   if(!Region||Region->ViewRadius<=0)return Layer;
   // Keep the compass/player shell visible while ground classification is unavailable.
   FMinimapFloorData Unknown;
   if(!Floor||!Floor->IsValid())
   {
    Unknown.Width=Unknown.Height=1;Unknown.Cells.Add(0);
    Floor=&Unknown;
   }
   const float R=FMath::Clamp(W->Diameter,180.f,360.f)*.5f,Scale=R/Region->ViewRadius;
   const FVector2f Center(R+16,R+23);const FVector2D Pawn(Sub->GetPawnPosition());
   const FLinearColor Tint=Style.GetColorAndOpacityTint(),Gold(.87f,.66f,.30f),Ivory(.94f,.90f,.79f);
   const auto* Brush=FCoreStyle::Get().GetBrush("WhiteBrush");
   const auto Resource=FSlateApplication::Get().GetRenderer()->GetResourceHandle(*Brush);
   TArray<FSlateVertex> Vertices;TArray<SlateIndex> Indices;
   auto Flush=[&]()
   {
    if(!Indices.IsEmpty())FSlateDrawElement::MakeCustomVerts(Elements,Layer,Resource,Vertices,Indices,nullptr,0,0);
    Vertices.Reset();Indices.Reset();++Layer;
   };
   auto Polygon=[&](const TArray<FVector2f>& Points,FLinearColor Color)
   {
    if(Points.Num()<3)return;
    if(Vertices.Num()+Points.Num()+1>60000)Flush();
    const int32 Base=Vertices.Num();const FColor VertexColor=(Color*Tint*Brush->GetTint(Style)).ToFColor(true);
    FVector2f Centroid=FVector2f::ZeroVector;for(const auto P:Points)Centroid+=P;Centroid/=Points.Num();
    Vertices.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(Geometry.GetAccumulatedRenderTransform(),Center+Centroid,FVector2f(.5f,.5f),VertexColor));
    for(const auto P:Points)Vertices.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(Geometry.GetAccumulatedRenderTransform(),Center+P,FVector2f(.5f,.5f),VertexColor));
    for(int32 I=0;I<Points.Num();++I){Indices.Add(Base);Indices.Add(Base+I+1);Indices.Add(Base+(I+1)%Points.Num()+1);}
   };
   auto Line=[&](TArray<FVector2f> Points,FLinearColor Color,float Width=1.f)
   {
    for(auto& P:Points)P+=Center;
    FSlateDrawElement::MakeLines(Elements,Layer,Geometry.ToPaintGeometry(),Points,ESlateDrawEffect::None,Color*Tint,true,Width);
   };
   auto Text=[&](const FString& Value,float Y,FLinearColor Color,int32 Size)
   {
    FSlateFontInfo Font=W->LabelFont;Font.Size=Size;
    const FVector2D Extent=FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(Value,Font);
    FSlateDrawElement::MakeText(Elements,Layer,Geometry.ToPaintGeometry(FVector2f(Extent),FSlateLayoutTransform(FVector2f(Center.X-Extent.X*.5f,Y))),Value,Font,ESlateDrawEffect::None,Color*Tint);
   };
   Polygon(Circle(R),FLinearColor(.012f,.025f,.039f,1));Flush();
   // Bound the iteration in world space, including the half-cell overhang.
   const float Reach=Region->ViewRadius+Floor->CellSize;
   const int32 X0=FMath::Clamp(FMath::FloorToInt((Pawn.X-Reach-Floor->Origin.X)/Floor->CellSize),0,Floor->Width-1);
   const int32 X1=FMath::Clamp(FMath::CeilToInt((Pawn.X+Reach-Floor->Origin.X)/Floor->CellSize),0,Floor->Width-1);
   const int32 Y0=FMath::Clamp(FMath::FloorToInt((Pawn.Y-Reach-Floor->Origin.Y)/Floor->CellSize),0,Floor->Height-1);
   const int32 Y1=FMath::Clamp(FMath::CeilToInt((Pawn.Y+Reach-Floor->Origin.Y)/Floor->CellSize),0,Floor->Height-1);
   for(int32 Y=Y0;Y<=Y1;++Y)for(int32 X=X0;X<=X1;++X)
   {
    const int32 Index=Y*Floor->Width+X;
    if(!Floor->Cells[Index]||!Sub->IsDiscovered(*Floor,Index))continue;
    const FVector2D Base=Floor->Origin+FVector2D(X,Y)*Floor->CellSize-Pawn;
    if((Base+FVector2D(Floor->CellSize*.5f)).SizeSquared()>FMath::Square(Reach))continue;
    TArray<FVector2f> Points;
    for(const FVector2D Offset:{FVector2D(0,0),FVector2D(Floor->CellSize,0),FVector2D(Floor->CellSize),FVector2D(0,Floor->CellSize)})Points.Add(Project(Base+Offset,Region->NorthYaw,Scale));
    Polygon(ClipCircle(MoveTemp(Points),R),Floor->Cells[Index]==2?FLinearColor(.46f,.52f,.55f):FLinearColor(.105f,.16f,.20f));
   }
   Flush();
   const float CameraAngle=FMath::DegreesToRadians(Sub->GetCameraYaw()-Region->NorthYaw-90);
   const float HalfFOV=FMath::DegreesToRadians(FMath::Clamp(Sub->GetCameraFOV(),10.f,150.f)*.5f);
   TArray<FVector2f> Wedge{FVector2f::ZeroVector};
   for(int32 I=0;I<=12;++I){const float A=CameraAngle-HalfFOV+2*HalfFOV*I/12;Wedge.Add(FVector2f(FMath::Cos(A),FMath::Sin(A))*38);}
   Polygon(Wedge,FLinearColor(.65f,.75f,.80f,.075f));Flush();
   for(const auto& Marker:Sub->GetMarkers())
   {
    if(Marker.bHidden||(Marker.Kind==EMinimapMarkerKind::Stairs&&!Marker.bConnectionVerified)||(Marker.FloorId!=Floor->FloorId&&Marker.ConnectedFloorId!=Floor->FloorId))continue;
    const FVector2D WorldPosition(Marker.Position);const int32 Index=Floor->IndexAt(WorldPosition);
    if(Index==INDEX_NONE||!Sub->IsDiscovered(*Floor,Index))continue;
    const FVector2f P=Project(WorldPosition-Pawn,Region->NorthYaw,Scale);
    if(P.Size()>R-12)continue;
    if(Marker.Kind==EMinimapMarkerKind::Door)Line({P+FVector2f(-5,3),P+FVector2f(-5,-3),P+FVector2f(5,-3),P+FVector2f(5,3)},Ivory,1.5f);
    else Line({P+FVector2f(-6,5),P+FVector2f(-2,5),P+FVector2f(-2,1),P+FVector2f(2,1),P+FVector2f(2,-3),P+FVector2f(6,-3),P+FVector2f(6,-6)},Ivory,1.5f);
   }
   ++Layer;
   auto Star=[&](FVector2f P,float Size,bool bHollow,FLinearColor Color)
   {
    TArray<FVector2f> Points;
    for(int32 I=0;I<8;++I){const float A=PI*I/4;Points.Add(P+FVector2f(FMath::Cos(A),FMath::Sin(A))*(I%2?Size*.23f:Size));}
    if(bHollow){const FVector2f First=Points[0];Points.Add(First);Line(Points,Color,1.2f);}else{Polygon(Points,Color);Flush();}
   };
   const auto& Objective=Sub->GetObjective();
   if(Objective.bValid)
   {
    FVector2f P=Project(FVector2D(Objective.Position)-Pawn,Region->NorthYaw,Scale);
    const bool bOutside=P.Size()>R-13;const FVector2f Direction=P.GetSafeNormal();
    if(bOutside)P=Direction*(R-13);
    Star(P,8,!Objective.bSameFloor,Gold);
    if(bOutside){const FVector2f Side(-Direction.Y,Direction.X);Line({Direction*(R-3)-Side*3,Direction*(R-1),Direction*(R-3)+Side*3},Gold,1.5f);}
   }
   // Ivory heading marker is always centered; the concave notch faces the rear.
   const FVector2f Forward=Project(FVector2D(FMath::Cos(FMath::DegreesToRadians(Sub->GetHeadingYaw())),FMath::Sin(FMath::DegreesToRadians(Sub->GetHeadingYaw()))),Region->NorthYaw,1);
   const FVector2f Side(-Forward.Y,Forward.X);
   Polygon({Forward*9,-Forward*5+Side*5,-Forward*2,-Forward*5-Side*5},Ivory);Flush();
   for(float Radius:{R+1,R+4}){auto Rim=Circle(Radius);const FVector2f First=Rim[0];Rim.Add(First);Line(Rim,Gold,Radius==R+1?.75f:1.15f);}
   // Static constellation decoration sits strictly outside the information circle.
   for(float Start:{-160.f,24.f})
   {
    for(int32 I=0;I<20;++I)
    {
     const float A=FMath::DegreesToRadians(Start+I*2.8f),B=A+.014f;
     Line({FVector2f(FMath::Cos(A),FMath::Sin(A))*(R+10),FVector2f(FMath::Cos(B),FMath::Sin(B))*(R+10)},FLinearColor(.72f,.53f,.24f,.55f),.7f);
    }
    for(int32 I=0;I<3;++I){const float A=FMath::DegreesToRadians(Start+10+I*19);Star(FVector2f(FMath::Cos(A),FMath::Sin(A))*(R+10),I==1?4:2,false,Gold);}
   }
   Text(TEXT("N"),0,Ivory,12);
   return Layer;
  }
 private:TWeakObjectPtr<UMinimapWidget> Owner;
 };
}

UMinimapWidget::UMinimapWidget(const FObjectInitializer& Initializer):Super(Initializer)
{
 static ConstructorHelpers::FObjectFinder<UFont> Font(TEXT("/Game/Constellation/UI/RegionTitle/F_RegionMyeongjo.F_RegionMyeongjo"));
 LabelFont=Font.Succeeded()?FSlateFontInfo(Font.Object,14,FName("Regular")):FCoreStyle::GetDefaultFontStyle("Regular",14);
 SetIsFocusable(false);SetVisibility(ESlateVisibility::HitTestInvisible);
}
TSharedRef<SWidget> UMinimapWidget::RebuildWidget()
{
 return SNew(SOverlay).Visibility(EVisibility::HitTestInvisible)
 +SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Top)
 .Padding(FMargin(FMath::Max(0.0,SafeMargin.X),FMath::Max(0.0,SafeMargin.Y),0,0))
 [SNew(MinimapPaint::SMinimap).Owner(this)];
}

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMinimapProjectionClipTest,"Constellation.Minimap.ProjectionAndCircularClip",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMinimapProjectionClipTest::RunTest(const FString&)
{
 using namespace MinimapPaint;
 TestTrue(TEXT("World north points up"),Project(FVector2D(10,0),0,1).Equals(FVector2f(0,-10),.001f));
 TestTrue(TEXT("Authored north rotates map"),Project(FVector2D(0,10),90,1).Equals(FVector2f(0,-10),.001f));
 TestTrue(TEXT("World east points right"),Project(FVector2D(0,10),0,1).Equals(FVector2f(10,0),.001f));
 auto Clipped=ClipCircle({FVector2f(7,7),FVector2f(12,7),FVector2f(12,12),FVector2f(7,12)},10);
 TestTrue(TEXT("Corner-straddling cell retains visible sliver"),Clipped.Num()>=3);
 for(const auto P:Clipped)TestTrue(TEXT("No vertex escapes circle"),P.Size()<=10.001f);
 TestTrue(TEXT("Outside cell is discarded"),ClipCircle({FVector2f(11,11),FVector2f(12,11),FVector2f(12,12),FVector2f(11,12)},10).IsEmpty());
 auto Cover=ClipCircle({FVector2f(-20,-20),FVector2f(20,-20),FVector2f(20,20),FVector2f(-20,20)},10);
 TestEqual(TEXT("Covering cell clips to entire aperture"),Cover.Num(),CircleSegments);
 return true;
}
#endif

