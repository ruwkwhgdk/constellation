#include "StarlightPlayerHUDWidget.h"
#include "CombatAbilitySystem.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Components/Widget.h"
#include "UObject/ConstructorHelpers.h"
#include "UObject/UnrealType.h"
#include "Widgets/SLeafWidget.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Layout/SBox.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Styling/CoreStyle.h"
#include "Framework/Application/SlateApplication.h"
#include "Rendering/SlateRenderer.h"
#include "Rendering/DrawElements.h"

namespace
{
 class SStarlightVitals : public SLeafWidget
 {
 public:
  SLATE_BEGIN_ARGS(SStarlightVitals){} SLATE_ARGUMENT(UStarlightPlayerHUDWidget*,Owner) SLATE_END_ARGS()
  void Construct(const FArguments& Args)
  {
   Owner=Args._Owner;SetVisibility(EVisibility::HitTestInvisible);
   Nebula.SetResourceObject(Args._Owner->GetNebulaTexture());Nebula.DrawAs=ESlateBrushDrawType::Image;
  }
  virtual FVector2D ComputeDesiredSize(float) const override{return FVector2D(560,120);}
  virtual bool ComputeVolatility() const override{return true;}
  virtual int32 OnPaint(const FPaintArgs&,const FGeometry& Geometry,const FSlateRect&,FSlateWindowElementList& Out,int32 Layer,const FWidgetStyle& Style,bool)const override
  {
   const UStarlightPlayerHUDWidget* HUD=Owner.Get();if(!HUD)return Layer;
   const FLinearColor Tint=Style.GetColorAndOpacityTint(),Gold(.95f,.78f,.39f),Ivory(.98f,.93f,.77f);
   auto Box=[&](FVector2f Position,FVector2f Size,const FSlateBrush* Brush,FLinearColor Color,int32 Extra=0)
   {FSlateDrawElement::MakeBox(Out,Layer+Extra,Geometry.ToPaintGeometry(Size,FSlateLayoutTransform(Position)),Brush,ESlateDrawEffect::None,Color*Tint*Brush->GetTint(Style));};
   auto Line=[&](const TArray<FVector2f>& Points,FLinearColor Color,float Width=1.f)
   {FSlateDrawElement::MakeLines(Out,Layer+3,Geometry.ToPaintGeometry(),Points,ESlateDrawEffect::None,Color*Tint,true,Width);};
   const FVector2f Center(64,60);
   Box(FVector2f(22,18),FVector2f(84,84),&Nebula,FLinearColor(1,1,1,.28f));
   auto Arc=[&](float Radius,float Begin,float End,FLinearColor Color,float Width)
   {
    TArray<FVector2f> Points;for(int32 I=0;I<=64;++I){float Angle=FMath::Lerp(Begin,End,I/64.f);Points.Add(Center+FVector2f(FMath::Cos(Angle),FMath::Sin(Angle))*Radius);}Line(Points,Color,Width);
   };
   Arc(34,0,2*PI,Gold*.7f,.7f);Arc(45,PI*.5f,PI*1.5f,Gold,1.5f);
   FSlateRoundedBoxBrush Dot(FLinearColor::White,3.f);
   for(const FVector2f Point:{Center+FVector2f(0,-45),Center+FVector2f(-45,0),Center+FVector2f(0,45)})Box(Point-FVector2f(2.5f),FVector2f(5),&Dot,Gold,4);
   const FLinearColor StarColor=HUD->GetStarColor();
   if(HUD->IsFailureFeedbackActive()||HUD->GetHealthRatio()<=HUD->LowHealthThreshold)
   {
    for(int32 I=0;I<4;++I){FLinearColor Halo=StarColor;Halo.A=.16f-I*.03f;Arc(27+I*2.5f,0,2*PI,Halo,3.f);}
   }
   // Faceted, solid eight-point star. Only its vertices move during rejection feedback.
   const FVector2f StarCenter=Center+FVector2f(HUD->GetStarOffset());
   TArray<FSlateVertex> Vertices;TArray<SlateIndex> Indices;
   const auto Transform=Geometry.GetAccumulatedRenderTransform();
   for(int32 I=0;I<16;++I)
   {
    auto Point=[&](int32 Index){float Angle=-PI*.5f+Index*PI/8;float Radius=Index%2?4.f:Index%4?15.f:26.f;return StarCenter+FVector2f(FMath::Cos(Angle),FMath::Sin(Angle))*Radius;};
    FLinearColor Facet=StarColor*(I%2?.66f:1.f);Facet.A=StarColor.A;
    const SlateIndex Base=Vertices.Num();
    Vertices.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(Transform,StarCenter,FVector2f(.5f),(Ivory*Tint).ToFColor(true)));
    Vertices.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(Transform,Point(I),FVector2f(.5f),(Facet*Tint).ToFColor(true)));
    Vertices.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(Transform,Point((I+1)%16),FVector2f(.5f),(Facet*Tint).ToFColor(true)));
    Indices.Append({Base,static_cast<SlateIndex>(Base+1),static_cast<SlateIndex>(Base+2)});
   }
   const FSlateResourceHandle White=FSlateApplication::Get().GetRenderer()->GetResourceHandle(*FCoreStyle::Get().GetBrush("WhiteBrush"));
   FSlateDrawElement::MakeCustomVerts(Out,Layer+5,White,Vertices,Indices,nullptr,0,0);
   auto Bar=[&](FVector2f Position,FVector2f Size,float Ratio,float Trail,FLinearColor Fill,bool EmptyStamina)
   {
    FSlateRoundedBoxBrush Frame(FLinearColor(.012f,.02f,.026f,.68f),Size.Y*.5f,EmptyStamina?FLinearColor(.39f,.44f,.49f):Gold,1.f);
    FSlateRoundedBoxBrush FillBrush(FLinearColor::White,(Size.Y-4)*.5f);
    Box(Position,Size,&Frame,FLinearColor::White,1);
    if(Trail>Ratio)Box(Position+FVector2f(2),FVector2f((Size.X-4)*Trail,Size.Y-4),&FillBrush,FLinearColor(.55f,.11f,.13f,.6f),2);
    if(Ratio>0)Box(Position+FVector2f(2),FVector2f(FMath::Max(1.f,(Size.X-4)*Ratio),Size.Y-4),&FillBrush,Fill,3);
    if(Ratio>0){FLinearColor Highlight=FLinearColor::White;Highlight.A=.23f;Box(Position+FVector2f(4,3),FVector2f(FMath::Max(0.f,(Size.X-8)*Ratio),1),FCoreStyle::Get().GetBrush("WhiteBrush"),Highlight,4);}
   };
   Bar(FVector2f(142,35),FVector2f(400,17),HUD->GetHealthRatio(),HUD->GetDamageTrailRatio(),FLinearColor(.96f,.12f,.14f),false);
   Bar(FVector2f(142,70),FVector2f(360,12),HUD->GetStaminaRatio(),0,FLinearColor(.015f,.76f,.63f),HUD->GetStaminaRatio()<=0);
   return Layer+5;
  }
 private:
  TWeakObjectPtr<UStarlightPlayerHUDWidget> Owner;
  FSlateBrush Nebula;
 };
}
TArray<TWeakObjectPtr<UStarlightPlayerHUDWidget>> UStarlightPlayerHUDWidget::ActiveHUDs;
UStarlightPlayerHUDWidget::UStarlightPlayerHUDWidget(const FObjectInitializer& Init):Super(Init)
{
 static ConstructorHelpers::FObjectFinder<UTexture2D> Texture(TEXT("/Game/Constellation/UI/RegionTitle/T_RegionNebula.T_RegionNebula"));NebulaTexture=Texture.Object;SetIsFocusable(false);
}
TSharedRef<SWidget> UStarlightPlayerHUDWidget::RebuildWidget()
{
 TSharedRef<SWidget> Existing=Super::RebuildWidget();CollapseLegacyBars();
 return SNew(SOverlay).Visibility(EVisibility::SelfHitTestInvisible)
 +SOverlay::Slot()[Existing]
 +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(FMargin(SafePadding.X,0,SafePadding.X,SafePadding.Y))
 [SNew(SBox).WidthOverride(560).HeightOverride(120).Visibility(EVisibility::HitTestInvisible)[SNew(SStarlightVitals).Owner(this)]];
}
void UStarlightPlayerHUDWidget::CollapseLegacyBars()
{
 for(FName Name:{FName("HPProgressBar"),FName("StaminaProgressBar")})if(UWidget* Widget=GetWidgetFromName(Name))Widget->SetVisibility(ESlateVisibility::Collapsed);
}
void UStarlightPlayerHUDWidget::DetachLegacyBarBinding(UObject* Stats)
{
 const FName FunctionName(TEXT("Update HP UI"));
 if(!Stats||!FindFunction(FunctionName))return;
 if(const FMulticastDelegateProperty* Property=FindFProperty<FMulticastDelegateProperty>(Stats->GetClass(),TEXT("OnHPChanged")))
 {
  FScriptDelegate Binding;Binding.BindUFunction(this,FunctionName);
  Property->RemoveDelegate(Binding,Stats,Property->ContainerPtrToValuePtr<void>(Stats));
 }
}
float UStarlightPlayerHUDWidget::ReadNumber(const UObject* Object,FName Name,float DefaultValue)
{
 if(!Object)return DefaultValue;
 const FNumericProperty* Property=FindFProperty<FNumericProperty>(Object->GetClass(),Name);if(!Property)return DefaultValue;
 const void* Value=Property->ContainerPtrToValuePtr<void>(Object);
 return Property->IsFloatingPoint()?Property->GetFloatingPointPropertyValue(Value):Property->GetSignedIntPropertyValue(Value);
}
UObject* UStarlightPlayerHUDWidget::FindLegacyStats(AActor* Actor)
{
 if(!Actor)return nullptr;
 TInlineComponentArray<UActorComponent*> Components(Actor);
 for(UActorComponent* Component:Components)if(Component->GetClass()->GetName().Contains(TEXT("Ac_Stats")))return Component;
 return nullptr;
}
void UStarlightPlayerHUDWidget::UnbindResources()
{
 if(UCombatAbilitySystem* Ability=Combat.Get()){Ability->OnDamageAccepted.Remove(DamageHandle);Ability->OnStaminaActionRejected.Remove(RejectedHandle);}
 DamageHandle.Reset();RejectedHandle.Reset();Combat.Reset();LegacyStats.Reset();ResourcePawn.Reset();bHaveSample=false;bPendingDamage=false;
}
void UStarlightPlayerHUDWidget::RebindResources()
{
 APawn* Pawn=GetOwningPlayerPawn();if(Pawn==ResourcePawn.Get()&&(LegacyStats.IsValid()||Combat.IsValid()))return;
 UnbindResources();ResourcePawn=Pawn;FailureElapsed=-1;FailureCooldown=0;
 if(Pawn)
 {
  LegacyStats=FindLegacyStats(Pawn);
  if(!LegacyStats.IsValid())if(auto* Ability=Pawn->FindComponentByClass<UCombatAbilitySystem>())
  {
   Combat=Ability;
   DamageHandle=Ability->OnDamageAccepted.AddWeakLambda(this,[this](const FCombatAcceptedDamage& Damage){if(Damage.AppliedDamage>0)RecordDamage();});
   RejectedHandle=Ability->OnStaminaActionRejected.AddWeakLambda(this,[this]{StartFailureFeedback();});
  }
 }
}
void UStarlightPlayerHUDWidget::SampleResources(float Delta)
{
 float HP=0,MaxHP=0,Stamina=0,MaxStamina=0;
 if(UObject* Stats=LegacyStats.Get())
 {HP=ReadNumber(Stats,TEXT("CurrentHP"));MaxHP=ReadNumber(Stats,TEXT("MaxHP"));Stamina=ReadNumber(Stats,TEXT("CurrentStamina"));MaxStamina=ReadNumber(Stats,TEXT("MaxStamina"));}
 else if(UCombatAbilitySystem* Ability=Combat.Get())
 {HP=Ability->GetHealth();MaxHP=Ability->GetMaxHealth();Stamina=Ability->GetStamina();MaxStamina=Ability->GetMaxStamina();}
 const float NewHP=MaxHP>0?FMath::Clamp(HP/MaxHP,0.f,1.f):0,NewST=MaxStamina>0?FMath::Clamp(Stamina/MaxStamina,0.f,1.f):0;
 const bool MaxChanged=!FMath::IsNearlyEqual(MaxHP,LastMaxHealth);
 if(!bHaveSample||MaxChanged){DamageTrailRatio=TrailStart=NewHP;TrailElapsed=1;}
 else if(bPendingDamage&&NewHP<HealthRatio){TrailStart=FMath::Max(DamageTrailRatio,HealthRatio);DamageTrailRatio=TrailStart;TrailElapsed=0;}
 else if(!FMath::IsNearlyEqual(NewHP,HealthRatio)){DamageTrailRatio=TrailStart=NewHP;TrailElapsed=1;}
 HealthRatio=NewHP;StaminaRatio=NewST;LastMaxHealth=MaxHP;bHaveSample=true;bPendingDamage=false;
 TrailElapsed+=Delta;
 DamageTrailRatio=FMath::Lerp(TrailStart,HealthRatio,FMath::Clamp((TrailElapsed-.15f)/.6f,0.f,1.f));
}
void UStarlightPlayerHUDWidget::RecordDamage(){if(bActive&&bHaveSample)bPendingDamage=true;}
void UStarlightPlayerHUDWidget::StartFailureFeedback()
{
 if(bActive&&!IsFailureFeedbackActive()&&FailureCooldown<=0){FailureElapsed=0;FailureCooldown=0;}
}
void UStarlightPlayerHUDWidget::NotifyDamage(AActor* Source)
{
 if(!Source)return;const auto Snapshot=ActiveHUDs;
 for(const auto& Weak:Snapshot)if(auto* HUD=Weak.Get()){HUD->RebindResources();if(HUD->ResourcePawn.Get()==Source)HUD->RecordDamage();}
}
void UStarlightPlayerHUDWidget::NotifyStaminaRejected(AActor* Source)
{
 if(!Source)return;const auto Snapshot=ActiveHUDs;
 for(const auto& Weak:Snapshot)if(auto* HUD=Weak.Get()){HUD->RebindResources();if(HUD->ResourcePawn.Get()==Source)HUD->StartFailureFeedback();}
}
void UStarlightPlayerHUDWidget::NotifyLegacySprintRejected(AActor* Source)
{
 UObject* Stats=FindLegacyStats(Source);if(!Stats||ReadNumber(Stats,TEXT("CurrentStamina"),1)>0)return;
 const FObjectPropertyBase* Property=FindFProperty<FObjectPropertyBase>(Source->GetClass(),TEXT("CurrentAttackComponent"));
 UObject* Attack=Property?Property->GetObjectPropertyValue_InContainer(Source):nullptr;if(!Attack)return;
 const FBoolProperty* Attacking=FindFProperty<FBoolProperty>(Attack->GetClass(),TEXT("IsAttacking"));
 if(Attacking&&!Attacking->GetPropertyValue_InContainer(Attack))NotifyStaminaRejected(Source);
}
FVector2D UStarlightPlayerHUDWidget::GetStarOffset()const
{return IsFailureFeedbackActive()?FVector2D(2.5f*FMath::Sin(FailureElapsed/.35f*4*PI),0):FVector2D::ZeroVector;}
FLinearColor UStarlightPlayerHUDWidget::GetStarColor()const
{
 if(IsFailureFeedbackActive())
 {
  const float Flash=.5f+.5f*FMath::Sin(FailureElapsed/.35f*4*PI);
  return FMath::Lerp(FLinearColor(.76f,.22f,.025f,1),FLinearColor(1,.58f,.12f,1),Flash);
 }
 if(HealthRatio<=LowHealthThreshold)
 {float Pulse=.5f+.5f*FMath::Sin(VisualTime/FMath::Max(.1f,LowHealthPulseSeconds)*2*PI);return FMath::Lerp(FLinearColor(.63f,.06f,.045f),FLinearColor(1,.29f,.17f),Pulse);}
 return FLinearColor(1,.75f,.32f);
}
void UStarlightPlayerHUDWidget::AdvanceVisuals(float DeltaSeconds)
{
 if(!bActive)return;const float Delta=FMath::Max(0.f,DeltaSeconds);VisualTime+=Delta;
 RebindResources();SampleResources(Delta);
 if(IsFailureFeedbackActive())
 {FailureElapsed+=Delta;if(FailureElapsed>=.35f){const float Excess=FailureElapsed-.35f;FailureElapsed=-1;FailureCooldown=FMath::Max(0.f,.15f-Excess);}}
 else FailureCooldown=FMath::Max(0.f,FailureCooldown-Delta);
}
void UStarlightPlayerHUDWidget::TickVisuals()
{
 if(UWorld* World=GetWorld()){double Now=World->GetTimeSeconds();float Delta=FMath::Max(0.0,Now-LastTickTime);LastTickTime=Now;AdvanceVisuals(Delta);}
}
void UStarlightPlayerHUDWidget::NativeConstruct()
{
 DetachLegacyBarBinding(LegacyBindingStats.Get());LegacyBindingStats=FindLegacyStats(GetOwningPlayerPawn());
 Super::NativeConstruct();DetachLegacyBarBinding(LegacyBindingStats.Get());CollapseLegacyBars();SetIsFocusable(false);SetVisibility(ESlateVisibility::SelfHitTestInvisible);
 UnbindResources();bActive=true;VisualTime=0;ActiveHUDs.RemoveAll([](const auto& Weak){return !Weak.IsValid();});ActiveHUDs.AddUnique(this);RebindResources();SampleResources(0);
 if(UWorld* World=GetWorld()){LastTickTime=World->GetTimeSeconds();World->GetTimerManager().SetTimer(VisualTimer,this,&UStarlightPlayerHUDWidget::TickVisuals,1.f/60.f,true);}
}
void UStarlightPlayerHUDWidget::NativeDestruct()
{
 if(UWorld* World=GetWorld())World->GetTimerManager().ClearTimer(VisualTimer);
 DetachLegacyBarBinding(LegacyBindingStats.Get());LegacyBindingStats.Reset();
 FailureElapsed=-1;FailureCooldown=0;
 bActive=false;UnbindResources();ActiveHUDs.RemoveAll([this](const auto& Weak){return !Weak.IsValid()||Weak.Get()==this;});Super::NativeDestruct();
}
