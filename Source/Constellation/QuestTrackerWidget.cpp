// Fill out your copyright notice in the Description page of Project Settings.


#include "QuestTrackerWidget.h"
#include "QuestSubsystem.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Engine/Font.h"
#include "QuestTrackerPresentation.h"
#include "MinimapWidget.h"
#include "MinimapWorldSubsystem.h"
#include "UObject/ConstructorHelpers.h"
#include "Framework/Application/SlateApplication.h"
#include "Fonts/FontMeasure.h"
#include "Rendering/SlateRenderer.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"

// Code-native vector artwork: no baked text, fixed-resolution border or full-screen texture.
class SStarlightQuestTracker : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SStarlightQuestTracker){} SLATE_ARGUMENT(UQuestTrackerWidget*,Owner) SLATE_END_ARGS()
 void Construct(const FArguments& Args)
 {
  Owner=Args._Owner;
  const FLinearColor Ivory(.94f,.90f,.80f),Gold(.88f,.69f,.35f);
  ChildSlot
  [SNew(SBox).WidthOverride_Lambda([this]{return Width();})
   .Padding(FMargin(40,6,12,16))
   [SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()
    [SAssignNew(Title,STextBlock).Font(Args._Owner->TitleFont).ColorAndOpacity(Ivory)
     .WrapTextAt_Lambda([this]{return Width()-52;}).WrappingPolicy(ETextWrappingPolicy::AllowPerCharacterWrapping)
     .ShadowOffset(FVector2D(0,1)).ShadowColorAndOpacity(FLinearColor(0,0,0,.65f))]
    +SVerticalBox::Slot().AutoHeight().Padding(0,9,0,0)
    [SNew(SHorizontalBox)
     +SHorizontalBox::Slot().FillWidth(1)
     [SAssignNew(Objective,STextBlock).Font(Args._Owner->ObjectiveFont).ColorAndOpacity(Ivory)
      .WrapTextAt_Lambda([this]{return FMath::Max(100.f,Width()-52-CountWidth());})
      .WrappingPolicy(ETextWrappingPolicy::AllowPerCharacterWrapping).LineHeightPercentage(1.15f)
      .ShadowOffset(FVector2D(0,1)).ShadowColorAndOpacity(FLinearColor(0,0,0,.65f))]
     +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Bottom)
     [SAssignNew(Quantity,STextBlock).Font(Args._Owner->ObjectiveFont).ColorAndOpacity(Gold)
      .Margin(FMargin(8,0,0,0)).Visibility(EVisibility::Collapsed)]
    ]
   ]
  ];
  SetVisibility(EVisibility::Collapsed);
 }
 void Update(const FQuestDisplayInfo& Info)
 {
  // No recreation, opacity reset, timer or animation on repeated quest events.
  if(!Title->GetText().EqualTo(Info.Title))Title->SetText(Info.Title);
  if(!Objective->GetText().EqualTo(Info.CurrentObjectiveText))Objective->SetText(Info.CurrentObjectiveText);
  const FText Count=QuestTrackerPresentation::QuantityText(Info);
  if(!Quantity->GetText().EqualTo(Count))Quantity->SetText(Count);
  Quantity->SetVisibility(Count.IsEmpty()?EVisibility::Collapsed:EVisibility::HitTestInvisible);
  SetVisibility(Info.bVisible&&Info.State==EQuestState::Progressed?EVisibility::HitTestInvisible:EVisibility::Collapsed);
 }
 virtual int32 OnPaint(const FPaintArgs& Args,const FGeometry& G,const FSlateRect& Clip,FSlateWindowElementList& Out,int32 Layer,const FWidgetStyle& Style,bool Enabled)const override
 {
  const FVector2f Size(G.GetLocalSize());
  const FSlateBrush* White=FCoreStyle::Get().GetBrush("WhiteBrush");
  const auto Resource=FSlateApplication::Get().GetRenderer()->GetResourceHandle(*White);
  const FLinearColor Tint=Style.GetColorAndOpacityTint()*White->GetTint(Style);
  TArray<FSlateVertex> Vertices;TArray<SlateIndex> Indices;
  auto Vertex=[&](FVector2f P,FLinearColor Color)
  {Vertices.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(G.GetAccumulatedRenderTransform(),P,FVector2f(.5f),(Color*Tint).ToFColor(true)));};
  // Gentle navy wash with transparent edges; no hard rectangular panel outline.
  constexpr int32 Columns=8,Rows=6;
  for(int32 Y=0;Y<=Rows;++Y)for(int32 X=0;X<=Columns;++X)
  {
   const float U=float(X)/Columns,V=float(Y)/Rows;
   const float Alpha=.48f*FMath::Min(U*8,1.f)*FMath::Min(V*8,1.f)*FMath::Pow(1-U,1.1f)*FMath::Pow(1-V,1.1f);
   Vertex(FVector2f(Size.X*U,Size.Y*V),FLinearColor(.008f,.021f,.032f,Alpha));
   if(X<Columns&&Y<Rows){const SlateIndex A=Y*(Columns+1)+X,B=A+Columns+1;Indices.Append({A,SlateIndex(A+1),B,SlateIndex(A+1),SlateIndex(B+1),B});}
  }
  FSlateDrawElement::MakeCustomVerts(Out,Layer,Resource,Vertices,Indices,nullptr,0,0);
  Vertices.Reset();Indices.Reset();
  const FVector2f Center(16,6+Title->GetDesiredSize().Y*.5f);
  const float ObjectiveMiddle=6+Title->GetDesiredSize().Y+9+Objective->GetDesiredSize().Y*.5f;
  FSlateDrawElement::MakeLines(Out,Layer+1,G.ToPaintGeometry(),{Center+FVector2f(0,12),FVector2f(16,ObjectiveMiddle),FVector2f(31,ObjectiveMiddle)},ESlateDrawEffect::None,FLinearColor(.76f,.57f,.25f,.85f)*Style.GetColorAndOpacityTint(),true,.85f);
  for(int32 I=0;I<16;++I)
  {
   auto Point=[&](int32 J){const float A=-PI*.5f+J*PI/8;const float R=J%2?2.1f:J%4?5.f:10.f;return Center+FVector2f(FMath::Cos(A),FMath::Sin(A))*R;};
   const SlateIndex Base=Vertices.Num();
   Vertex(Center,FLinearColor(.99f,.94f,.76f));
   const FLinearColor Facet=I%2?FLinearColor(.68f,.45f,.17f):FLinearColor(.94f,.74f,.37f);
   Vertex(Point(I),Facet);Vertex(Point((I+1)%16),Facet);
   Indices.Append({Base,SlateIndex(Base+1),SlateIndex(Base+2)});
  }
  FSlateDrawElement::MakeCustomVerts(Out,Layer+2,Resource,Vertices,Indices,nullptr,0,0);
  return SCompoundWidget::OnPaint(Args,G,Clip,Out,Layer+3,Style,Enabled);
 }
