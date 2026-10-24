#include "ItemAcquisitionSubsystem.h"
#include "ItemAcquisitionWidget.h"
#include "SceneDirectorPlayer.h"
#include "Components/ActorComponent.h"
#include "EnhancedPlayerInput.h"
#include "EnhancedActionKeyMapping.h"
#include "InputAction.h"
#include "Engine/World.h"
#include "Engine/LocalPlayer.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "Framework/Application/IInputProcessor.h"
#include "Framework/Application/SlateApplication.h"
#include "Framework/Application/SlateUser.h"
#include "Layout/WidgetPath.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"

class FItemAcquisitionInput final : public IInputProcessor
{
 TWeakObjectPtr<UItemAcquisitionSubsystem> Owner;
 bool Active()const{return Owner.IsValid()&&Owner->CapturesInput();}
public:
 explicit FItemAcquisitionInput(UItemAcquisitionSubsystem* In):Owner(In){}
 virtual void Tick(float,FSlateApplication&,TSharedRef<ICursor>)override{}
 virtual bool HandleKeyDownEvent(FSlateApplication&,const FKeyEvent& E)override{if(!Active())return false;Owner->InputKey(E.GetKey(),true,E.IsRepeat());return true;}
 virtual bool HandleKeyUpEvent(FSlateApplication&,const FKeyEvent& E)override{if(!Active())return false;Owner->InputKey(E.GetKey(),false,false);return true;}
 virtual bool HandleMouseButtonDownEvent(FSlateApplication&,const FPointerEvent& E)override{if(!Active())return false;Owner->InputKey(E.GetEffectingButton(),true,false);return true;}
 virtual bool HandleMouseButtonUpEvent(FSlateApplication&,const FPointerEvent& E)override{if(!Active())return false;Owner->InputKey(E.GetEffectingButton(),false,false);return true;}
 virtual bool HandleMouseMoveEvent(FSlateApplication&,const FPointerEvent&)override{return Active();}
 // Route directly: cursor visibility and position must not make long descriptions inaccessible.
 virtual bool HandleMouseWheelOrGestureEvent(FSlateApplication&,const FPointerEvent& E,const FPointerEvent*)override{if(!Active())return false;Owner->ScrollDescription(-E.GetWheelDelta()*96.f);return true;}
 virtual bool HandleMouseButtonDoubleClickEvent(FSlateApplication&,const FPointerEvent&)override{return Active();}
 virtual bool HandleMotionDetectedEvent(FSlateApplication&,const FMotionEvent&)override{return Active();}
 virtual bool HandleAnalogInputEvent(FSlateApplication&,const FAnalogInputEvent&)override{return Active();}
};

