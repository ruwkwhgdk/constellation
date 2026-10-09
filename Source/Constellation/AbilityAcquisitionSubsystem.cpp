#include "AbilityAcquisitionSubsystem.h"
#include "AbilityAcquisitionArt.h"
#include "AbilityAcquisitionWidget.h"
#include "AbilityAcquisitionModel.h"
#include "Components/ActorComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Framework/Application/IInputProcessor.h"
#include "Framework/Application/SlateApplication.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/UnrealType.h"
#include "Sound/SoundBase.h"
#include "Engine/World.h"
#include "SceneEventSubsystem.h"
class FAbilityAcquisitionInput : public IInputProcessor
{
 TWeakObjectPtr<UAbilityAcquisitionSubsystem> Owner;
public:
 explicit FAbilityAcquisitionInput(UAbilityAcquisitionSubsystem* In):Owner(In){}
 virtual void Tick(const float,FSlateApplication&,TSharedRef<ICursor>)override{}
 virtual bool HandleKeyDownEvent(FSlateApplication&,const FKeyEvent& E)override{if(Owner.IsValid())Owner->Dismiss(E.IsRepeat());return Owner.IsValid();}
 virtual bool HandleKeyUpEvent(FSlateApplication&,const FKeyEvent&)override{return Owner.IsValid();}
 virtual bool HandleMouseButtonDownEvent(FSlateApplication&,const FPointerEvent&)override{if(Owner.IsValid())Owner->Dismiss(false);return Owner.IsValid();}
 virtual bool HandleMouseButtonUpEvent(FSlateApplication&,const FPointerEvent&)override{return Owner.IsValid();}
 virtual bool HandleAnalogInputEvent(FSlateApplication&,const FAnalogInputEvent&)override{return Owner.IsValid();}
};
void UAbilityAcquisitionSubsystem::Enqueue(int32 Slot,int32 PreviousMask)
{
 if(!AbilityAcquisition::ShouldPresent(Slot,PreviousMask,true))return;
 if(Widget&&Widget->Slot==Slot)return;for(const auto& R:Requests)if(R.Slot==Slot)return;
 Requests.Add({Slot,PreviousMask|(1<<Slot)});NotBefore=FPlatformTime::Seconds()+.15;
}
void UAbilityAcquisitionSubsystem::Preview(int32 Slot,int32 PreviousMask){Enqueue(Slot,PreviousMask&~(1<<FMath::Clamp(Slot,0,6)));}
void UAbilityAcquisitionSubsystem::PlayCue(int32 Index){if(Art&&Art->Sounds.IsValidIndex(Index)&&Art->Sounds[Index])UGameplayStatics::PlaySound2D(this,Art->Sounds[Index],.5f,1,0,nullptr,nullptr,true);}
void UAbilityAcquisitionSubsystem::Tick(float)
{
 const double Now=FPlatformTime::Seconds();
 if(!Widget)
 {
  if(Requests.IsEmpty()||Now<NotBefore||!FSlateApplication::IsInitialized())return;
  auto* PC=GetWorld()->GetFirstPlayerController();if(!PC||!PC->IsLocalController()||PC->bCinematicMode)return;
  if(auto* Events=GetWorld()->GetSubsystem<USceneEventSubsystem>();Events&&Events->IsBusy())return;
  if(!Art)Art=LoadObject<UAbilityAcquisitionArt>(nullptr,TEXT("/Game/Constellation/UI/AbilityAcquisition/DA_AbilityAcquisition.DA_AbilityAcquisition"));
  if(!Art||!Art->IsReady()){UE_LOG(LogTemp,Error,TEXT("Ability acquisition art missing; request discarded without capturing input"));Requests.Reset();return;}
  const auto Request=Requests[0];Requests.RemoveAt(0);
  Widget=CreateWidget<UAbilityAcquisitionWidget>(PC);if(!Widget)return;
  Widget->ForceVolatile(true);Widget->Art=Art;Widget->Slot=Request.Slot;Widget->OwnedMask=Request.Mask;Widget->AddToViewport(10000);
  // Releases are consumed by the overlay, so clear any gameplay keys held before capture.
  PC->FlushPressedKeys();Player=PC;OldCursor=PC->bShowMouseCursor;PC->SetShowMouseCursor(false);PC->SetIgnoreMoveInput(true);PC->SetIgnoreLookInput(true);
  PreviousFocus=FSlateApplication::Get().GetKeyboardFocusedWidget();Input=MakeShared<FAbilityAcquisitionInput>(this);FSlateApplication::Get().RegisterInputPreProcessor(Input,0);
  PausedByUs=!UGameplayStatics::IsGamePaused(this)&&PC->SetPause(true);
  Started=Now;ExitStarted=-1;SoundStage=0;
  UE_LOG(LogTemp,Display,TEXT("AbilityAcquisition START slot=%d mask=%d"),Request.Slot,Request.Mask);
 }
 Widget->Elapsed=Now-Started;
 if(SoundStage==0&&Widget->Elapsed>=.35){PlayCue(0);SoundStage=1;}
 if(SoundStage==1&&Widget->Elapsed>=1.55){PlayCue(1);SoundStage=2;}
 if(SoundStage==2&&Widget->Elapsed>=4){PlayCue(2);SoundStage=3;}
 if(ExitStarted>=0){Widget->ExitOpacity=1-AbilityAcquisition::Fade(Now-ExitStarted,0,.7);if(Now-ExitStarted>=.7)Finish();}
}
void UAbilityAcquisitionSubsystem::Dismiss(bool Repeat){if(Widget&&AbilityAcquisition::CanDismiss(FPlatformTime::Seconds()-Started,Repeat,ExitStarted>=0)){ExitStarted=FPlatformTime::Seconds();PlayCue(3);}}
void UAbilityAcquisitionSubsystem::Finish()
{
 if(Input&&FSlateApplication::IsInitialized()){FSlateApplication::Get().UnregisterInputPreProcessor(Input);if(auto Focus=PreviousFocus.Pin())FSlateApplication::Get().SetKeyboardFocus(Focus,EFocusCause::SetDirectly);}Input.Reset();PreviousFocus.Reset();
 if(Player){Player->FlushPressedKeys();Player->SetIgnoreMoveInput(false);Player->SetIgnoreLookInput(false);Player->SetShowMouseCursor(OldCursor);if(PausedByUs)Player->SetPause(false);}PausedByUs=false;Player=nullptr;
 if(Widget){Widget->RemoveFromParent();Widget=nullptr;UE_LOG(LogTemp,Display,TEXT("AbilityAcquisition FINISH"));}
 NotBefore=FPlatformTime::Seconds()+.1;
}
void UAbilityAcquisitionSubsystem::Deinitialize(){Requests.Reset();Finish();Art=nullptr;Super::Deinitialize();}
void UAbilityAcquisitionLibrary::BeforeUnlock(UActorComponent* Component,int32 Slot,bool Unlock)
{
 if(!Component||!Component->GetWorld()||Slot<0||Slot>2)return;
 const auto* Pawn=Cast<APawn>(Component->GetOwner());if(!Pawn||!Pawn->IsLocallyControlled())return;
 const FName Names[]={TEXT("IsJumpUnlocked"),TEXT("IsCombatUnlocked"),TEXT("IsTransformUnlocked")};int32 Mask=0;
 for(int32 I=0;I<3;I++){auto* P=FindFProperty<FBoolProperty>(Component->GetClass(),Names[I]);if(!P){UE_LOG(LogTemp,Error,TEXT("Ability UI flag schema mismatch"));return;}if(P->GetPropertyValue_InContainer(Component))Mask|=1<<I;}
 if(AbilityAcquisition::ShouldPresent(Slot,Mask,Unlock))if(auto* S=Component->GetWorld()->GetSubsystem<UAbilityAcquisitionSubsystem>())S->Enqueue(Slot,Mask);
}
void UAbilityAcquisitionLibrary::PreviewAbilityAcquisition(UObject* Context,int32 Slot,int32 Mask){if(Context&&Context->GetWorld())if(auto* S=Context->GetWorld()->GetSubsystem<UAbilityAcquisitionSubsystem>())S->Preview(Slot,Mask);}