private:
 float Width()const{return Owner.IsValid()?FMath::Clamp(Owner->TrackerWidth,280.f,420.f):310;}
 float CountWidth()const
 {
  if(!Quantity.IsValid()||Quantity->GetText().IsEmpty()||!Owner.IsValid())return 0;
  return FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(Quantity->GetText(),Owner->ObjectiveFont).X+8;
 }
 TWeakObjectPtr<UQuestTrackerWidget> Owner;
 TSharedPtr<STextBlock> Title,Objective,Quantity;
};

UQuestTrackerWidget::UQuestTrackerWidget(const FObjectInitializer& Initializer):Super(Initializer)
{
 static ConstructorHelpers::FObjectFinder<UFont> Font(TEXT("/Game/Constellation/UI/RegionTitle/F_RegionMyeongjo.F_RegionMyeongjo"));
 TitleFont=Font.Succeeded()?FSlateFontInfo(Font.Object,20,FName("Regular")):FCoreStyle::GetDefaultFontStyle("Regular",20);
 ObjectiveFont=FCoreStyle::GetDefaultFontStyle("Regular",16);
 SetIsFocusable(false);
 DisplayInfo.bVisible=false;
}

TSharedRef<SWidget> UQuestTrackerWidget::RebuildWidget()
{
 // Initialize the existing BP widget tree for its refresh event but do not mount
 // its prototype panel (including Progress/MaxProgress) in the rendered hierarchy.
 Super::RebuildWidget();
 TSharedRef<SWidget> Result=SNew(SOverlay).Visibility(EVisibility::HitTestInvisible)
 +SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Top)
 [SNew(SBox).Padding_Lambda([this]{const FVector2D P=GetTrackerOrigin();return FMargin(P.X,P.Y,0,0);})
  [SAssignNew(Presentation,SStarlightQuestTracker).Owner(this)]];
 Presentation->Update(DisplayInfo);
 return Result;
}

