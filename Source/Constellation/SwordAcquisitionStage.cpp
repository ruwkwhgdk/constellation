#include "SwordAcquisitionStage.h"
#include "AbilityAcquisitionSubsystem.h"
#include "ItemAcquisitionSubsystem.h"
#include "ItemAcquisitionDefinition.h"
#include "SceneDirectorPlayer.h"
#include "TutorialPromptWidget.h"
#include "Blueprint/UserWidget.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"
#include "Engine/LocalPlayer.h"
#include "Engine/Texture2D.h"
#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "UObject/UnrealType.h"
#include "UObject/StructOnScope.h"

namespace
{
 bool ReadFlag(UObject* Object,FName Name)
 {auto* P=Object?FindFProperty<FBoolProperty>(Object->GetClass(),Name):nullptr;return P&&P->GetPropertyValue_InContainer(Object);}
}
ASwordAcquisitionStage::ASwordAcquisitionStage()
{PrimaryActorTick.bCanEverTick=true;SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));}
UActorComponent* ASwordAcquisitionStage::Ability()const
{
 auto* PC=GetWorld()?GetWorld()->GetFirstPlayerController():nullptr;
 auto* Pawn=Character.IsValid()?Character.Get():(PC?Cast<ACharacter>(PC->GetPawn()):nullptr);
 if(Pawn)for(auto* C:Pawn->GetComponents())if(C&&FindFProperty<FBoolProperty>(C->GetClass(),TEXT("IsCombatUnlocked")))return C;
 return nullptr;
}
bool ASwordAcquisitionStage::CombatUnlocked()const{return ReadFlag(Ability(),TEXT("IsCombatUnlocked"))&&ReadFlag(Ability(),TEXT("IsAttackUnlocked"));}
bool ASwordAcquisitionStage::RunCue(ASceneDirectorPlayer* P,FName Cue)
{
 auto* PC=GetWorld()->GetFirstPlayerController();
 if(!P||P->GetWorld()!=GetWorld()||!PC)return false;
 if(Cue==TEXT("Begin"))
 {
  if(Director.IsValid()||bCompleted||CombatUnlocked()||!IsValid(Sword)||!ReadFlag(Ability(),TEXT("IsJumpUnlocked")))return false;
  Character=Cast<ACharacter>(PC->GetPawn());if(!Character.IsValid()||!ItemDefinition||!ItemDefinition->Presentation.Sprite)return false;
  if(AnimationSet&&!BeginAnimation())return false;
  Director=P;P->OnDirectorStopped.AddDynamic(this,&ASwordAcquisitionStage::Finished);
  BeforeCharacter=Character->GetActorTransform();bOldHidden=Sword->IsHidden();bOldCollision=Sword->GetActorEnableCollision();
  auto* Move=Character->GetCharacterMovement();OldMovement=Move->MovementMode;OldCustom=Move->CustomMovementMode;
  Move->StopMovementImmediately();Move->DisableMovement();Character->SetActorTransform(HeroineTransform,false,nullptr,ETeleportType::TeleportPhysics);
  bOldPawnInput=Character->InputEnabled();Character->DisableInput(PC);
  Sword->SetActorEnableCollision(false);PC->FlushPressedKeys();bItemConfirmed=bCommitted=false;Phase=Cue;return true;
 }
 if(Director!=P||!Character.IsValid())return false;
 if(Cue==TEXT("ItemUI"))
 {
  auto* UI=GetWorld()->GetSubsystem<UItemAcquisitionSubsystem>();if(ItemRequest.IsValid()||bItemConfirmed||!UI)return false;
  P->SetDirectorPaused(true);TWeakObjectPtr<ASwordAcquisitionStage> Weak(this);
  ItemRequest=UI->Enqueue(ItemDefinition->Presentation,FKey(),P,[Weak](bool Confirmed)
  {
   if(auto* Stage=Weak.Get())
   {
    Stage->ItemRequest.Invalidate();Stage->bItemConfirmed=Confirmed;
    if(auto* Scene=Stage->Director.Get();Scene&&Scene->IsDirectorPlaying())
    {if(Confirmed){Stage->Phase=TEXT("ItemConfirmed");Scene->SetDirectorPaused(false);}else Scene->StopDirector();}
   }
  });
  if(!ItemRequest.IsValid()){P->SetDirectorPaused(false);return false;}
 }
 else if(Cue==TEXT("Commit"))
 {
  if(!bItemConfirmed||ItemRequest.IsValid()||bCommitted)return false;
  // The current player gates attack separately from the legacy combat mode.
  auto* Component=Ability();auto* UnlockFunction=Component?Component->FindFunction(TEXT("Unlock Ability")):nullptr;
  auto* Type=UnlockFunction?FindFProperty<FByteProperty>(UnlockFunction,TEXT("Ability Type")):nullptr;
  auto* Unlock=UnlockFunction?FindFProperty<FBoolProperty>(UnlockFunction,TEXT("Unlock")):nullptr;
  const int64 AttackType=Type&&Type->Enum?Type->Enum->GetValueByNameString(TEXT("NewEnumerator3")):INDEX_NONE;
  if(!Unlock||AttackType==INDEX_NONE||!FindFProperty<FBoolProperty>(Component->GetClass(),TEXT("IsAttackUnlocked")))return false;
  auto* UI=GetWorld()->GetSubsystem<UAbilityAcquisitionSubsystem>();
  if(!UI||!UI->GrantPresentedAbility(Component,1))return false;
  FStructOnScope Params(UnlockFunction);Type->SetPropertyValue_InContainer(Params.GetStructMemory(),uint8(AttackType));Unlock->SetPropertyValue_InContainer(Params.GetStructMemory(),true);Component->ProcessEvent(UnlockFunction,Params.GetStructMemory());
  if(!CombatUnlocked())return false;
  bCommitted=bCompleted=true;Sword->SetActorHiddenInGame(true);
  if(auto* Flag=FindFProperty<FBoolProperty>(Sword->GetClass(),TEXT("bIsInteracted")))Flag->SetPropertyValue_InContainer(Sword,true);
 }
 else if(Cue!=TEXT("Grip")&&Cue!=TEXT("Pull")&&Cue!=TEXT("RaiseHold")&&Cue!=TEXT("Lower"))return false;
 else if(AnimationSet&&!QueueAnimation(Cue))return false;
 Phase=Cue;UE_LOG(LogTemp,Display,TEXT("SwordAcquisition cue=%s"),*Cue.ToString());return true;
}
void ASwordAcquisitionStage::CloseItem()
{
 const FGuid Id=ItemRequest;ItemRequest.Invalidate();
 if(Id.IsValid())if(auto* UI=GetWorld()->GetSubsystem<UItemAcquisitionSubsystem>())UI->Cancel(Id);
}
void ASwordAcquisitionStage::Restore(bool Cancelled)
{
 CloseItem();
 RestoreAnimation(Cancelled);
 if(auto* P=Director.Get(true))P->OnDirectorStopped.RemoveDynamic(this,&ASwordAcquisitionStage::Finished);
 if(auto* C=Character.Get())
 {
  if(Cancelled)C->SetActorTransform(BeforeCharacter,false,nullptr,ETeleportType::TeleportPhysics);C->GetCharacterMovement()->SetMovementMode(EMovementMode(OldMovement),OldCustom);
  if(auto* PC=Cast<APlayerController>(C->GetController())){PC->FlushPressedKeys();if(bOldPawnInput)C->EnableInput(PC);}
 }
 if(IsValid(Sword)){Sword->SetActorHiddenInGame(Cancelled?bOldHidden:true);Sword->SetActorEnableCollision(Cancelled?bOldCollision:false);}
 Director.Reset();Phase=Cancelled?TEXT("Cancelled"):TEXT("Completed");
}
void ASwordAcquisitionStage::Finished(bool)
{
 Restore(!bCommitted);
 if(bCommitted)
 {
  if(IsValid(Sword))if(auto* D=FindFProperty<FMulticastDelegateProperty>(Sword->GetClass(),TEXT("OnInteractionSequenceComplete")))
  {FStructOnScope Params(D->SignatureFunction);D->GetMulticastDelegate(D->ContainerPtrToValuePtr<void>(Sword))->ProcessDelegate<UObject>(Params.GetStructMemory());}
  bToastPending=true;
 }
}
void ASwordAcquisitionStage::ShowToast()
{
 auto* PC=GetWorld()->GetFirstPlayerController();
 if(!PC||PC->IsMoveInputIgnored()||PC->IsLookInputIgnored()||PC->bCinematicMode||!Character.IsValid()||!Character->InputEnabled()||Character->GetCharacterMovement()->MovementMode==MOVE_None)return;
 auto* Toast=CreateWidget<UTutorialPromptWidget>(PC);if(!Toast)return;
 Toast->Action=ETutorialPromptAction::Attack;
 if(auto* Local=PC->GetLocalPlayer())if(auto* Input=Local->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
  if(auto* Action=LoadObject<UInputAction>(nullptr,TEXT("/Game/Constellation/Input/IA_Attack.IA_Attack")))Toast->TargetKeys=Input->QueryKeysMappedToAction(Action);
 Toast->FooterText=FText::FromString(TEXT("공격 기능이 해금되었습니다."));Toast->AddToViewport(15);AttackToast=Toast;bToastPending=false;
 UE_LOG(LogTemp,Display,TEXT("SwordAcquisition toast after input restoration"));
}
void ASwordAcquisitionStage::Tick(float Dt)
{
 Super::Tick(Dt);
 if(bAnimationInstalled)TickAnimation();
 if(bToastPending)ShowToast();
 if(!Director.IsValid()&&!bCompleted&&IsValid(Sword)&&CombatUnlocked()){bCompleted=true;Sword->SetActorHiddenInGame(true);Sword->SetActorEnableCollision(false);}
}
void ASwordAcquisitionStage::EndPlay(const EEndPlayReason::Type Reason)
{bToastPending=false;if(Director.IsValid()||ItemRequest.IsValid())Restore(!bCommitted);if(AttackToast)AttackToast->RemoveFromParent();Super::EndPlay(Reason);}
bool USwordAcquisitionAction::Execute_Implementation(ASceneDirectorPlayer* P,AActor* Target,const FDirectorActionParameters& Params,FString& Error)
{
 auto* Stage=Cast<ASwordAcquisitionStage>(Target?Target:(P?P->ResolveObject(TEXT("SwordStage")):nullptr));
 if(Stage&&Stage->RunCue(P,Params.Identifier))return true;
 Error=TEXT("Sword acquisition cue failed: ")+Params.Identifier.ToString();return false;
}
