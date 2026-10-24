#include "JumpAcquisitionStage.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "AbilityAcquisitionSubsystem.h"
#include "SceneDirectorPlayer.h"
#include "TutorialPromptWidget.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "UObject/UnrealType.h"
#include "UObject/StructOnScope.h"
#include "InputCoreTypes.h"

AJumpAcquisitionStage::AJumpAcquisitionStage()
{
 PrimaryActorTick.bCanEverTick=true;
 SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
 Motes=CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("AbsorptionMotes"));Motes->SetupAttachment(RootComponent);Motes->SetCollisionEnabled(ECollisionEnabled::NoCollision);Motes->SetCastShadow(false);
 Light=CreateDefaultSubobject<UPointLightComponent>(TEXT("StarResponseLight"));Light->SetupAttachment(RootComponent);Light->SetLightColor(FLinearColor(1,.65,.2));Light->SetIntensity(0);Light->SetAttenuationRadius(260);Light->SetCastShadows(false);
 FaceFill=CreateDefaultSubobject<UPointLightComponent>(TEXT("FaceFill"));FaceFill->SetupAttachment(RootComponent);FaceFill->SetLightColor(FLinearColor(.8f,.86f,1.f));FaceFill->SetIntensity(0);FaceFill->SetAttenuationRadius(220);FaceFill->SetCastShadows(false);FaceFill->SetIndirectLightingIntensity(0);
}
UActorComponent* AJumpAcquisitionStage::Ability()const
{
 auto* Pawn=Character.IsValid()?Character.Get():(GetWorld()&&GetWorld()->GetFirstPlayerController()?Cast<ACharacter>(GetWorld()->GetFirstPlayerController()->GetPawn()):nullptr);
 if(Pawn)for(auto* C:Pawn->GetComponents())if(C&&FindFProperty<FBoolProperty>(C->GetClass(),TEXT("IsJumpUnlocked")))return C;return nullptr;
}
bool AJumpAcquisitionStage::RunCue(ASceneDirectorPlayer* P,FName Cue,float Seconds)
{
 if(!P)return false;
 auto* PC=GetWorld()->GetFirstPlayerController();
 if(Cue==TEXT("Begin"))
 {
  if(Director.IsValid()||!IsValid(Star)||bCompleted||!PC)return false;
  Character=Cast<ACharacter>(PC->GetPawn());if(!Character.IsValid()||!Ability())return false;
  if(FindFProperty<FBoolProperty>(Ability()->GetClass(),TEXT("IsJumpUnlocked"))->GetPropertyValue_InContainer(Ability())){bCompleted=true;Star->SetActorHiddenInGame(true);Star->SetActorEnableCollision(false);return false;}
  StarMesh=Star->FindComponentByClass<UStaticMeshComponent>();if(!StarMesh)return false;
  auto* Mesh=Character->GetMesh();bOldPostDisabled=Mesh->GetDisablePostProcessBlueprint();
  auto* Anim=Mesh->GetAnimInstance();if(!Anim||Anim->IsAnyMontagePlaying())return false;
  RuntimeMontages.Empty();
  for(FName Name:{FName("Inspect"),FName("Reach"),FName("Surprise"),FName("Absorb"),FName("Chest"),FName("Palm")})
  {
   auto* Source=AnimationMontages.FindRef(Name).Get();if(!Source)return false;
   auto* Copy=DuplicateObject<UAnimMontage>(Source,this);Copy->SetFlags(RF_Transient);
   // Hold the approved end pose through graph waits and the blocking ability UI.
   // Never edit the delivered montage assets or their timing.
   Copy->bEnableAutoBlendOut=false;RuntimeMontages.Add(Name,Copy);
  }
  Mesh->SetDisablePostProcessBlueprint(true);bAnimationInstalled=true;
  Director=P;P->OnDirectorStopped.AddDynamic(this,&AJumpAcquisitionStage::Finished);
  BeforeCharacter=Character->GetActorTransform();BeforeStar=StarMesh->GetComponentTransform();StarCenter=StarMesh->GetComponentLocation();bOldStarHidden=Star->IsHidden();bOldCollision=Star->GetActorEnableCollision();
  auto* Move=Character->GetCharacterMovement();OldMovement=Move->MovementMode;OldCustom=Move->CustomMovementMode;Move->StopMovementImmediately();Move->DisableMovement();
  // Small staging adjustment inside the existing interaction radius; no stand-in character.
  Character->SetActorTransform(HeroineTransform,false,nullptr,ETeleportType::TeleportPhysics);PC->FlushPressedKeys();Star->SetActorEnableCollision(false);
  FaceFill->SetWorldLocation(HeroineTransform.TransformPosition(FVector(45,70,85)));FaceFill->SetIntensity(FaceFillIntensity);
  StarMesh->SetMobility(EComponentMobility::Movable);
  Motes->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Sphere.Sphere")));Motes->SetMaterial(0,ParticleMaterial);Motes->ClearInstances();
  for(int32 I=0;I<48;I++)Motes->AddInstance(FTransform(FRotator::ZeroRotator,StarCenter,FVector::ZeroVector),true);
  ContactPosition=StarCenter;
  Phase=Cue;Elapsed=0;return true;
 }
 if(Director!=P||!Character.IsValid())return false;
 if(Cue==TEXT("White")){PC->PlayerCameraManager->StartCameraFade(0,1,FMath::Max(.05f,Seconds),FLinearColor::White,false,true);return true;}
 if(Cue==TEXT("AbilityUI"))
 {
  auto* UI=GetWorld()->GetSubsystem<UAbilityAcquisitionSubsystem>();int32 Mask=0;
  const FName Flags[]={TEXT("IsJumpUnlocked"),TEXT("IsCombatUnlocked"),TEXT("IsTransformUnlocked")};
  for(int32 I=0;I<3;I++)if(auto* B=FindFProperty<FBoolProperty>(Ability()->GetClass(),Flags[I]);B&&B->GetPropertyValue_InContainer(Ability()))Mask|=1<<I;
  return UI&&UI->PresentForScene(P,0,Mask);
 }
 if(Cue==TEXT("Commit"))
 {
  auto* UI=GetWorld()->GetSubsystem<UAbilityAcquisitionSubsystem>();
  bCommitRequested=UI&&UI->GrantPresentedAbility(Ability(),0);return bCommitRequested;
 }
 auto* Anim=Character->GetMesh()->GetAnimInstance();if(!Anim)return false;
 if(auto* Montage=RuntimeMontages.FindRef(Cue).Get())
 {
  // Adjacent clips share an authored boundary pose. A zero-duration handover
  // avoids mixing that pose with locomotion or shortening either source clip.
  const float Blend=ActiveMontage?0.f:.15f;
  if(Anim->Montage_PlayWithBlendIn(Montage,FAlphaBlendArgs(Blend),1.f)<=0)return false;
  ActiveMontage=Montage;
 }
 else if(Cue==TEXT("Contact"))ContactPosition=Character->GetMesh()->GetSocketLocation(TEXT("index_03_r"));
 else if(Cue==TEXT("Release")){if(ActiveMontage)Anim->Montage_Stop(.35f,ActiveMontage);ActiveMontage=nullptr;}
 else return false;
 Phase=Cue;Elapsed=0;Duration=FMath::Max(.05f,Seconds);
 UE_LOG(LogTemp,Display,TEXT("JumpAcquisition cue=%s duration=%.2f"),*Cue.ToString(),Seconds);return true;
}
void AJumpAcquisitionStage::Tick(float Dt)
{
 Super::Tick(Dt);
 if(!Director.IsValid())
 {
  // Ability state is authoritative across map visits, where event state is visit-local.
  if(!bCompleted&&IsValid(Star))if(auto* C=Ability();C&&FindFProperty<FBoolProperty>(C->GetClass(),TEXT("IsJumpUnlocked"))->GetPropertyValue_InContainer(C)){bCompleted=true;Star->SetActorHiddenInGame(true);Star->SetActorEnableCollision(false);}
  return;
 }
 if(!Character.IsValid())return;
 if(auto* Camera=Cast<ACameraActor>(Director->FindCamera(TEXT("JumpCamera"))))
 {
  auto* View=Camera->GetCameraComponent();View->SetConstraintAspectRatio(false);
  View->PostProcessSettings.bOverride_MotionBlurAmount=true;View->PostProcessSettings.MotionBlurAmount=0;
 }
 Elapsed+=Dt;float T=FMath::Clamp(Elapsed/Duration,0.f,1.f);float Smooth=T*T*(3-2*T);
 if(Phase==TEXT("Contact")||Phase==TEXT("Surprise"))
 {
  Light->SetWorldLocation(StarCenter);Light->SetIntensity(ContactLightIntensity*FMath::Sin(FMath::Min(Elapsed,.5f)*PI));
  const FVector F=HeroineTransform.GetRotation().GetForwardVector(),R=HeroineTransform.GetRotation().GetRightVector();
  for(int32 I=0;I<48;I++){float A=I*2*PI/48;FVector Pos=ContactPosition+(R*FMath::Cos(A)+FVector::UpVector*FMath::Sin(A))*(8+T*20);Motes->UpdateInstanceTransform(I,FTransform(FRotator::ZeroRotator,Pos,FVector(.013*(1-T))),true,false,true);}Motes->MarkRenderStateDirty();
 }
 else if(Phase==TEXT("Absorb"))
 {
  const FVector Chest=HeroineTransform.TransformPosition(FVector(9,0,43));
  const float Shrink=1-FMath::SmoothStep(0.f,.85f,T);StarMesh->SetWorldScale3D(BeforeStar.GetScale3D()*Shrink);StarMesh->SetWorldLocation(FMath::Lerp(StarCenter,Chest,Smooth));
  for(int32 I=0;I<48;I++)
  {
   const float A=I*2.399963f,Progress=FMath::Clamp(T*1.5f-I/48.f*.45f,0.f,1.f),Radius=(1-Progress)*25;
   FVector Pos=FMath::Lerp(StarCenter,Chest,Progress)+FVector(0,FMath::Cos(A+Progress*7)*Radius,FMath::Sin(A+Progress*7)*Radius);
   float Size=.018f*(1-Progress)*FMath::Clamp(T*8,0.f,1.f);Motes->UpdateInstanceTransform(I,FTransform(FRotator::ZeroRotator,Pos,FVector(Size)),true,false,true);
  }
  Motes->MarkRenderStateDirty();Light->SetWorldLocation(FMath::Lerp(StarCenter,Chest,Smooth));Light->SetIntensity(AbsorptionLightIntensity*FMath::Sin(T*PI));if(T>=1)Star->SetActorHiddenInGame(true);
 }
 else if(Phase==TEXT("Chest")||Phase==TEXT("Palm")||Phase==TEXT("Release")){Light->SetIntensity(0);Motes->ClearInstances();}
}
void AJumpAcquisitionStage::Restore(bool Cancelled)
{
 // The event subsystem may mark the runner pending-kill earlier in this same
 // stopped broadcast. Its UObject is still alive: release its UI lease as well.
 if(auto* P=Director.Get(true)){if(auto* UI=GetWorld()->GetSubsystem<UAbilityAcquisitionSubsystem>())UI->CancelScene(P);P->OnDirectorStopped.RemoveDynamic(this,&AJumpAcquisitionStage::Finished);}
 if(auto* C=Character.Get())
 {
  if(auto* Anim=C->GetMesh()->GetAnimInstance();Anim&&ActiveMontage)Anim->Montage_Stop(Cancelled?0.f:.35f,ActiveMontage);
  ActiveMontage=nullptr;
  if(bAnimationInstalled)C->GetMesh()->SetDisablePostProcessBlueprint(bOldPostDisabled);
  bAnimationInstalled=false;RuntimeMontages.Empty();
  if(Cancelled)C->SetActorTransform(BeforeCharacter,false,nullptr,ETeleportType::TeleportPhysics);
  C->GetCharacterMovement()->SetMovementMode(EMovementMode(OldMovement),OldCustom);
 }
 if(IsValid(Star)&&StarMesh){StarMesh->SetWorldTransform(BeforeStar);Star->SetActorHiddenInGame(Cancelled?bOldStarHidden:true);Star->SetActorEnableCollision(Cancelled?bOldCollision:false);}
 if(auto* PC=GetWorld()->GetFirstPlayerController();PC&&PC->PlayerCameraManager)PC->PlayerCameraManager->StopCameraFade();
 Light->SetIntensity(0);FaceFill->SetIntensity(0);Motes->ClearInstances();Director.Reset();Phase=Cancelled?TEXT("Cancelled"):TEXT("Completed");
}
void AJumpAcquisitionStage::Finished(bool Done)
{
 const bool Granted=bCommitRequested; // Commit is the final graph action; failure stops before completion is recorded.
 bCompleted=Granted;Restore(!Granted);bCommitRequested=false;
 if(Granted&&Star)
 {
  if(auto* Flag=FindFProperty<FBoolProperty>(Star->GetClass(),TEXT("bIsInteracted")))Flag->SetPropertyValue_InContainer(Star,true);
  // Same quest-completion multicast used by the original star, without old tutorial/jump callbacks.
  if(auto* Property=FindFProperty<FMulticastDelegateProperty>(Star->GetClass(),TEXT("OnInteractionSequenceComplete")))
  {FStructOnScope Params(Property->SignatureFunction);Property->GetMulticastDelegate(Property->ContainerPtrToValuePtr<void>(Star))->ProcessDelegate<UObject>(Params.GetStructMemory());}
  if(auto* PC=GetWorld()->GetFirstPlayerController()){auto* Toast=CreateWidget<UTutorialPromptWidget>(PC);Toast->Action=ETutorialPromptAction::Jump;Toast->TargetKeys={EKeys::SpaceBar};Toast->AddToViewport(15);}
 }
 UE_LOG(LogTemp,Display,TEXT("JumpAcquisition finished completed=%d granted=%d"),Done,Granted);
}
void AJumpAcquisitionStage::EndPlay(const EEndPlayReason::Type R){if(Director.IsValid())Restore(true);Super::EndPlay(R);}
bool UJumpAcquisitionAction::Execute_Implementation(ASceneDirectorPlayer* P,AActor* Target,const FDirectorActionParameters& Params,FString& Error)
{
 auto* Stage=Cast<AJumpAcquisitionStage>(Target?Target:(P?P->ResolveObject(TEXT("JumpStage")):nullptr));if(Stage&&Stage->RunCue(P,Params.Identifier,Params.Value))return true;
 Error=TEXT("Jump acquisition cue failed: ")+Params.Identifier.ToString();return false;
}
