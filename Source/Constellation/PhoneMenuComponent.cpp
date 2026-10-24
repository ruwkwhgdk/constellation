#include "PhoneMenuComponent.h"
#include "PhoneMenuWidget.h"
#include "CarryComponent.h"
#include "PlayerFallComponent.h"
#include "AbilityAcquisitionSubsystem.h"
#include "SceneEventSubsystem.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/GameViewportClient.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "Framework/Application/IInputProcessor.h"
#include "Framework/Application/SlateApplication.h"
#include "Framework/Application/SlateUser.h"
#include "Layout/WidgetPath.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "UObject/UnrealType.h"

namespace
{
bool Bool(const UObject* O,FName N)
{
 const auto* P=O?FindFProperty<FBoolProperty>(O->GetClass(),N):nullptr;
 return P&&P->GetPropertyValue_InContainer(O);
}
bool UIKey(FKey K)
{return K==EKeys::Tab||K==EKeys::Left||K==EKeys::Right||K==EKeys::Up||K==EKeys::Down||K==EKeys::Enter||K==EKeys::SpaceBar;}
class FPhoneInput final : public IInputProcessor
{
 TWeakObjectPtr<UPhoneMenuComponent> Owner;
public:
 explicit FPhoneInput(UPhoneMenuComponent* O):Owner(O){}
 virtual void Tick(float,FSlateApplication&,TSharedRef<ICursor>) override {}
 virtual bool HandleKeyDownEvent(FSlateApplication&,const FKeyEvent& E) override
 {
  auto* O=Owner.Get();if(!O||!O->BlocksGameplay())return false;
  if(E.GetKey()==EKeys::Escape||E.GetKey()==EKeys::Tilde){O->RequestClose(E.IsRepeat());return true;}
  return !O->IsOpen()||!UIKey(E.GetKey());
 }
 virtual bool HandleKeyUpEvent(FSlateApplication&,const FKeyEvent& E) override
 {auto* O=Owner.Get();return O&&O->BlocksGameplay()&&(!O->IsOpen()||!UIKey(E.GetKey()));}
 virtual bool HandleMouseButtonDownEvent(FSlateApplication&,const FPointerEvent&) override
 {auto* O=Owner.Get();return O&&O->BlocksGameplay()&&!O->IsOpen();}
 virtual bool HandleMouseButtonUpEvent(FSlateApplication&,const FPointerEvent&) override
 {auto* O=Owner.Get();return O&&O->BlocksGameplay()&&!O->IsOpen();}
 virtual bool HandleAnalogInputEvent(FSlateApplication&,const FAnalogInputEvent&) override
 {return Owner.IsValid()&&Owner->BlocksGameplay();}
};
}
UPhoneMenuComponent::UPhoneMenuComponent()
{PrimaryComponentTick.bCanEverTick=true;PrimaryComponentTick.bTickEvenWhenPaused=true;PrimaryComponentTick.TickGroup=TG_PostPhysics;}
void UPhoneMenuComponent::BeginPlay()
{
 Super::BeginPlay();Character=Cast<ACharacter>(GetOwner());
 if(Character.IsValid()&&Character->GetMesh())AddTickPrerequisiteComponent(Character->GetMesh());
 if(GetOwner())GetOwner()->OnTakeAnyDamage.AddDynamic(this,&UPhoneMenuComponent::OnOwnerDamaged);
}
void UPhoneMenuComponent::BindInput()
{
 auto* C=Character.Get();auto* PC=C?Cast<APlayerController>(C->GetController()):nullptr;
 auto* EI=PC?Cast<UEnhancedInputComponent>(C->InputComponent):nullptr;
 if(!PC||!PC->IsLocalController()||!EI||(BoundInput==EI&&Controller==PC))return;
 if(BoundInput.IsValid())BoundInput->RemoveBindingByHandle(InputBinding);
 if(Controller.IsValid()&&Controller->GetLocalPlayer()&&MenuContext)
  if(auto* S=Controller->GetLocalPlayer()->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())S->RemoveMappingContext(MenuContext);
 Controller=PC;BoundInput=EI;
 if(!MenuAction)
 {
  MenuAction=NewObject<UInputAction>(this);MenuAction->ValueType=EInputActionValueType::Boolean;
  MenuAction->bTriggerWhenPaused=true;
  MenuContext=NewObject<UInputMappingContext>(this);MenuContext->MapKey(MenuAction,EKeys::Escape);MenuContext->MapKey(MenuAction,EKeys::Tilde);
 }
 if(auto* LP=PC->GetLocalPlayer())
  if(auto* S=LP->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())S->AddMappingContext(MenuContext,0);
 InputBinding=EI->BindAction(MenuAction,ETriggerEvent::Started,this,&UPhoneMenuComponent::ToggleMenu).GetHandle();
}
bool UPhoneMenuComponent::IsEnvironmentSafe() const
{
 auto* C=Character.Get();auto* PC=Controller.Get();
 if(!bGameplayAllowsMenu||!C||!PC||C->GetController()!=PC||!PC->IsLocalController()||PC->bCinematicMode)return false;
 if(!C->GetCharacterMovement()->IsMovingOnGround())return false;
 for(FName N:{FName("bIsBattleOn"),FName("bIsJumping"),FName("IsAttacking"),FName("IsPushing"),FName("IsClimbing"),FName("IsActiveSlime")})
  if(Bool(C,N))return false;
 if(auto* Carry=C->FindComponentByClass<UCarryComponent>();Carry&&Carry->BlocksOtherActions())return false;
 if(auto* Fall=C->FindComponentByClass<UPlayerFallComponent>();Fall&&Fall->IsLandingLocked())return false;
 if(auto* A=GetWorld()->GetSubsystem<UAbilityAcquisitionSubsystem>();A&&(A->IsPresenting()||A->PendingCount()>0))return false;
 if(auto* E=GetWorld()->GetSubsystem<USceneEventSubsystem>();E&&E->IsBusy())return false;
 TArray<UStaticMeshComponent*> Meshes;C->GetComponents(Meshes);
 for(auto* M:Meshes)if(M->GetFName()==TEXT("Sword")&&M->IsVisible()&&!M->bHiddenInGame)return false;
 return true;
}
bool UPhoneMenuComponent::CanOpen() const
{
 auto* C=Character.Get();auto* PC=Controller.Get();
 return bAnimationApproved&&DrawMontage&&HoldMontage&&StowMontage&&ApprovedPhoneTrack.Num()==285&&IsEnvironmentSafe()
  &&GetWorld()->GetNetMode()==NM_Standalone&&!GetWorld()->IsPaused()
  &&!PC->IsMoveInputIgnored()&&!PC->IsLookInputIgnored()
  &&C->GetMesh()&&C->GetMesh()->DoesSocketExist(HandSocket)
  &&C->GetMesh()->GetAnimInstance()&&!C->GetMesh()->GetAnimInstance()->IsAnyMontagePlaying()
  &&FSlateApplication::IsInitialized();
}
void UPhoneMenuComponent::ToggleMenu()
{
 if(Flow.Active()){RequestClose();return;}
 if(!Flow.RequestOpen(CanOpen(),FPlatformTime::Seconds()))return;
 auto* PC=Controller.Get();
 bOldCursor=PC->bShowMouseCursor;PreviousView=PC->GetViewTarget();
 PreviousFocus=FSlateApplication::Get().GetKeyboardFocusedWidget();
 PC->FlushPressedKeys();PC->SetIgnoreMoveInput(true);PC->SetIgnoreLookInput(true);bLocked=true;
 InputCapture=MakeShared<FPhoneInput>(this);
 FSlateApplication::Get().RegisterInputPreProcessor(InputCapture,0);
 ApplyPhase();
}
void UPhoneMenuComponent::RequestClose(bool Repeat)
{Flow.RequestClose(Repeat,FPlatformTime::Seconds());ApplyPhase();}
bool UPhoneMenuComponent::Play(UAnimMontage* M)
{
 auto* C=Character.Get();auto* A=C&&C->GetMesh()?C->GetMesh()->GetAnimInstance():nullptr;
 if(!A||!M)return false;
 const float Length=A->Montage_Play(M,1,EMontagePlayReturnType::Duration,0,false);
 if(Length<=0||Length>30)return false;
 ActiveMontage=M;
 LastAnimationPosition=-1.f;
 Flow.Deadline=FPlatformTime::Seconds()+Length+.5;return true;
}
FTransform UPhoneMenuComponent::SamplePhonePose(float SourceFrame) const
{
 if(ApprovedPhoneTrack.IsEmpty())return PhoneOffset;
 const float Index=FMath::Clamp(SourceFrame-1.f,0.f,float(ApprovedPhoneTrack.Num()-1));
 const int32 First=FMath::FloorToInt(Index),Last=FMath::Min(First+1,ApprovedPhoneTrack.Num()-1);
 FTransform Result;Result.Blend(ApprovedPhoneTrack[First],ApprovedPhoneTrack[Last],Index-First);
 return Result;
}
void UPhoneMenuComponent::UpdateAnimation()
{
 auto* C=Character.Get();
 auto* A=C&&C->GetMesh()?C->GetMesh()->GetAnimInstance():nullptr;
 if(!A||!ActiveMontage||!Phone)return;
 const float Position=A->Montage_GetPosition(ActiveMontage);
 const bool Drawing=Flow.Phase==PhoneMenu::Phase::Drawing,Stowing=Flow.Phase==PhoneMenu::Phase::Stowing;
 // Shader/screenshot stalls can make game time slower than wall time.
 // Recover only when the montage stops advancing, not while it is still progressing.
 if((Drawing||Stowing)&&Position>LastAnimationPosition+KINDA_SMALL_NUMBER)
 {
  LastAnimationPosition=Position;
  Flow.Deadline=FPlatformTime::Seconds()+2.;
 }
 const float Frame=(Drawing?1.f:(Stowing?207.f:73.f))+Position*30.f;
 Phone->SetRelativeTransform(SamplePhonePose(Frame));
 // Read the actual montage cursor, not wall time: slow frames cannot skip prop events.
 if(Drawing&&!bGrabbed&&Frame>=31.f)NotifyPhoneEvent(EPhoneMenuEvent::Grab,GetMenuToken());
 if(Stowing&&Frame>=246.f)NotifyPhoneEvent(EPhoneMenuEvent::Stow,GetMenuToken());
 if(Position>=ActiveMontage->GetPlayLength()-KINDA_SMALL_NUMBER)
 {
  if(Drawing)NotifyPhoneEvent(EPhoneMenuEvent::Drawn,GetMenuToken());
  else if(Stowing)NotifyPhoneEvent(EPhoneMenuEvent::Finished,GetMenuToken());
 }
}
bool UPhoneMenuComponent::CreateCamera()
{
 auto* C=Character.Get();auto* PC=Controller.Get();if(!C||!PC)return false;
 const FVector Position=C->GetActorTransform().TransformPosition(CameraLocal);
 FCollisionQueryParams Query(SCENE_QUERY_STAT(PhoneCamera),false,C);
 FHitResult Hit;
 // Trace from in front of the torso, avoiding the head/shoulder interior.
 const FVector Start=C->GetActorLocation()+C->GetActorForwardVector()*30+FVector(0,0,35);
 if(GetWorld()->SweepSingleByChannel(Hit,Start,Position,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(8),Query))return false;
 MenuCamera=GetWorld()->SpawnActor<ACameraActor>(Position,(C->GetActorQuat()*CameraRotation.Quaternion()).Rotator());
 if(!MenuCamera)return false;
 MenuCamera->GetCameraComponent()->SetFieldOfView(CameraFOV);
 MenuCamera->GetCameraComponent()->SetConstraintAspectRatio(false);
 bCameraSettled=BlendSeconds<=0;
 if(PC->PlayerCameraManager)
  CameraBlendHandle=PC->PlayerCameraManager->OnBlendComplete().AddWeakLambda(this,[this]()
  {if(Controller.IsValid()&&Controller->GetViewTarget()==MenuCamera)bCameraSettled=true;});
 PC->SetViewTargetWithBlend(MenuCamera,BlendSeconds,VTBlend_Cubic);
 return true;
}
void UPhoneMenuComponent::ApplyPhase()
{
 if(Applied==Flow.Phase)return;
 Applied=Flow.Phase;PhaseStarted=FPlatformTime::Seconds();
 auto* C=Character.Get();auto* PC=Controller.Get();
 switch(Applied)
 {
 case PhoneMenu::Phase::Closed:Cleanup();break;
 case PhoneMenu::Phase::Preparing:break;
 case PhoneMenu::Phase::Drawing:
 {
  Phone=NewObject<UStaticMeshComponent>(C);
  Phone->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
  if(!Phone->GetStaticMesh()){CancelMenu();return;}
  Phone->SetCollisionEnabled(ECollisionEnabled::NoCollision);Phone->SetGenerateOverlapEvents(false);
  Phone->SetSimulatePhysics(false);Phone->SetupAttachment(C->GetMesh(),HandSocket);Phone->RegisterComponent();
  Phone->SetRelativeTransform(SamplePhonePose(1));Phone->SetVisibility(false);
  bGrabbed=false;
  if(!Play(DrawMontage))CancelMenu();
  break;
 }
 case PhoneMenu::Phase::Camera:
  if(!bGrabbed||!Play(HoldMontage)||!CreateCamera()){CancelMenu();return;}
  // Hold montage length does not govern the camera watchdog.
  Flow.Deadline=PhaseStarted+BlendSeconds+1;break;
 case PhoneMenu::Phase::Open:
 {
  Widget=CreateWidget<UPhoneMenuWidget>(PC);
  if(!Widget){CancelMenu();return;}
  Widget->OnClose.BindUObject(this,&UPhoneMenuComponent::RequestClose,false);
  TArray<UUserWidget*> Widgets;UWidgetBlueprintLibrary::GetAllWidgetsOfClass(this,Widgets,UUserWidget::StaticClass(),true);
  for(auto* W:Widgets)if(W&&W->GetOwningPlayer()==PC&&W->IsInViewport())
  {HiddenHUD.Add(W,static_cast<uint8>(W->GetVisibility()));W->SetVisibility(ESlateVisibility::Collapsed);}
  Widget->AddToPlayerScreen(9000);
  auto& Slate=FSlateApplication::Get();
  PreviousCaptor=Slate.GetCursorUser()->GetCursorCaptor();
  if(auto* LP=PC->GetLocalPlayer();LP&&LP->ViewportClient)
  {
   InputViewport=LP->ViewportClient;
   PreviousCaptureMode=static_cast<uint8>(InputViewport->GetMouseCaptureMode());
   PreviousLockMode=static_cast<uint8>(InputViewport->GetMouseLockMode());
   InputViewport->SetMouseCaptureMode(EMouseCaptureMode::NoCapture);
   InputViewport->SetMouseLockMode(EMouseLockMode::DoNotLock);
  }
  Slate.ReleaseAllPointerCapture();
  Slate.ProcessReply(FWidgetPath(),FReply::Handled().ReleaseMouseLock(),nullptr,nullptr);
  Widget->FocusFirst();PC->SetShowMouseCursor(true);bMenuUIOwned=true;
  bReleasingPause=false;bPaused=PC->SetPause(true,FCanUnpause::CreateUObject(this,&UPhoneMenuComponent::CanReleasePause));
  if(!bPaused)CancelMenu();
  break;
 }
 case PhoneMenu::Phase::Stowing:
  ReleaseMenuUI();
  if(Widget){Widget->RemoveFromParent();Widget=nullptr;}
  if(bPaused){bReleasingPause=true;PC->SetPause(false);bPaused=false;}
  if(MenuCamera&&PC->GetViewTarget()==MenuCamera&&PreviousView.IsValid())
   PC->SetViewTargetWithBlend(PreviousView.Get(),BlendSeconds,VTBlend_Cubic);
  if(!Play(StowMontage))CancelMenu();
  break;
 }
}
void UPhoneMenuComponent::NotifyPhoneEvent(EPhoneMenuEvent Event,int32 Token)
{
 if(Token!=GetMenuToken()||!Flow.Active())return;
 const double Now=FPlatformTime::Seconds();
 if(Event==EPhoneMenuEvent::Grab&&Flow.Phase==PhoneMenu::Phase::Drawing&&Phone)
 {Phone->SetVisibility(true);bGrabbed=true;}
 else if(Event==EPhoneMenuEvent::Drawn&&bGrabbed)Flow.Drawn(Flow.Generation,Now);
 else if(Event==EPhoneMenuEvent::Stow&&Flow.Phase==PhoneMenu::Phase::Stowing&&Phone)Phone->SetVisibility(false);
 else if(Event==EPhoneMenuEvent::Finished)Flow.Stowed(Flow.Generation,Now);
 ApplyPhase();
}
void UPhoneMenuComponent::TickComponent(float D,ELevelTick T,FActorComponentTickFunction* F)
{
 Super::TickComponent(D,T,F);
 if(!Flow.Active()){BindInput();return;}
 UpdateAnimation();
 if(!Flow.Active())return;
 if(!IsEnvironmentSafe()){CancelMenu();return;}
 if(GetWorld()->IsPaused()&&!bPaused){CancelMenu();return;}
 if(MenuCamera&&Flow.Phase==PhoneMenu::Phase::Open&&Controller->GetViewTarget()!=MenuCamera){CancelMenu();return;}
 const double Now=FPlatformTime::Seconds();Flow.Tick(Now);
 if(Flow.Phase==PhoneMenu::Phase::Preparing&&Character->GetVelocity().Size2D()<3)Flow.Ready(Flow.Generation,Now);
 if(Flow.Phase==PhoneMenu::Phase::Camera&&bCameraSettled)Flow.CameraReady(Flow.Generation,Now);
 ApplyPhase();
}
void UPhoneMenuComponent::CancelMenu(){Flow.Abort();ApplyPhase();Cleanup();}
void UPhoneMenuComponent::ReleaseMenuUI()
{
 if(!bMenuUIOwned||!FSlateApplication::IsInitialized())return;
 auto& Slate=FSlateApplication::Get();
 const auto Root=Widget?Widget->GetCachedWidget():TSharedPtr<SWidget>();
 const bool OwnFocus=Root&&(Root->HasKeyboardFocus()||Root->HasFocusedDescendants());
 if(OwnFocus)
 {
  if(Controller.IsValid())Controller->SetShowMouseCursor(bOldCursor);
  if(auto Focus=PreviousFocus.Pin())Slate.SetKeyboardFocus(Focus,EFocusCause::SetDirectly);
  if(InputViewport.IsValid()&&InputViewport->GetMouseCaptureMode()==EMouseCaptureMode::NoCapture
     &&InputViewport->GetMouseLockMode()==EMouseLockMode::DoNotLock)
  {
   InputViewport->SetMouseCaptureMode(static_cast<EMouseCaptureMode>(PreviousCaptureMode));
   InputViewport->SetMouseLockMode(static_cast<EMouseLockMode>(PreviousLockMode));
   if(auto Captor=PreviousCaptor.Pin();Captor&&!Slate.GetCursorUser()->GetCursorCaptor())
   {
    FReply Reply=FReply::Handled().CaptureMouse(Captor.ToSharedRef());
    if(static_cast<EMouseLockMode>(PreviousLockMode)!=EMouseLockMode::DoNotLock)Reply.LockMouseToWidget(Captor.ToSharedRef());
    Slate.ProcessReply(FWidgetPath(),Reply,nullptr,nullptr);
   }
  }
 }
 bMenuUIOwned=false;PreviousCaptor.Reset();InputViewport.Reset();
}
void UPhoneMenuComponent::Cleanup()
{
 ReleaseMenuUI();
 if(Widget){Widget->OnClose.Unbind();Widget->RemoveFromParent();Widget=nullptr;}
 if(InputCapture&&FSlateApplication::IsInitialized())FSlateApplication::Get().UnregisterInputPreProcessor(InputCapture);
 InputCapture.Reset();
 if(auto* C=Character.Get())
  if(auto* A=C->GetMesh()?C->GetMesh()->GetAnimInstance():nullptr)
   // A no-auto-blend montage remains active at its final pose after playback stops.
   for(auto* M:{DrawMontage.Get(),HoldMontage.Get(),StowMontage.Get()})if(M&&A->Montage_IsActive(M))A->Montage_Stop(.15f,M);
 if(auto* PC=Controller.Get())
 {
  if(CameraBlendHandle.IsValid()&&PC->PlayerCameraManager)PC->PlayerCameraManager->OnBlendComplete().Remove(CameraBlendHandle);
  if(MenuCamera&&PC->GetViewTarget()==MenuCamera)
  {
   if(PC->GetPawn()==Character.Get()&&PreviousView.IsValid())PC->SetViewTarget(PreviousView.Get());
   else PC->SetViewTarget(PC->GetPawn()?static_cast<AActor*>(PC->GetPawn()):PC);
  }
  if(bPaused){bReleasingPause=true;PC->SetPause(false);}
  if(bLocked)
  {PC->FlushPressedKeys();PC->SetIgnoreMoveInput(false);PC->SetIgnoreLookInput(false);}
 }
 CameraBlendHandle.Reset();bCameraSettled=false;
 for(auto& It:HiddenHUD)if(It.Key.IsValid()&&It.Key->GetVisibility()==ESlateVisibility::Collapsed)It.Key->SetVisibility(static_cast<ESlateVisibility>(It.Value));
 HiddenHUD.Reset();PreviousFocus.Reset();PreviousView.Reset();
 bLocked=false;bPaused=false;bGrabbed=false;
 ActiveMontage=nullptr;
 if(Phone){Phone->DestroyComponent();Phone=nullptr;}
 if(MenuCamera){MenuCamera->Destroy();MenuCamera=nullptr;}
}
void UPhoneMenuComponent::OnOwnerDamaged(AActor*,float,const UDamageType*,AController*,AActor*){if(Flow.Active())CancelMenu();}
void UPhoneMenuComponent::EndPlay(const EEndPlayReason::Type Reason)
{
 CancelMenu();
 if(BoundInput.IsValid())BoundInput->RemoveBindingByHandle(InputBinding);
 if(Controller.IsValid()&&Controller->GetLocalPlayer()&&MenuContext)
  if(auto* S=Controller->GetLocalPlayer()->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())S->RemoveMappingContext(MenuContext);
 if(GetOwner())GetOwner()->OnTakeAnyDamage.RemoveDynamic(this,&UPhoneMenuComponent::OnOwnerDamaged);
 Super::EndPlay(Reason);
}
