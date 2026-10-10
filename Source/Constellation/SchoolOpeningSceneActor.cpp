#include "SchoolOpeningSceneActor.h"
#include "SceneDirectorPlayer.h"
#include "Blueprint/UserWidget.h"
#include "Components/StaticMeshComponent.h"
#include "Components/AudioComponent.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Widgets/SLeafWidget.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"
#include "UObject/UnrealType.h"
#include "TimerManager.h"

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
 if(auto* View=GetWorld()->GetGameViewport())
 {EyeMask=SNew(SSchoolEyeMask).Open_Lambda([Weak=TWeakObjectPtr<ASchoolOpeningSceneActor>(this)](){return Weak.IsValid()?Weak->EyeOpen:1.f;});View->AddViewportWidgetContent(EyeMask.ToSharedRef(),50);}
 if(Locker){TArray<UStaticMeshComponent*> Components;Locker->GetComponents(Components);for(auto* C:Components)if(C->GetFName()==DoorComponentName){Door=C;DoorClosed=C->GetRelativeRotation();C->SetMobility(EComponentMobility::Movable);break;}}
}
void ASchoolOpeningSceneActor::Tick(float Dt)
{
 Super::Tick(Dt);
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
 if(Cue==TEXT("OpenDoor")){if(!Door)return false;DoorTime=0;DoorDuration=FMath::Max(.01f,Seconds);if(DoorSound)UGameplayStatics::PlaySoundAtLocation(this,DoorSound,Door->GetComponentLocation());return true;}
 if(Cue==TEXT("Fall")){if(FallSound)UGameplayStatics::PlaySoundAtLocation(this,FallSound,ExitTransform.GetLocation());return true;}
 if(Cue==TEXT("PrepareHandoff"))
 {auto* PC=UGameplayStatics::GetPlayerController(this,0);if(!PC||!PC->GetPawn())return false;PC->GetPawn()->SetActorTransform(ExitTransform,false,nullptr,ETeleportType::TeleportPhysics);Player->GameplayPose=ExitTransform;RemoveMask();return true;}
 return false;
}
void ASchoolOpeningSceneActor::StopSound(){if(Song){Song->Stop();Song->DestroyComponent();Song=nullptr;}}
void ASchoolOpeningSceneActor::RemoveMask(){if(EyeMask.IsValid()){if(GetWorld()&&GetWorld()->GetGameViewport())GetWorld()->GetGameViewport()->RemoveViewportWidgetContent(EyeMask.ToSharedRef());EyeMask.Reset();}}
void ASchoolOpeningSceneActor::DirectorStopped(bool Completed)
{
 bCompleted=Completed;bPending=false;StopSound();RemoveMask();EyeDuration=DoorDuration=0;
 if(!Completed&&Door)Door->SetRelativeRotation(DoorClosed);
 if(Completed&&Girl)Girl->SetActorHiddenInGame(true);
 if(Director.IsValid())Director->OnDirectorStopped.RemoveDynamic(this,&ASchoolOpeningSceneActor::DirectorStopped);Director.Reset();
 if(Completed&&RegionTitleClass)
 {auto* PC=UGameplayStatics::GetPlayerController(this,0);if(PC){RegionTitle=CreateWidget<UUserWidget>(PC,RegionTitleClass);
  if(RegionTitle){for(auto Pair:{TPair<FName,FString>(TEXT("RegionTitleName"),TEXT("폐교")),TPair<FName,FString>(TEXT("RegionTitleDesc"),TEXT("텅 빈 교실"))})if(auto* Property=FindFProperty<FTextProperty>(RegionTitle->GetClass(),Pair.Key))Property->SetPropertyValue_InContainer(RegionTitle,FText::FromString(Pair.Value));
   RegionTitle->AddToViewport(10);RegionTitle->SetVisibility(ESlateVisibility::HitTestInvisible);GetWorldTimerManager().SetTimer(TitleTimer,[this](){if(RegionTitle){RegionTitle->RemoveFromParent();RegionTitle=nullptr;}},4.f,false);}}}
}
void ASchoolOpeningSceneActor::EndPlay(const EEndPlayReason::Type Reason){StopSound();RemoveMask();GetWorldTimerManager().ClearTimer(TitleTimer);if(RegionTitle)RegionTitle->RemoveFromParent();Super::EndPlay(Reason);}

bool ASchoolOpeningSceneActor::IsGameplayInputAvailable() const
{auto* PC=UGameplayStatics::GetPlayerController(this,0);auto* View=GetWorld()?GetWorld()->GetGameViewport():nullptr;return PC&&View&&!View->IgnoreInput()&&!PC->IsMoveInputIgnored()&&!PC->IsLookInputIgnored();}
