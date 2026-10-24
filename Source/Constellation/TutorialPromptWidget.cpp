#include "TutorialPromptWidget.h"
#include "TutorialToastStyle.h"
#include "InteractionPromptComponent.h"
#include "SchoolOpeningSceneActor.h"
#include "CombatAbilitySystem.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Components/SkeletalMeshComponent.h"
#include "UObject/UnrealType.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Text/STextBlock.h"
#include "Styling/CoreStyle.h"
#include "Brushes/SlateRoundedBoxBrush.h"

TArray<TWeakObjectPtr<UTutorialPromptWidget>> UTutorialPromptWidget::ActivePrompts;
namespace
{
 // The legacy gate caller identifies its lesson with this authored image.
 // Do not infer door instructions from F alone: pickup and other interactions share it.
 bool IsGateTutorial(const UTutorialPromptWidget* Widget)
 {
  if(Widget->Action!=ETutorialPromptAction::Auto||!Widget->TargetKeys.Contains(EKeys::F))return false;
  const auto* Property=FindFProperty<FObjectPropertyBase>(Widget->GetClass(),TEXT("Image"));
  const UObject* Image=Property?Property->GetObjectPropertyValue_InContainer(Widget):nullptr;
  return Image&&Image->GetPathName()==TEXT("/Game/Constellation/UI/Art/Tutorial_Interact.Tutorial_Interact");
 }
 bool ReadTutorialBool(const UObject* Object,FName Name)
 {
  if(!Object)return false;
  const FBoolProperty* Property=FindFProperty<FBoolProperty>(Object->GetClass(),Name);
  return Property&&Property->GetPropertyValue_InContainer(Object);
 }
 int32 TutorialMontageInstance(APawn* Pawn)
 {
  const ACharacter* Character=Cast<ACharacter>(Pawn);
  if(!Character||!Character->GetMesh())return INDEX_NONE;
  UAnimInstance* Anim=Character->GetMesh()->GetAnimInstance();
  FAnimMontageInstance* Montage=Anim?Anim->GetActiveMontageInstance():nullptr;
  return Montage&&Montage->IsPlaying()?Montage->GetInstanceID():INDEX_NONE;
 }
}

