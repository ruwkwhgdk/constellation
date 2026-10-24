#include "SchoolGateOpeningComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/AudioComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundAttenuation.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
USchoolGateOpeningComponent::USchoolGateOpeningComponent(){PrimaryComponentTick.bCanEverTick=true;PrimaryComponentTick.bStartWithTickEnabled=false;}
float USchoolGateOpeningComponent::OpeningAngle(float T)
{
 const float Times[]={0,.85f,1.65f,2.f,5.f,5.8f,8.f,8.5f};
 const float Angles[]={0,0,5,4.8f,20,24,90,90};
 const float Speeds[]={0,0,0,0,5.5f,7.f,0,0};
 for(int I=1;I<8;++I)if(T<=Times[I])
 {
  const float H=Times[I]-Times[I-1],A=FMath::Clamp((T-Times[I-1])/H,0.f,1.f);
  const float A2=A*A,A3=A2*A;
  return (2*A3-3*A2+1)*Angles[I-1]+(A3-2*A2+A)*H*Speeds[I-1]+(-2*A3+3*A2)*Angles[I]+(A3-A2)*H*Speeds[I];
 }
 return 90;
}
bool USchoolGateOpeningComponent::BeginOpening(AActor* Gate,AActor* Interactor)
{
 auto* C=Cast<ACharacter>(Interactor);if(!IsValid(Gate)||!IsValid(C))return false;
 auto* G=Gate->FindComponentByClass<USchoolGateOpeningComponent>();
 if(!G){G=NewObject<USchoolGateOpeningComponent>(Gate);Gate->AddInstanceComponent(G);G->RegisterComponent();}
 return G->Start(C);
}
bool USchoolGateOpeningComponent::Start(ACharacter* C)
{
 if(bOpening||bCompleted)return false;
 bCharacterReleased=false;
 auto* PC=Cast<APlayerController>(C->GetController());auto* Anim=C->GetMesh()->GetAnimInstance();
 const FVector GateScale=GetOwner()->GetActorScale3D();
 const TCHAR* MontagePath=FMath::Abs(GateScale.Y)>5.f ? TEXT("/Game/Constellation/Characters/Heroine/GamePilot/Gate/AM_GateOpen.AM_GateOpen") : (FMath::Abs(GateScale.X)<4.25f ? TEXT("/Game/Constellation/Characters/Heroine/GamePilot/Gate/AM_GateOpen_Narrow.AM_GateOpen_Narrow") : TEXT("/Game/Constellation/Characters/Heroine/GamePilot/Gate/AM_GateOpen_Entry.AM_GateOpen_Entry"));
 Montage=LoadObject<UAnimMontage>(nullptr,MontagePath);
 if(!PC||!Anim||!Montage||Anim->IsAnyMontagePlaying())return false;
 TArray<UStaticMeshComponent*> Meshes;GetOwner()->GetComponents(Meshes);
 for(auto* M:Meshes){if(M->GetFName()==TEXT("DoorLeft"))Left=M;if(M->GetFName()==TEXT("DoorRight"))Right=M;}
 if(!Left||!Right)return false;
 // Position in world centimetres; gate instances have non-uniform, very large scales.
 const FVector Forward=GetOwner()->GetActorForwardVector();const FVector Center=(Left->GetComponentLocation()+Right->GetComponentLocation())*.5f;
 const FVector Scale=GetOwner()->GetActorScale3D();
 const auto* Leaf=Cast<UStaticMeshComponent>(Left);const FBox Bounds=Leaf->GetStaticMesh()->GetBoundingBox();
 const float SurfaceOffset=FMath::Max(FMath::Abs(Bounds.Min.X),FMath::Abs(Bounds.Max.X))*FMath::Abs(Leaf->GetComponentScale().X);
 PushRadius=85.f*FMath::Abs(Scale.Y)-17.5f;LeafHalfThickness=1.5f*FMath::Abs(Scale.X);
 FVector Start=Center+Forward*(SurfaceOffset+20.2825f);Start.Z=C->GetActorLocation().Z;
 const FRotator Facing=(-Forward).Rotation();FHitResult Hit;
 C->GetCapsuleComponent()->IgnoreActorWhenMoving(GetOwner(),true);
 C->SetActorLocationAndRotation(Start,FRotator(0,Facing.Yaw,0),true,&Hit,ETeleportType::None);
 if(FVector::Dist2D(C->GetActorLocation(),Start)>5){C->GetCapsuleComponent()->IgnoreActorWhenMoving(GetOwner(),false);return false;}
 StartLocation=C->GetActorLocation();TravelDirection=-Forward;Character=C;Controller=PC;auto* Move=C->GetCharacterMovement();Move->StopMovementImmediately();
 bUseControllerYaw=C->bUseControllerRotationYaw;bOrientToMovement=Move->bOrientRotationToMovement;bUseDesiredRotation=Move->bUseControllerDesiredRotation;
 C->bUseControllerRotationYaw=false;Move->bOrientRotationToMovement=false;Move->bUseControllerDesiredRotation=false;
 PC->SetControlRotation(FRotator(PC->GetControlRotation().Pitch,Facing.Yaw,0));
 bInputWasEnabled=C->InputEnabled();if(bInputWasEnabled)C->DisableInput(PC);
 PC->SetIgnoreMoveInput(true);bMoveLock=true;PC->SetIgnoreLookInput(true);bLookLock=true;
 if(Anim->Montage_Play(Montage,1.f)<=0){Finish(true);return false;}
 bOpening=true;bCharacterReleased=false;Elapsed=0;PlaybackSeconds=0;SetComponentTickEnabled(true);ApplyAngle(0);
 if(auto* Sound=LoadObject<USoundBase>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/GamePilot/Gate/S_Gate_HeavyCreak.S_Gate_HeavyCreak")))Audio=UGameplayStatics::SpawnSoundAtLocation(this,Sound,Center,FRotator::ZeroRotator,.8f);
 if(Audio){FSoundAttenuationSettings Settings;Settings.bAttenuate=true;Settings.AttenuationShapeExtents=FVector(250,0,0);Settings.FalloffDistance=1500;Audio->AdjustAttenuation(Settings);}
 return true;
}
void USchoolGateOpeningComponent::ApplyAngle(float Angle){if(Left)Left->SetRelativeRotation(FRotator(0,180-Angle,0));if(Right)Right->SetRelativeRotation(FRotator(0,Angle,0));}
void USchoolGateOpeningComponent::TickComponent(float Dt,ELevelTick T,FActorComponentTickFunction* F)
{
 Super::TickComponent(Dt,T,F);if(!bOpening)return;Elapsed+=Dt;
 if(!bCharacterReleased)
 {
  auto* Anim=IsValid(Character)?Character->GetMesh()->GetAnimInstance():nullptr;
  if(!Anim){Finish(true);return;}
  if(Anim->Montage_IsActive(Montage))PlaybackSeconds=Anim->Montage_GetPosition(Montage);
  else
  {
   if(PlaybackSeconds+Dt<5.3f){Finish(true);return;}
   ReleaseCharacter(false);
   PlaybackSeconds+=Dt;
  }
 }
 else PlaybackSeconds+=Dt;
 ApplyAngle(OpeningAngle(PlaybackSeconds));
 if(!bCharacterReleased)
 {
  // Match the authored contact trajectory in world centimetres for each actual gate size.
  const float PushAngle=OpeningAngle(FMath::Min(PlaybackSeconds,5.f));
  const float Radians=FMath::DegreesToRadians(PushAngle);
  const float Advance=PushRadius*FMath::Sin(Radians)+LeafHalfThickness*(1-FMath::Cos(Radians));
  FVector Target=StartLocation+TravelDirection*Advance;
  // Keep horizontal contact travel exact while following a walkable entrance ramp.
  // Sweeping back to the original Z clips the floor and shortens the push.
  auto* Move=Character->GetCharacterMovement();
  const FVector Current=Character->GetActorLocation();
  Target.Z=Current.Z;
  if(Move->CurrentFloor.IsWalkableFloor())
  {
   const FVector Normal=Move->CurrentFloor.HitResult.ImpactNormal;
   if(Normal.Z>UE_KINDA_SMALL_NUMBER)
    Target.Z-=FVector::DotProduct(Normal,Target-Current)/Normal.Z;
  }
  FHitResult Hit;Character->SetActorLocation(Target,true,&Hit);
  Move->FindFloor(Character->GetActorLocation(),Move->CurrentFloor,false);
  if(Move->CurrentFloor.IsWalkableFloor())Move->AdjustFloorHeight();
  if(FVector::Dist2D(Character->GetActorLocation(),Target)>5){Finish(true);return;}
 }
 if(PlaybackSeconds>=8.5f){Finish(false);return;}
 if(Elapsed>11.f)Finish(true);
}
void USchoolGateOpeningComponent::Finish(bool bInterrupted)
{
 if(bOpening){ApplyAngle(90);bCompleted=true;}
 bOpening=false;SetComponentTickEnabled(false);
 if(Audio){Audio->FadeOut(.15f,0);Audio=nullptr;}
 ReleaseCharacter(bInterrupted);
}
void USchoolGateOpeningComponent::ReleaseCharacter(bool bInterrupted)
{
 if(bCharacterReleased)return;
 if(IsValid(Character))
 {
  if(bInterrupted)if(auto* A=Character->GetMesh()->GetAnimInstance())A->Montage_Stop(.15f,Montage);
  Character->GetCapsuleComponent()->IgnoreActorWhenMoving(GetOwner(),false);
  Character->bUseControllerRotationYaw=bUseControllerYaw;
  auto* M=Character->GetCharacterMovement();M->bOrientRotationToMovement=bOrientToMovement;M->bUseControllerDesiredRotation=bUseDesiredRotation;
  if(bInputWasEnabled&&IsValid(Controller))Character->EnableInput(Controller);
 }
 if(IsValid(Controller)){if(bMoveLock)Controller->SetIgnoreMoveInput(false);if(bLookLock)Controller->SetIgnoreLookInput(false);}
 bMoveLock=false;bLookLock=false;Character=nullptr;Controller=nullptr;bCharacterReleased=true;
}
void USchoolGateOpeningComponent::EndPlay(const EEndPlayReason::Type Reason){if(bOpening)Finish(true);Super::EndPlay(Reason);}