FGuid UItemAcquisitionSubsystem::Enqueue(const FItemAcquisitionPresentation& P,FKey Key,UObject* Owner,TFunction<void(bool)> Callback)
{
 if(Key==EKeys::AnyKey||Key.IsAxis1D()||Key.IsAxis2D()||Key.IsAxis3D())return FGuid();
 if(bStopping||bCancelling||!IsValid(P.Sprite)||P.Name.IsEmpty()||P.Description.IsEmpty()||P.Quantity<1
    ||!FMath::IsFinite(P.SpriteScale)||P.SpriteScale<=0||P.SpriteOffset.ContainsNaN())return FGuid();
 FItemAcquisitionRequest R;R.Id=FGuid::NewGuid();R.Presentation=P;R.Key=Key;R.Owner=Owner;R.bHasOwner=Owner!=nullptr;R.Resolved=MoveTemp(Callback);
 const FGuid Id=R.Id;Requests.Add(MoveTemp(R));return Id;
}
void UItemAcquisitionSubsystem::Cancel(FGuid Id)
{
 const int32 Index=Requests.IndexOfByPredicate([Id](const auto& R){return R.Id==Id;});if(Index==INDEX_NONE)return;
 if(Index==0&&Widget){Finish(false);return;}
 auto Callback=MoveTemp(Requests[Index].Resolved);Requests.RemoveAt(Index);if(Callback)Callback(false);
}
void UItemAcquisitionSubsystem::CancelAll()
{
 if(bCancelling)return;TGuardValue<bool> Guard(bCancelling,true);
 // Detach before broadcasting: callback cancellation cannot invalidate this iteration.
 auto Pending=MoveTemp(Requests);Requests.Reset();Restore();
 if(auto* Scene=OverlayScene.Get())Scene->SceneOverlays.Remove(Widget);OverlayScene.Reset();
 if(Widget){Widget->RemoveFromParent();Widget=nullptr;}
 for(auto& R:Pending)if(R.Resolved)R.Resolved(false);
}
void UItemAcquisitionSubsystem::Capture(APlayerController* PC)
{
 if(bCaptured)return;bCaptured=true;Player=PC;bOldCursor=PC->bShowMouseCursor;
 auto& Slate=FSlateApplication::Get();PreviousFocus=Slate.GetKeyboardFocusedWidget();PreviousCaptor=Slate.GetCursorUser()->GetCursorCaptor();
 if(auto* LP=PC->GetLocalPlayer();LP&&LP->ViewportClient)
 {
  Viewport=LP->ViewportClient;PreviousCapture=uint8(Viewport->GetMouseCaptureMode());PreviousLock=uint8(Viewport->GetMouseLockMode());
  bOldIgnoreInput=Viewport->IgnoreInput();Viewport->SetIgnoreInput(true);
  Viewport->SetMouseCaptureMode(EMouseCaptureMode::NoCapture);Viewport->SetMouseLockMode(EMouseLockMode::DoNotLock);
 }
 Slate.ReleaseAllPointerCapture();Slate.ProcessReply(FWidgetPath(),FReply::Handled().ReleaseMouseLock(),nullptr,nullptr);
 PC->FlushPressedKeys();PC->SetIgnoreMoveInput(true);PC->SetIgnoreLookInput(true);PC->SetShowMouseCursor(false);
 Input=MakeShared<FItemAcquisitionInput>(this);Slate.RegisterInputPreProcessor(Input,0);
}
void UItemAcquisitionSubsystem::Restore()
{
 if(!bCaptured)return;
 if(FSlateApplication::IsInitialized())
 {
  auto& Slate=FSlateApplication::Get();if(Input)Slate.UnregisterInputPreProcessor(Input);
  const auto Root=OwnedFocus;
  const bool OwnFocus=!Slate.GetKeyboardFocusedWidget().IsValid()||(Root&&(Root->HasKeyboardFocus()||Root->HasFocusedDescendants()));
  if(OwnFocus)
  {
   if(Player.IsValid()&&!Player->bShowMouseCursor)Player->SetShowMouseCursor(bOldCursor);
   if(auto Focus=PreviousFocus.Pin())Slate.SetKeyboardFocus(Focus,EFocusCause::SetDirectly);
   else Slate.ClearKeyboardFocus(EFocusCause::SetDirectly);
   if(Viewport.IsValid()&&Viewport->GetMouseCaptureMode()==EMouseCaptureMode::NoCapture&&Viewport->GetMouseLockMode()==EMouseLockMode::DoNotLock)
   {
    Viewport->SetMouseCaptureMode(EMouseCaptureMode(PreviousCapture));Viewport->SetMouseLockMode(EMouseLockMode(PreviousLock));
    if(auto Captor=PreviousCaptor.Pin();Captor&&!Slate.GetCursorUser()->GetCursorCaptor())
    {
     auto Reply=FReply::Handled().CaptureMouse(Captor.ToSharedRef());
     if(EMouseLockMode(PreviousLock)!=EMouseLockMode::DoNotLock)Reply.LockMouseToWidget(Captor.ToSharedRef());
     Slate.ProcessReply(FWidgetPath(),Reply,nullptr,nullptr);
    }
   }
  }
 }
 if(Viewport.IsValid()&&Viewport->IgnoreInput())Viewport->SetIgnoreInput(bOldIgnoreInput);
 if(Player.IsValid()){Player->FlushPressedKeys();Player->SetIgnoreMoveInput(false);Player->SetIgnoreLookInput(false);}
 bCaptured=false;Player.Reset();Viewport.Reset();Input.Reset();PreviousFocus.Reset();PreviousCaptor.Reset();OwnedFocus.Reset();HeldKeys.Reset();ActiveKey=FKey();
}
bool UItemAcquisitionSubsystem::StartNext()
{
 if(Requests.IsEmpty()||!FSlateApplication::IsInitialized())return false;
 auto* PC=GetWorld()?GetWorld()->GetFirstPlayerController():nullptr;
 if(!PC||!PC->IsLocalController()){CancelAll();return false;}
 auto& R=Requests[0];ActiveKey=R.Key;
 if(!ActiveKey.IsValid())
 {
  if(auto* Enhanced=Cast<UEnhancedPlayerInput>(PC->PlayerInput))
   for(const auto& Mapping:Enhanced->GetEnhancedActionMappingsView())
    if(Mapping.Action&&Mapping.Action->GetFName()==TEXT("IA_Interact")&&Mapping.Key.IsValid()&&!Mapping.Key.IsAxis1D()&&!Mapping.Key.IsAxis2D()&&!Mapping.Key.IsAxis3D())
    {
     if(!ActiveKey.IsValid())ActiveKey=Mapping.Key;
     // Desktop default is a real keyboard binding; callers can explicitly choose a gamepad binding.
     if(!Mapping.Key.IsGamepadKey()&&!Mapping.Key.IsMouseButton()){ActiveKey=Mapping.Key;break;}
    }
 }
 if(!ActiveKey.IsValid()){UE_LOG(LogTemp,Warning,TEXT("Special item card cancelled: IA_Interact has no live button mapping; provide ConfirmKey."));Cancel(R.Id);return false;}
 const bool Held=HeldKeys.Contains(ActiveKey)||PC->IsInputKeyDown(ActiveKey);
 Widget=CreateWidget<UItemAcquisitionWidget>(PC);
 if(!Widget){Cancel(R.Id);return false;}
 ASceneDirectorPlayer* Scene=Cast<ASceneDirectorPlayer>(R.Owner.Get());
 if(auto* Component=Cast<UActorComponent>(R.Owner.Get()))Scene=Cast<ASceneDirectorPlayer>(Component->GetOwner());
 // Register before entering the viewport so the director never caches this card as hidden gameplay HUD.
 if(Scene){OverlayScene=Scene;Scene->SceneOverlays.Add(Widget);}
 Widget->SetPresentation(R.Presentation,ActiveKey);Widget->SetPresentationOpacity(0,0);Widget->SetIsFocusable(true);
 // Global HUD widgets also use AddToViewport; share that layer so world markers
 // cannot draw over this full-screen modal card despite its high local Z order.
 Widget->AddToViewport(11000);Capture(PC);Widget->SetKeyboardFocus();OwnedFocus=Widget->GetCachedWidget();
 if(R.Presentation.AppearanceSound)UGameplayStatics::PlaySound2D(this,R.Presentation.AppearanceSound);
 Timing.Reset(Held);LastTick=FPlatformTime::Seconds();return true;
}
void UItemAcquisitionSubsystem::InputKey(FKey Key,bool Down,bool Repeat)
{
 if(Down)HeldKeys.Add(Key);else HeldKeys.Remove(Key);
 if(Widget&&Down&&Key!=ActiveKey)
 {
  if(Key==EKeys::PageDown||Key==EKeys::Gamepad_DPad_Down)ScrollDescription(180.f);
  else if(Key==EKeys::PageUp||Key==EKeys::Gamepad_DPad_Up)ScrollDescription(-180.f);
 }
 if(!Widget||Key!=ActiveKey)return;
 if(!Down)Timing.Release();else if(FSlateApplication::Get().IsActive())Timing.Press(Repeat);
}
void UItemAcquisitionSubsystem::ScrollDescription(float PixelDelta)
{
 if(Widget&&!Timing.bExiting&&FSlateApplication::IsInitialized()&&FSlateApplication::Get().IsActive())Widget->ScrollDescription(PixelDelta);
}
void UItemAcquisitionSubsystem::Finish(bool Completed)
{
 if(Requests.IsEmpty())return;
 auto Callback=MoveTemp(Requests[0].Resolved);Requests.RemoveAt(0);
 // Keep the modal input lease across queued cards, including the transition tick.
 if(Requests.IsEmpty())Restore();
 if(auto* Scene=OverlayScene.Get())Scene->SceneOverlays.Remove(Widget);OverlayScene.Reset();
 if(Widget){Widget->RemoveFromParent();Widget=nullptr;}
 if(Callback)Callback(Completed);
}
void UItemAcquisitionSubsystem::Tick(float)
{
 if(bStopping)return;
 TArray<FGuid> Dead;
 for(const auto& R:Requests)if(R.bHasOwner&&!R.Owner.IsValid())Dead.Add(R.Id);
 for(const auto& Id:Dead)Cancel(Id);
 if(Requests.IsEmpty()){Restore();return;}
 if(!FSlateApplication::IsInitialized()){CancelAll();return;}
 if(bCaptured&&(!Player.IsValid()||Player.Get()!=GetWorld()->GetFirstPlayerController())){CancelAll();return;}
 if(!Widget){StartNext();return;}
 // External modal focus takes precedence; do not steal it back or overwrite its restoration state.
 const auto Root=Widget->GetCachedWidget();
 if(Root&&!Root->HasKeyboardFocus()&&!Root->HasFocusedDescendants()&&FSlateApplication::Get().IsActive()){CancelAll();return;}
 const double Now=FPlatformTime::Seconds();const float Delta=float(FMath::Clamp(Now-LastTick,0.,.1));LastTick=Now;
 Timing.Advance(Delta,FSlateApplication::Get().IsActive());
 const float Exit=Timing.bExiting?1-FMath::Clamp(Timing.ExitElapsed/.25f,0.f,1.f):1.f;
 Widget->SetPresentationOpacity(FMath::Clamp(Timing.Elapsed/.35f,0.f,1.f)*Exit,FMath::Clamp((Timing.Elapsed-.2f)/.3f,0.f,1.f)*Exit);
 if(Timing.Finished())Finish(true);
}
void UItemAcquisitionSubsystem::Deinitialize(){bStopping=true;CancelAll();Super::Deinitialize();}
