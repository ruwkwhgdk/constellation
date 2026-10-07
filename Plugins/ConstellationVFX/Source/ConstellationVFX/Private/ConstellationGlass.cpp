#include "ConstellationGlass.h"
#include "ConstellationFXLibrary.h"
#include "ConstellationFXActor.h"
#include "SceneDirectorPlayer.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Materials/MaterialInterface.h"
AConstellationGlass::AConstellationGlass(){
 Pane=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("GlassPane"));RootComponent=Pane;
 static ConstructorHelpers::FObjectFinder<UStaticMesh> Mesh(TEXT("/Engine/BasicShapes/Cube.Cube"));Pane->SetStaticMesh(Mesh.Object);
 Pane->SetCollisionProfileName(TEXT("BlockAll"));Pane->SetCastShadow(false);
}
void AConstellationGlass::OnConstruction(const FTransform& T){Super::OnConstruction(T);Pane->SetRelativeScale3D(FVector(.025,FMath::Max(1.,Size.X)/100,FMath::Max(1.,Size.Y)/100));if(auto* M=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Constellation/VFX/Materials/M_GlassPane.M_GlassPane")))Pane->SetMaterial(0,M);Pane->SetVisibility(!bBroken);SetActorEnableCollision(!bBroken);}
bool AConstellationGlass::BreakGlass(FVector Point,FVector Direction){if(bBroken||Point.ContainsNaN()||Direction.ContainsNaN())return false;bBroken=true;Pane->SetVisibility(false);SetActorEnableCollision(false);auto* FX=UConstellationFXLibrary::SpawnEffect(this,EConstellationFXKind::GlassBreak,Point,Direction,Tint,FMath::Clamp(float(Size.Size()/210),.5f,2.5f));if(FX)FX->SetOwner(this);return true;}
void AConstellationGlass::ResetGlass(){UConstellationFXLibrary::StopEffectsForOwner(this);bBroken=false;Pane->SetVisibility(true);SetActorEnableCollision(true);}
float AConstellationGlass::TakeDamage(float Damage,const FDamageEvent& E,AController* I,AActor* C){if(!FMath::IsFinite(Damage)||Damage<=0||bBroken)return 0;BreakGlass(GetActorLocation(),C?(GetActorLocation()-C->GetActorLocation()).GetSafeNormal():GetActorForwardVector());return Damage;}

bool AConstellationGlass::BreakForScene(ASceneDirectorPlayer* Player){return SetBrokenForScene(Player,true);}
bool AConstellationGlass::SetBrokenForScene(ASceneDirectorPlayer* Player,bool Broken){
 if(!IsValid(Player)||(SceneOwner.IsValid()&&SceneOwner.Get()!=Player))return false;
 if(!SceneOwner.IsValid()){bBeforeSceneBroken=bBroken;SceneOwner=Player;Player->OnDirectorStopped.AddUniqueDynamic(this,&AConstellationGlass::OnSceneStopped);}
 if(Broken){if(!bBroken)BreakGlass(GetActorLocation(),GetActorForwardVector());}else ResetGlass();return true;
}
void AConstellationGlass::OnSceneStopped(bool Completed){
 if(SceneOwner.IsValid())SceneOwner->OnDirectorStopped.RemoveDynamic(this,&AConstellationGlass::OnSceneStopped);SceneOwner.Reset();
 if(!Completed){UConstellationFXLibrary::StopEffectsForOwner(this);bBroken=bBeforeSceneBroken;Pane->SetVisibility(!bBroken);SetActorEnableCollision(!bBroken);}
}
void AConstellationGlass::EndPlay(const EEndPlayReason::Type Reason){if(SceneOwner.IsValid())SceneOwner->OnDirectorStopped.RemoveDynamic(this,&AConstellationGlass::OnSceneStopped);UConstellationFXLibrary::StopEffectsForOwner(this);Super::EndPlay(Reason);}
