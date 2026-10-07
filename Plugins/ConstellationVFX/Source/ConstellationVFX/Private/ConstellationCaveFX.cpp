#include "ConstellationCaveFX.h"
#include "ConstellationFXLibrary.h"
#include "ConstellationFXActor.h"
#include "Camera/PlayerCameraManager.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "SceneDirectorPlayer.h"
AConstellationCaveFX::AConstellationCaveFX(){PrimaryActorTick.bCanEverTick=true;PrimaryActorTick.TickInterval=.08f;RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Root"));}
void AConstellationCaveFX::SetEffectsEnabled(bool Enabled){bEnabled=Enabled;if(!Enabled){UConstellationFXLibrary::StopEffectsForOwner(this);Drops.Reset();}}
void AConstellationCaveFX::EndPlay(const EEndPlayReason::Type Reason){if(SceneOwner.IsValid())SceneOwner->OnDirectorStopped.RemoveDynamic(this,&AConstellationCaveFX::OnSceneStopped);UConstellationFXLibrary::StopEffectsForOwner(this);Super::EndPlay(Reason);}
void AConstellationCaveFX::Tick(float Dt){Super::Tick(Dt);auto* Cam=UGameplayStatics::GetPlayerCameraManager(this,0);if(!bEnabled||!Cam||FVector::DistSquared(Cam->GetCameraLocation(),GetActorLocation())>FMath::Square(ActiveDistance))return;
 auto Spawn=[&](EConstellationFXKind K,FVector P,FLinearColor C,float S){if(auto* F=UConstellationFXLibrary::SpawnEffect(this,K,P,FVector::UpVector,C,S))F->SetOwner(this);};
 DustClock-=Dt;MistClock-=Dt;DropClock-=Dt;SporeClock-=Dt;
 if(DustClock<=0){DustClock=2.7;Spawn(EConstellationFXKind::CaveDust,GetActorLocation()+FVector(0,0,70),FLinearColor(.5,.58,.65,.4),Radius/160);}
 if(bMist&&MistClock<=0){MistClock=4.3;Spawn(EConstellationFXKind::CaveMist,GetActorLocation()+FVector(0,0,12),MistColor,Radius/250);}
 if(bSpores&&SporeClock<=0){SporeClock=3.5;Spawn(EConstellationFXKind::CaveSpore,GetActorLocation()+FVector(0,0,25),SporeColor,1);}
 for(int I=Drops.Num()-1;I>=0;--I){Drops[I].Time-=Dt;if(Drops[I].Time<=0){Spawn(EConstellationFXKind::WaterRipple,Drops[I].Point,FLinearColor(.4,.65,.7,.5),1);Drops.RemoveAtSwap(I);}}
 if(bDrips&&DropClock<=0){DropClock=FMath::FRandRange(1.4,2.5);FVector Start=GetActorLocation()+FVector(FMath::FRandRange(-Radius*.5,Radius*.5),FMath::FRandRange(-Radius*.5,Radius*.5),CeilingHeight);FHitResult Hit;FCollisionQueryParams Q(SCENE_QUERY_STAT(CaveDrip),false,this);if(GetWorld()->LineTraceSingleByChannel(Hit,Start,Start-FVector(0,0,CeilingHeight+150),ECC_Visibility,Q)){float H=FVector::Dist(Start,Hit.ImpactPoint);Spawn(EConstellationFXKind::WaterDrop,Start,FLinearColor(.3,.6,.7,1),1);Drops.Add({(-160+FMath::Sqrt(25600+600*H))/300,Hit.ImpactPoint+FVector(0,0,2)});}}
}

bool AConstellationCaveFX::ApplySceneEnabled(ASceneDirectorPlayer* Player,bool Enabled){if(!IsValid(Player)||(SceneOwner.IsValid()&&SceneOwner.Get()!=Player))return false;if(!SceneOwner.IsValid()){bBeforeScene=bEnabled;SceneOwner=Player;Player->OnDirectorStopped.AddUniqueDynamic(this,&AConstellationCaveFX::OnSceneStopped);}SetEffectsEnabled(Enabled);return true;}
void AConstellationCaveFX::OnSceneStopped(bool){if(SceneOwner.IsValid())SceneOwner->OnDirectorStopped.RemoveDynamic(this,&AConstellationCaveFX::OnSceneStopped);SceneOwner.Reset();SetEffectsEnabled(false);SetEffectsEnabled(bBeforeScene);}
