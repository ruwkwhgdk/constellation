#include "SchoolOpeningSceneActor.h"
#include "RegionTitleWidget.h"
#include "TutorialPromptWidget.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "SceneDirectorPlayer.h"
#include "SceneDirectorTesting.h"
#include "Blueprint/UserWidget.h"
#include "Components/StaticMeshComponent.h"
#include "Components/AudioComponent.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Kismet/GameplayStatics.h"
#include "Widgets/SLeafWidget.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"
#include "UObject/UnrealType.h"
#include "TimerManager.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "ConstellationFXLibrary.h"
#include "ConstellationFXActor.h"

class SSchoolEyeMask : public SLeafWidget
{
public:
 SLATE_BEGIN_ARGS(SSchoolEyeMask){} SLATE_ATTRIBUTE(float,Open) SLATE_END_ARGS()
 void Construct(const FArguments& Args){Open=Args._Open;SetVisibility(EVisibility::HitTestInvisible);}
 virtual FVector2D ComputeDesiredSize(float) const override{return FVector2D::ZeroVector;}
 virtual int32 OnPaint(const FPaintArgs&,const FGeometry& G,const FSlateRect&,FSlateWindowElementList& Out,int32 Layer,const FWidgetStyle&,bool) const override
 {
  const FVector2D Size=G.GetLocalSize();const float Height=Size.Y*.5f*(1-FMath::Clamp(Open.Get(),0.f,1.f));
  if(Height>.01f){const auto* Brush=FCoreStyle::Get().GetBrush("WhiteBrush");
   FSlateDrawElement::MakeBox(Out,Layer,G.ToPaintGeometry(FVector2f(Size.X,Height),FSlateLayoutTransform()),Brush,ESlateDrawEffect::None,FLinearColor::Black);
   FSlateDrawElement::MakeBox(Out,Layer,G.ToPaintGeometry(FVector2f(Size.X,Height),FSlateLayoutTransform(FVector2f(0,Size.Y-Height))),Brush,ESlateDrawEffect::None,FLinearColor::Black);}
  return Layer;
 }
 TAttribute<float> Open;
};
ASchoolOpeningSceneActor::ASchoolOpeningSceneActor(){PrimaryActorTick.bCanEverTick=true;RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Root"));}
void ASchoolOpeningSceneActor::BeginPlay()
{
 Super::BeginPlay();bPending=true;bCompleted=false;
 // The bootstrap mask is outside the director. A skipped request never sends
 // Begin/Stopped cues, so it must not acquire presentation or tutorial gates.
 if(DirectorTesting::ShouldSkip(GetWorld())){bPending=false;EyeOpen=1.f;return;}
 if(auto* View=GetWorld()->GetGameViewport())
 {EyeMask=SNew(SSchoolEyeMask).Open_Lambda([Weak=TWeakObjectPtr<ASchoolOpeningSceneActor>(this)](){return Weak.IsValid()?Weak->EyeOpen:1.f;});View->AddViewportWidgetContent(EyeMask.ToSharedRef(),50);}
 if(Locker){TArray<UStaticMeshComponent*> Components;Locker->GetComponents(Components);for(auto* C:Components)if(C->GetFName()==DoorComponentName){Door=C;DoorClosed=C->GetRelativeRotation();C->SetMobility(EComponentMobility::Movable);break;}}
}
void ASchoolOpeningSceneActor::Tick(float Dt)
{
 Super::Tick(Dt);
 // S0 blends to an unconstrained gameplay view: do not drop pillarboxes at handoff.
 if(Director.IsValid())if(auto* Camera=Cast<ACameraActor>(Director->FindCamera(TEXT("Eyes"))))Camera->GetCameraComponent()->SetConstraintAspectRatio(false);
 if(bGirlLooking){GirlLookElapsed+=Dt;GirlGaze.Update(GirlLookTarget,FMath::Clamp(GirlLookElapsed/.4f,0.f,1.f));}
 if(LockerCharacter.IsValid())
 {
  // Do not render the previous gameplay pose at the newly teleported locker position.
  // Let the montage evaluate before exposing the first-person body/arm.
  if(bLockerPosePending&&GFrameCounter>LockerPoseStartFrame+1)
  {LockerCharacter->GetMesh()->SetVisibility(bBeforeLockerMeshVisible);bLockerPosePending=false;}
  if(LockerPhase==TEXT("Recovering"))
  {
   RecoveryElapsed+=Dt;
   if(RecoveryElapsed>=RecoveryDuration)
   {LockerCharacter->GetMesh()->GetAnimInstance()->Montage_Stop(.35f,LockerMontage);LockerPhase=TEXT("Settling");SettleElapsed=0;}
  }
  else if(LockerPhase==TEXT("Settling"))
  {SettleElapsed+=Dt;if(SettleElapsed>=.4f)LockerPhase=TEXT("Ready");}
  else if(LockerPhase==TEXT("Falling")&&LockerCharacter->GetMesh()->GetAnimInstance()->Montage_GetCurrentSection(LockerMontage)==TEXT("ProneHold"))LockerPhase=TEXT("ProneHold");
 }
 if(EyeMask.IsValid()&&Director.IsValid()&&Director->HasStartedEyeEffect())RemoveMask();
 if(Song&&Girl)Song->SetWorldLocation(Girl->GetActorLocation()+FVector(0,0,70));
 if(bPending&&!bStarted){BootstrapTime+=Dt;if(BootstrapTime>45.f){UE_LOG(LogTemp,Error,TEXT("S0 did not start within 45 seconds; releasing opening mask"));DirectorStopped(false);}}
 if(EyeDuration>0){EyeTime+=Dt;EyeOpen=FMath::InterpEaseInOut(EyeFrom,EyeTo,FMath::Clamp(EyeTime/EyeDuration,0.f,1.f),2.f);if(EyeTime>=EyeDuration)EyeDuration=0;}
 if(Door&&DoorDuration>0){DoorTime+=Dt;float Alpha=FMath::InterpEaseInOut(0.f,1.f,FMath::Clamp(DoorTime/DoorDuration,0.f,1.f),2.f);Door->SetRelativeRotation(DoorClosed+FRotator(0,DoorOpenAngle*Alpha,0));if(DoorTime>=DoorDuration)DoorDuration=0;}
}
bool ASchoolOpeningSceneActor::RunCue(ASceneDirectorPlayer* Player,FName Cue,float Seconds)
{
 if(!IsValid(Player))return false;
 if(Cue==TEXT("Begin"))
 {if(Director.IsValid()&&Director!=Player)return false;bStarted=true;bPending=true;bCompleted=false;Director=Player;if(Girl)Girl->SetActorHiddenInGame(false);
 if(!EyeMask.IsValid()){EyeOpen=0;if(auto* View=GetWorld()->GetGameViewport()){EyeMask=SNew(SSchoolEyeMask).Open_Lambda([Weak=TWeakObjectPtr<ASchoolOpeningSceneActor>(this)](){return Weak.IsValid()?Weak->EyeOpen:1.f;});View->AddViewportWidgetContent(EyeMask.ToSharedRef(),50);}}
 // Bootstrap mask remains until the common eyelid cue actually starts.
 Player->OnDirectorStopped.AddUniqueDynamic(this,&ASchoolOpeningSceneActor::DirectorStopped);return Door!=nullptr;}
 if(Cue==TEXT("PeekStart")||Cue==TEXT("PeekEnd")){EyeFrom=EyeOpen;EyeTo=Cue==TEXT("PeekStart")?.16f:1.f;EyeTime=0;EyeDuration=.3f;return true;}
 if(Cue==TEXT("OpenEyes")||Cue==TEXT("CloseEyes")){EyeFrom=EyeOpen;EyeTo=Cue==TEXT("OpenEyes")?1.f:0.f;EyeTime=0;EyeDuration=FMath::Max(.01f,Seconds);return true;}
 if(Cue==TEXT("PlayGirlSong")){StopSound();if(GirlSong)Song=UGameplayStatics::SpawnSoundAtLocation(this,GirlSong,GetActorLocation(),FRotator::ZeroRotator,.25f);return true;}
 if(Cue==TEXT("StopGirlSong")){StopSound();return true;}
 if(Cue==TEXT("PlayGirlRun")){if(RunSound){RunSound->Stop();RunSound=nullptr;}if(GirlRunSound&&Girl)RunSound=UGameplayStatics::SpawnSoundAttached(GirlRunSound,Girl->GetRootComponent());return true;}
 if(Cue==TEXT("OpenDoor")){if(!Door)return false;StartGirlLook();DoorTime=0;DoorDuration=FMath::Max(.01f,Seconds);if(DoorSound)UGameplayStatics::PlaySoundAtLocation(this,DoorSound,Door->GetComponentLocation());return true;}
 if(Cue==TEXT("StopGirlLook")){bGirlLooking=false;GirlGaze.Reset();return true;}
 if(Cue==TEXT("ThirdPerson"))
 {if(LockerCharacter.IsValid()&&bLockerHeadHiddenByScene){LockerCharacter->GetMesh()->UnHideBoneByName(TEXT("head"));bLockerHeadHiddenByScene=false;}return true;}
 if(Cue==TEXT("Fall")){if(!StartLockerMotion())return false;if(FallSound)UGameplayStatics::PlaySoundAtLocation(this,FallSound,FallTransform.GetLocation());return true;}
 if(Cue==TEXT("FallImpact"))
 {
  if(!LockerCharacter.IsValid())return false;
  // Two small puffs flank the contact point, leaving the girl's escape visible.
  FVector Contact=(LockerCharacter->GetMesh()->GetSocketLocation(TEXT("hand_l"))+LockerCharacter->GetMesh()->GetSocketLocation(TEXT("hand_r")))*.5f;
  FHitResult Hit;FCollisionQueryParams Query;Query.AddIgnoredActor(LockerCharacter.Get());
  if(GetWorld()->LineTraceSingleByChannel(Hit,Contact+FVector(0,0,80),Contact-FVector(0,0,250),ECC_WorldStatic,Query))Contact.Z=Hit.ImpactPoint.Z+3;
  else Contact.Z=FallTransform.GetLocation().Z-LockerCharacter->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()+3;
  for(float Side:{-48.f,48.f})if(auto* FX=UConstellationFXLibrary::SpawnEffect(this,EConstellationFXKind::RunDust,Contact+FVector(-75,Side,0),FVector::UpVector,FLinearColor(.38f,.34f,.28f,.65f),1.1f))
  {FX->SetOwner(Player);Player->OnDirectorStopped.AddUniqueDynamic(FX,&AConstellationFXActor::OnSceneStopped);}
  return true;
 }
 if(Cue==TEXT("Recover"))
 {
  if(!LockerCharacter.IsValid()||LockerPhase!=TEXT("ProneHold"))return false;
  auto* Anim=LockerCharacter->GetMesh()->GetAnimInstance();
  Anim->Montage_JumpToSection(TEXT("GetUp"),LockerMontage);
  RecoveryDuration=LockerMontage->GetSectionLength(LockerMontage->GetSectionIndex(TEXT("GetUp")));
  RecoveryElapsed=0;LockerPhase=TEXT("Recovering");return true;
 }
 if(Cue==TEXT("PrepareHandoff"))
 {auto* Character=LockerCharacter.Get();if(!Character||LockerPhase!=TEXT("Ready"))return false;Player->GameplayPose=Character->GetActorTransform();RestoreLockerMotion(false);LockerPhase=TEXT("Complete");RemoveMask();return true;}
 return false;
}
void ASchoolOpeningSceneActor::StopSound(){if(Song){Song->Stop();Song->DestroyComponent();Song=nullptr;}}
void ASchoolOpeningSceneActor::StartGirlLook()
{
 if(!Girl)return;
 TArray<USkeletalMeshComponent*> Meshes;Girl->GetComponents(Meshes);
 for(auto* Mesh:Meshes)if(auto* Asset=Mesh->GetSkeletalMeshAsset())
 {
  const auto& Ref=Asset->GetRefSkeleton();int32 Bone=Ref.FindBoneIndex(TEXT("head"));if(Bone==INDEX_NONE)continue;
  FTransform Head=Ref.GetRefBonePose()[Bone];
  while((Bone=Ref.GetParentIndex(Bone))!=INDEX_NONE)Head=Head*Ref.GetRefBonePose()[Bone];
  FString Error;
  if(GirlGaze.Initialize(Mesh,TEXT("head"),Head.GetRotation().Inverse().RotateVector(FVector::ForwardVector),Error))
  {bGirlLooking=true;GirlLookElapsed=0;GirlGaze.Update(GirlLookTarget,0);}
  else UE_LOG(LogTemp,Warning,TEXT("S0 girl gaze: %s"),*Error);
  return;
 }
}
void ASchoolOpeningSceneActor::RemoveMask(){if(EyeMask.IsValid()){if(GetWorld()&&GetWorld()->GetGameViewport())GetWorld()->GetGameViewport()->RemoveViewportWidgetContent(EyeMask.ToSharedRef());EyeMask.Reset();}}
void ASchoolOpeningSceneActor::DirectorStopped(bool Completed)
{
 GetWorldTimerManager().ClearTimer(MovementTutorialTimer);
 bGirlLooking=false;GirlGaze.Reset();
 if(RunSound){RunSound->Stop();RunSound=nullptr;}
 RestoreLockerMotion(!Completed);
 bCompleted=Completed;bPending=false;StopSound();RemoveMask();EyeDuration=DoorDuration=0;
 if(!Completed&&Door)Door->SetRelativeRotation(DoorClosed);
 if(Completed&&Girl)Girl->SetActorHiddenInGame(true);
 if(Director.IsValid())Director->OnDirectorStopped.RemoveDynamic(this,&ASchoolOpeningSceneActor::DirectorStopped);Director.Reset();
 if(Completed)
 {auto* PC=UGameplayStatics::GetPlayerController(this,0);if(PC){GetWorldTimerManager().ClearTimer(TitleTimer);if(RegionTitle)RegionTitle->RemoveFromParent();RegionTitle=CreateWidget<UUserWidget>(PC,RegionTitleClass?RegionTitleClass:TSubclassOf<UUserWidget>(URegionTitleWidget::StaticClass()));
 if(auto* Title=Cast<URegionTitleWidget>(RegionTitle))Title->SetRegionText(FText::FromString(TEXT("폐교")),FText::FromString(TEXT("텅 빈 교실")));
  if(RegionTitle){for(auto Pair:{TPair<FName,FString>(TEXT("RegionTitleName"),TEXT("폐교")),TPair<FName,FString>(TEXT("RegionTitleDesc"),TEXT("텅 빈 교실"))})if(auto* Property=FindFProperty<FTextProperty>(RegionTitle->GetClass(),Pair.Key))Property->SetPropertyValue_InContainer(RegionTitle,FText::FromString(Pair.Value));
   RegionTitle->AddToViewport(10);RegionTitle->SetVisibility(ESlateVisibility::HitTestInvisible);if(!RegionTitle->IsA<URegionTitleWidget>())GetWorldTimerManager().SetTimer(TitleTimer,[this](){if(RegionTitle){RegionTitle->RemoveFromParent();RegionTitle=nullptr;}},4.f,false);}GetWorldTimerManager().SetTimer(MovementTutorialTimer,this,&ASchoolOpeningSceneActor::ShowMovementTutorial,4.5f,false);}}
}
void ASchoolOpeningSceneActor::ShowMovementTutorial()
{
 auto* PC=UGameplayStatics::GetPlayerController(this,0);if(!PC||!bCompleted)return;
 TArray<UUserWidget*> Existing;UWidgetBlueprintLibrary::GetAllWidgetsOfClass(this,Existing,UTutorialPromptWidget::StaticClass(),false);
 for(auto* Widget:Existing)if(auto* Prompt=Cast<UTutorialPromptWidget>(Widget))
  if(Prompt->GetOwningPlayer()==PC&&Prompt->IsInViewport()&&(Prompt->Action==ETutorialPromptAction::Movement||Prompt->TargetKeys.Contains(EKeys::W)))return;
 auto* Prompt=CreateWidget<UTutorialPromptWidget>(PC,UTutorialPromptWidget::StaticClass());
 if(Prompt){Prompt->Action=ETutorialPromptAction::Movement;Prompt->TargetKeys={EKeys::W,EKeys::A,EKeys::S,EKeys::D};Prompt->AddToViewport(15);}
}
void ASchoolOpeningSceneActor::EndPlay(const EEndPlayReason::Type Reason){bGirlLooking=false;GirlGaze.Reset();RestoreLockerMotion(true);StopSound();if(RunSound){RunSound->Stop();RunSound=nullptr;}RemoveMask();GetWorldTimerManager().ClearTimer(TitleTimer);GetWorldTimerManager().ClearTimer(MovementTutorialTimer);if(RegionTitle)RegionTitle->RemoveFromParent();Super::EndPlay(Reason);}

bool ASchoolOpeningSceneActor::StartLockerMotion()
{
 auto* Character=UGameplayStatics::GetPlayerCharacter(this,0);
 if(!Character||!LockerMontage||LockerCharacter.IsValid())return false;
 auto* Mesh=Character->GetMesh();auto* Anim=Mesh?Mesh->GetAnimInstance():nullptr;
 if(!Anim||LockerMontage->GetSectionIndex(TEXT("ProneHold"))==INDEX_NONE||LockerMontage->GetSectionIndex(TEXT("GetUp"))==INDEX_NONE)return false;
 auto* Move=Character->GetCharacterMovement();auto* Capsule=Character->GetCapsuleComponent();
 BeforeLockerTransform=Character->GetActorTransform();
 BeforeMovementMode=Move->MovementMode;BeforeCustomMode=Move->CustomMovementMode;
 BeforeRootMotionMode=Anim->RootMotionMode;BeforeAnimTick=uint8(Mesh->VisibilityBasedAnimTickOption);BeforeCollision=uint8(Capsule->GetCollisionEnabled());
 // This imported mesh has reference-pose bounds only 28 cm deep. The authored
 // reach/fall deforms outside them, so an otherwise visible hand can be culled.
 BeforeLockerBoundsScale=Mesh->BoundsScale;
 FTransform Start=FallTransform;
 FHitResult Floor;FCollisionQueryParams Query(SCENE_QUERY_STAT(LockerFloor),false,Character);
 const FVector Location=Start.GetLocation();
 if(!GetWorld()->LineTraceSingleByChannel(Floor,Location+FVector(0,0,150),Location-FVector(0,0,300),ECC_Visibility,Query))return false;
 Start.SetLocation(FVector(Location.X,Location.Y,Floor.ImpactPoint.Z-Mesh->GetRelativeLocation().Z+.15f));
 LockerCharacter=Character;
 Mesh->SetBoundsScale(FMath::Max(10.f,BeforeLockerBoundsScale));
 Move->StopMovementImmediately();Move->SetMovementMode(MOVE_Flying);
 Capsule->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 Character->SetActorTransform(Start,false,nullptr,ETeleportType::TeleportPhysics);
 Character->SetActorHiddenInGame(false);
 Mesh->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
 Anim->SetRootMotionMode(ERootMotionMode::RootMotionFromMontagesOnly);
 if(Anim->Montage_Play(LockerMontage,1.f)<=0){RestoreLockerMotion(true);return false;}
 bBeforeLockerMeshVisible=Mesh->IsVisible();Mesh->SetVisibility(false);bLockerPosePending=true;LockerPoseStartFrame=GFrameCounter;
 bLockerHeadHiddenByScene=bUseFirstPersonHeadMask&&Mesh->GetBoneIndex(TEXT("head"))!=INDEX_NONE&&!Mesh->IsBoneHiddenByName(TEXT("head"));
 if(bLockerHeadHiddenByScene)Mesh->HideBoneByName(TEXT("head"),PBO_None);
 LockerPhase=TEXT("Falling");return true;
}

void ASchoolOpeningSceneActor::RestoreLockerMotion(bool Cancelled)
{
 auto* Character=LockerCharacter.Get();if(!Character)return;
 auto* Mesh=Character->GetMesh();
 if(bLockerPosePending){Mesh->SetVisibility(bBeforeLockerMeshVisible);bLockerPosePending=false;}
 if(bLockerHeadHiddenByScene){Mesh->UnHideBoneByName(TEXT("head"));bLockerHeadHiddenByScene=false;}
 if(auto* Anim=Mesh->GetAnimInstance()){Anim->Montage_Stop(0.f,LockerMontage);Anim->SetRootMotionMode(ERootMotionMode::Type(BeforeRootMotionMode));}
 Mesh->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption(BeforeAnimTick);
 Mesh->SetBoundsScale(BeforeLockerBoundsScale);
 Character->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::Type(BeforeCollision));
 auto* Move=Character->GetCharacterMovement();Move->StopMovementImmediately();Move->SetMovementMode(EMovementMode(BeforeMovementMode),BeforeCustomMode);
 if(Cancelled){Character->SetActorTransform(BeforeLockerTransform,false,nullptr,ETeleportType::TeleportPhysics);LockerPhase=TEXT("Cancelled");}
 // Director owns visibility restoration on both completion and cancellation.
 LockerCharacter.Reset();
}

bool ASchoolOpeningSceneActor::IsGameplayInputAvailable() const
{auto* PC=UGameplayStatics::GetPlayerController(this,0);auto* View=GetWorld()?GetWorld()->GetGameViewport():nullptr;return PC&&View&&!View->IgnoreInput()&&!PC->IsMoveInputIgnored()&&!PC->IsLookInputIgnored();}