UTutorialPromptWidget::UTutorialPromptWidget(const FObjectInitializer& ObjectInitializer):Super(ObjectInitializer)
{
 static ConstructorHelpers::FObjectFinder<UTexture2D> Texture(TEXT("/Game/Constellation/UI/Dialogue/T_Tutorial_StarThreadAtlas.T_Tutorial_StarThreadAtlas"));
 Atlas=Texture.Object;
 SetIsFocusable(false);
}
TSharedRef<SWidget> UTutorialPromptWidget::RebuildWidget()
{
 // Build the Blueprint tree so its existing bound widgets and Construct logic survive.
 Super::RebuildWidget();

 PanelBrush=TutorialToastStyle::Brush(Atlas,0); OrnamentBrush=TutorialToastStyle::Brush(Atlas,1);
 const FLinearColor Ivory(.94f,.91f,.79f), Gold(.84f,.66f,.31f);
 KeyBrush=FSlateRoundedBoxBrush(FLinearColor(.015f,.025f,.035f,.7f),6.f,Ivory,1.5f);
 return SNew(SOverlay).Visibility(EVisibility::HitTestInvisible)
 // Bias the centered toast upward by 160 Slate units to clear the interaction row.
 + SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Center).Padding(0,0,48,320)
 [ SAssignNew(ToastBox,SBox).WidthOverride(640).HeightOverride(192)
   [ SNew(SOverlay)
     + SOverlay::Slot()[SNew(SImage).Image(&PanelBrush)]
     + SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Center).Padding(22,0,0,0)
       [SNew(SBox).WidthOverride(30).HeightOverride(136)[SNew(SImage).Image(&OrnamentBrush)]]
     + SOverlay::Slot().Padding(76,34,26,20)
       [SNew(SVerticalBox)
        + SVerticalBox::Slot().AutoHeight()
          [SNew(SHorizontalBox)
           + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
             [SNew(STextBlock).Text(FText::FromString(TEXT("문 앞에서 "))).Font(FCoreStyle::GetDefaultFontStyle("Regular",23)).ColorAndOpacity(Ivory)
              .Visibility_Lambda([this]{return IsGateTutorial(this)?EVisibility::HitTestInvisible:EVisibility::Collapsed;})]
           + SHorizontalBox::Slot().AutoWidth()
             [SNew(SBorder).BorderImage(&KeyBrush).BorderBackgroundColor(FLinearColor::White).Padding(8,3)
               [SNew(STextBlock).Text_Lambda([this]{return GetKeyText();}).Font(FCoreStyle::GetDefaultFontStyle("Bold",23)).ColorAndOpacity(Ivory)]]
           + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(8,0,0,0)
             [SNew(STextBlock).Text(FText::FromString(TEXT("를 눌러"))).Font(FCoreStyle::GetDefaultFontStyle("Regular",23)).ColorAndOpacity(Ivory)]]
        + SVerticalBox::Slot().AutoHeight().Padding(0,12,0,0)
          [SNew(SHorizontalBox)
           + SHorizontalBox::Slot().AutoWidth()[SNew(STextBlock).Text_Lambda([this]{return GetBodyText();}).Font(FCoreStyle::GetDefaultFontStyle("Regular",23)).ColorAndOpacity(Ivory)]
           + SHorizontalBox::Slot().AutoWidth()[SNew(STextBlock).Text_Lambda([this]{return GetVerbText();}).Font(FCoreStyle::GetDefaultFontStyle("Regular",23)).ColorAndOpacity(Gold)]]
        + SVerticalBox::Slot().AutoHeight().Padding(0,6,0,0)
          [SNew(STextBlock).Text_Lambda([this]{return FooterText;}).Font(FCoreStyle::GetDefaultFontStyle("Regular",11)).ColorAndOpacity(Ivory)
           .Visibility_Lambda([this]{return FooterText.IsEmpty()?EVisibility::Collapsed:EVisibility::HitTestInvisible;})]
       ]
   ]
 ];
}
void UTutorialPromptWidget::ReleaseSlateResources(bool bReleaseChildren)
{
 Super::ReleaseSlateResources(bReleaseChildren); ToastBox.Reset();
}
ETutorialPromptAction UTutorialPromptWidget::ResolveAction() const
{
 if(Action!=ETutorialPromptAction::Auto)return Action;
 if(TargetKeys.Contains(EKeys::SpaceBar))return ETutorialPromptAction::Jump;
 if(TargetKeys.Contains(EKeys::LeftMouseButton))return ETutorialPromptAction::Attack;
 if(TargetKeys.Contains(EKeys::W)||TargetKeys.Contains(EKeys::A)||TargetKeys.Contains(EKeys::S)||TargetKeys.Contains(EKeys::D))return ETutorialPromptAction::Movement;
 if(TargetKeys.Contains(EKeys::Z))return ETutorialPromptAction::Transform;
 return ETutorialPromptAction::Auto;
}
FText UTutorialPromptWidget::GetKeyText() const
{
 if(ResolveAction()==ETutorialPromptAction::PickUp||IsGateTutorial(this))
  if(const APawn* Pawn=GetOwningPlayerPawn())
   if(const auto* Interaction=Pawn->FindComponentByClass<UInteractionPromptComponent>())return Interaction->GetInteractionKeyText();
 FString Label;
 for(const FKey& Key:TargetKeys)
 {
  if(!Label.IsEmpty())Label+=TEXT("  ");
  Label+=Key==EKeys::SpaceBar?TEXT("Space"):Key==EKeys::LeftMouseButton?TEXT("좌클릭"):Key.GetDisplayName().ToString();
 }
 return FText::FromString(Label);
}
FText UTutorialPromptWidget::GetBodyText() const
{
 if(IsGateTutorial(this))return FText::FromString(TEXT("문을 "));
 switch(ResolveAction())
 {
 case ETutorialPromptAction::Movement:return FText::FromString(TEXT("주변을 자유롭게 "));
 case ETutorialPromptAction::Jump:return FText::FromString(TEXT("낮은 장애물을 "));
 case ETutorialPromptAction::Attack:return FText::FromString(TEXT("앞에 있는 적을 "));
 case ETutorialPromptAction::Transform:return FText::FromString(TEXT("새로운 모습으로 "));
 case ETutorialPromptAction::PickUp:return FText::FromString(TEXT("물건을 "));
 default:return FText::GetEmpty();
 }
}
FText UTutorialPromptWidget::GetVerbText() const
{
 if(IsGateTutorial(this))return FText::FromString(TEXT("여세요."));
 switch(ResolveAction())
 {
 case ETutorialPromptAction::Movement:return FText::FromString(TEXT("이동하세요."));
 case ETutorialPromptAction::Jump:return FText::FromString(TEXT("뛰어넘으세요."));
 case ETutorialPromptAction::Attack:return FText::FromString(TEXT("공격하세요."));
 case ETutorialPromptAction::Transform:return FText::FromString(TEXT("변신하세요."));
 case ETutorialPromptAction::PickUp:return FText::FromString(TEXT("들 수 있습니다."));
 default:return FText::GetEmpty();
 }
}
FText UTutorialPromptWidget::GetInstructionText() const
{
 return FText::FromString((IsGateTutorial(this)?FString(TEXT("문 앞에서 ")):FString())+GetKeyText().ToString()+TEXT("를 눌러 ")+GetBodyText().ToString()+GetVerbText().ToString());
}
void UTutorialPromptWidget::NativeConstruct()
{
 Super::NativeConstruct();
 UnregisterToast();
 bDismissed=false; bFadingOut=false; bOpeningDeferred=false; Elapsed=FadeElapsed=0;
 SetIsFocusable(false);
 if(UWorld* World=GetWorld())
 {
  World->GetTimerManager().ClearTimer(OpeningTimer);
  World->GetTimerManager().ClearTimer(ToastTimer);
  for(TActorIterator<ASchoolOpeningSceneActor> It(World);It;++It)if(It->bPending)
  {
   bOpeningDeferred=true; SetVisibility(ESlateVisibility::Collapsed);
   World->GetTimerManager().SetTimer(OpeningTimer,this,&UTutorialPromptWidget::WaitForOpening,.25f,true);return;
  }
 }
 ActivatePrompt();
}
void UTutorialPromptWidget::WaitForOpening()
{
 UWorld* World=GetWorld();if(!World||bDismissed)return;
 for(TActorIterator<ASchoolOpeningSceneActor> It(World);It;++It)if(It->bPending)return;
 World->GetTimerManager().ClearTimer(OpeningTimer);
 World->GetTimerManager().SetTimer(OpeningTimer,this,&UTutorialPromptWidget::ActivatePrompt,4.5f,false);
}
void UTutorialPromptWidget::ActivatePrompt()
{
 if(bDismissed||bActive)return;
 UWorld* World=GetWorld();if(!World)return;
 if(bOpeningDeferred)for(TActorIterator<ASchoolOpeningSceneActor> It(World);It;++It)if(It->bPending)
 {
  World->GetTimerManager().SetTimer(OpeningTimer,this,&UTutorialPromptWidget::WaitForOpening,.25f,true);return;
 }
 bOpeningDeferred=false;bActive=true;
 SetVisibility(ESlateVisibility::HitTestInvisible);
 SetRenderOpacity(FadeInSeconds>0?0:1);
 ActivePrompts.AddUnique(this);RefreshStacks();
 ObservedPawn=GetOwningPlayerPawn();InitialPawn=ObservedPawn;
 TransformComponent.Reset();LegacyAttackComponents.Reset();bInitiallyTransformed=false;
 InitialMontageInstanceId=TutorialMontageInstance(ObservedPawn.Get());InitialExecution=0;bPreviouslyJumping=false;
 if(APawn* Pawn=ObservedPawn.Get())
 {
  TInlineComponentArray<UActorComponent*> Components(Pawn);
  for(UActorComponent* Component:Components)
  {
   const FString Name=Component->GetClass()->GetName();
   if(Name.Contains(TEXT("Ac_Transform")))TransformComponent=Component;
   if(Name.Contains(TEXT("Ac_Attack"))||Name.Contains(TEXT("Ac_ComboAttack")))LegacyAttackComponents.Add(Component);
  }
  bInitiallyTransformed=ReadTutorialBool(TransformComponent.Get(),TEXT("IsActiveSlime"));
 }
 if(APawn* Pawn=ObservedPawn.Get())
 {
  LastPawnLocation=Pawn->GetActorLocation();
  if(auto* Combat=Pawn->FindComponentByClass<UCombatAbilitySystem>())InitialExecution=Combat->GetExecutionId();
  if(auto* Character=Cast<ACharacter>(Pawn))bPreviouslyJumping=Character->bWasJumping;
 }
 LastTickTime=World->GetTimeSeconds();
 World->GetTimerManager().SetTimer(ToastTimer,this,&UTutorialPromptWidget::TickToast,1.f/60.f,true);
}
void UTutorialPromptWidget::TickToast()
{
 if(UWorld* World=GetWorld())
 {
  const double Now=World->GetTimeSeconds();const float Delta=FMath::Max(0.0,Now-LastTickTime);LastTickTime=Now;
  AdvanceToast(Delta);
 }
}
bool UTutorialPromptWidget::ObserveAction()
{
 APawn* Pawn=GetOwningPlayerPawn();if(!Pawn)return false;
 // Legacy transform marks this flag only after successfully spawning and possessing the slime.
 if(ResolveAction()==ETutorialPromptAction::Transform&&!bInitiallyTransformed&&InitialPawn.IsValid()&&Pawn!=InitialPawn.Get()
  &&ReadTutorialBool(TransformComponent.Get(),TEXT("IsActiveSlime")))return true;
 if(Pawn!=ObservedPawn.Get())
 {
  ObservedPawn=Pawn;LastPawnLocation=Pawn->GetActorLocation();
  InitialExecution=0;if(auto* Combat=Pawn->FindComponentByClass<UCombatAbilitySystem>())InitialExecution=Combat->GetExecutionId();
  bPreviouslyJumping=false;return false;
 }
 const FVector Location=Pawn->GetActorLocation();
 const float Distance=FVector::Dist2D(Location,LastPawnLocation);LastPawnLocation=Location;
 switch(ResolveAction())
 {
 case ETutorialPromptAction::Movement:
  return !Pawn->GetLastMovementInputVector().IsNearlyZero()&&Distance>0.5f&&Pawn->GetVelocity().SizeSquared2D()>1.f;
 case ETutorialPromptAction::Jump:
  if(auto* Character=Cast<ACharacter>(Pawn))
  {
   const bool Jumping=Character->bWasJumping;
   const bool Success=Jumping&&!bPreviouslyJumping&&Character->GetVelocity().Z>0&&Character->GetCharacterMovement()->IsFalling();
   bPreviouslyJumping=Jumping;return Success;
  }return false;
 case ETutorialPromptAction::Attack:
  if(auto* Combat=Pawn->FindComponentByClass<UCombatAbilitySystem>())
   if(Combat->GetExecutionId()!=InitialExecution&&Combat->GetActiveAction()!=nullptr&&Combat->ObserveAction().bActive)return true;
  if(const int32 MontageId=TutorialMontageInstance(Pawn);MontageId!=INDEX_NONE&&MontageId!=InitialMontageInstanceId)
   for(const auto& Weak:LegacyAttackComponents)if(ReadTutorialBool(Weak.Get(),TEXT("IsAttacking")))return true;
  return false;
 default:return false;
 }
}
bool UTutorialPromptWidget::CanAdvancePresentation() const
{
 const ESlateVisibility CurrentVisibility=GetVisibility();
 if(bQueued||CurrentVisibility==ESlateVisibility::Hidden||CurrentVisibility==ESlateVisibility::Collapsed)return false;
 const APlayerController* PC=GetOwningPlayer();
 return !PC||(!PC->IsMoveInputIgnored()&&!PC->IsLookInputIgnored()&&!PC->bCinematicMode);
}
void UTutorialPromptWidget::AdvanceToast(float DeltaSeconds)
{
 if(!bActive||bDismissed||!CanAdvancePresentation())return;
 const float Delta=FMath::Max(0.f,DeltaSeconds);
 if(bFadingOut)
 {
  FadeElapsed+=Delta;
  SetRenderOpacity(FadeOutSeconds>0?FadeStartOpacity*(1-FMath::Clamp(FadeElapsed/FadeOutSeconds,0.f,1.f)):0);
  if(FadeElapsed>=FMath::Max(0.f,FadeOutSeconds))FinishDismissal();
  return;
 }
 Elapsed+=Delta;
 SetRenderOpacity(FadeInSeconds>0?FMath::Clamp(Elapsed/FadeInSeconds,0.f,1.f):1);
 if(ObserveAction()||Elapsed>=FMath::Max(0.f,FadeInSeconds)+FMath::Max(0.f,HoldSeconds))Dismiss();
}
void UTutorialPromptWidget::NotifyTutorialActionCompleted(ETutorialPromptAction CompletedAction)
{
 if(bActive&&!bOpeningDeferred&&CanAdvancePresentation()&&CompletedAction!=ETutorialPromptAction::Auto&&CompletedAction==ResolveAction())Dismiss();
}
void UTutorialPromptWidget::NotifyPlayerTutorialActionCompleted(APlayerController* Player,ETutorialPromptAction CompletedAction)
{
 if(!Player)return;
 const auto Snapshot=ActivePrompts;
 for(const auto& Weak:Snapshot)if(auto* Prompt=Weak.Get())if(Prompt->GetOwningPlayer()==Player&&Prompt->GetWorld()==Player->GetWorld())Prompt->NotifyTutorialActionCompleted(CompletedAction);
}
void UTutorialPromptWidget::Dismiss()
{
 if(bDismissed||bFadingOut||!bActive)return;
 bFadingOut=true;FadeElapsed=0;FadeStartOpacity=GetRenderOpacity();
 if(FadeOutSeconds<=0)FinishDismissal();
}
void UTutorialPromptWidget::FinishDismissal()
{
 if(bDismissed)return;
 bDismissed=true;bActive=false;
 if(UWorld* World=GetWorld())World->GetTimerManager().ClearTimer(ToastTimer);
 UnregisterToast();
 // Remove first: listeners may synchronously re-add this instance for another lesson.
 RemoveFromParent();
 OnTutorialPromptDismissed.Broadcast();
}
int32 UTutorialPromptWidget::GetStackIndex() const
{
 int32 Index=0;for(const auto& Weak:ActivePrompts)if(auto* Other=Weak.Get())
 {
  if(Other->GetWorld()!=GetWorld()||Other->GetOwningPlayer()!=GetOwningPlayer())continue;
  if(Other==this)return Index;++Index;
 }return INDEX_NONE;
}
void UTutorialPromptWidget::RefreshStacks()
{
 ActivePrompts.RemoveAll([](const auto& Weak){return !Weak.IsValid()||!Weak->bActive;});
 for(const auto& Weak:ActivePrompts)if(auto* Prompt=Weak.Get())
 {
  int32 Count=0;for(const auto& Candidate:ActivePrompts)if(auto* Other=Candidate.Get())if(Other->GetWorld()==Prompt->GetWorld()&&Other->GetOwningPlayer()==Prompt->GetOwningPlayer())++Count;
  const int32 Index=Prompt->GetStackIndex();
  Prompt->bQueued=Index>=2;
  // Hide only the card: cinematic systems own the outer widget's visibility.
  // Queued cards retain their hold time until a visible slot becomes available.
  if(Prompt->ToastBox.IsValid())
  {
   Prompt->ToastBox->SetVisibility(Prompt->bQueued?EVisibility::Collapsed:EVisibility::HitTestInvisible);
   Prompt->ToastBox->SetRenderTransform(FSlateRenderTransform(FVector2D(0,(Index-(FMath::Min(Count,2)-1)*.5f)*208.f)));
  }
 }
}
void UTutorialPromptWidget::UnregisterToast()
{
 bActive=false;ActivePrompts.RemoveAll([this](const auto& Weak){return !Weak.IsValid()||Weak.Get()==this;});RefreshStacks();
}
void UTutorialPromptWidget::NativeDestruct()
{
 if(UWorld* World=GetWorld()){World->GetTimerManager().ClearTimer(OpeningTimer);World->GetTimerManager().ClearTimer(ToastTimer);}
 bDismissed=true;bOpeningDeferred=false;UnregisterToast();
 Super::NativeDestruct();
}