void UQuestTrackerWidget::ReleaseSlateResources(bool bReleaseChildren)
{
 Super::ReleaseSlateResources(bReleaseChildren);Presentation.Reset();
}

FText UQuestTrackerWidget::GetQuantityLabel()const{return QuestTrackerPresentation::QuantityText(DisplayInfo);}
bool UQuestTrackerWidget::IsTrackerPresented()const{return DisplayInfo.bVisible&&DisplayInfo.State==EQuestState::Progressed;}
FVector2D UQuestTrackerWidget::GetTrackerContentSize()const{return Presentation.IsValid()?Presentation->GetDesiredSize():FVector2D::ZeroVector;}
FVector2D UQuestTrackerWidget::GetTrackerOrigin()const
{
 const UMinimapWorldSubsystem* Map=GetWorld()?GetWorld()->GetSubsystem<UMinimapWorldSubsystem>():nullptr;
 const UMinimapWidget* Widget=Map?Map->GetHUDWidget():nullptr;
 const FVector2D Margin=Widget?Widget->SafeMargin:FVector2D(32,28);
 const float Diameter=Widget?FMath::Clamp(Widget->Diameter,180.f,360.f):250;
 // Keep a stable gap below the compass decoration; the map has no footer labels.
 return FVector2D(Margin.X,Margin.Y+Diameter+33+FMath::Max(0.f,MinimapGap));
}

void UQuestTrackerWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (const UWorld* World = GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				Sub->OnQuestStateChanged.AddUniqueDynamic(this, &UQuestTrackerWidget::HandleQuestStateChanged);
				Sub->OnQuestProgressChanged.AddUniqueDynamic(this, &UQuestTrackerWidget::HandleQuestProgressChanged);
				Sub->OnQuestInnerProgressChanged.AddUniqueDynamic(this, &UQuestTrackerWidget::HandleQuestInnerProgressChanged);
				Sub->OnTrackedQuestChanged.AddUniqueDynamic(this, &UQuestTrackerWidget::HandleTrackedQuestChanged);
			}
		}
	}

	RefreshTracker();
	SetVisibility(ESlateVisibility::HitTestInvisible);
}

void UQuestTrackerWidget::NativeDestruct()
{
	if (const UWorld* World = GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				Sub->OnQuestStateChanged.RemoveDynamic(this, &UQuestTrackerWidget::HandleQuestStateChanged);
				Sub->OnQuestProgressChanged.RemoveDynamic(this, &UQuestTrackerWidget::HandleQuestProgressChanged);
				Sub->OnQuestInnerProgressChanged.RemoveDynamic(this, &UQuestTrackerWidget::HandleQuestInnerProgressChanged);
				Sub->OnTrackedQuestChanged.RemoveDynamic(this, &UQuestTrackerWidget::HandleTrackedQuestChanged);
			}
		}
	}

	Super::NativeDestruct();
}

void UQuestTrackerWidget::RefreshTracker()
{
	FQuestDisplayInfo Info;

	if (const UWorld* World = GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				Info = Sub->GetTrackedQuestDisplayInfo();
			}
		}
	}

	OnTrackerRefreshed(Info);
	DisplayInfo=Info;
	if(Presentation.IsValid())Presentation->Update(DisplayInfo);
}

void UQuestTrackerWidget::HandleQuestStateChanged(FName QuestID, EQuestState OldState, EQuestState NewState)
{
	RefreshTracker();
}

void UQuestTrackerWidget::HandleQuestProgressChanged(FName QuestID, int32 NewProgress)
{
	RefreshTracker();
}

void UQuestTrackerWidget::HandleQuestInnerProgressChanged(FName QuestID, int32 NewInnerProgress)
{
	RefreshTracker();
}

void UQuestTrackerWidget::HandleTrackedQuestChanged(FName NewTrackedQuestID)
{
	RefreshTracker();
}
