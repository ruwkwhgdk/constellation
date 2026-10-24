#include "LittleGirlBasketActor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"

namespace
{
 void ConfigureProp(UStaticMeshComponent* Mesh)
 {
  Mesh->SetMobility(EComponentMobility::Movable);
  Mesh->SetCollisionObjectType(ECC_PhysicsBody);
  Mesh->SetCollisionResponseToAllChannels(ECR_Ignore);
  Mesh->SetCollisionResponseToChannel(ECC_WorldStatic,ECR_Block);
  Mesh->SetCollisionResponseToChannel(ECC_WorldDynamic,ECR_Block);
  // Contents start inside the basket: avoid self-collision impulses at release.
  Mesh->SetCollisionResponseToChannel(ECC_PhysicsBody,ECR_Ignore);
  Mesh->SetCollisionResponseToChannel(ECC_Pawn,ECR_Ignore);
  Mesh->SetLinearDamping(.5f);Mesh->SetAngularDamping(1.5f);
 }
}
ALittleGirlBasketActor::ALittleGirlBasketActor()
{
 PrimaryActorTick.bCanEverTick=false;
 BasketMesh=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BasketMesh"));
 SetRootComponent(BasketMesh);ConfigureProp(BasketMesh);
 BasketMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}
bool ALittleGirlBasketActor::AttachToCarrier(USceneComponent* Carrier,FName HandBone)
{
 if(!IsValid(Carrier)||!BasketMesh->GetStaticMesh()||(!HandBone.IsNone()&&!Carrier->DoesSocketExist(HandBone)))return false;
 BasketMesh->SetSimulatePhysics(false);BasketMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 SetOwner(nullptr);SetLifeSpan(0.f);SetActorHiddenInGame(false);
 AttachToComponent(Carrier,FAttachmentTransformRules::SnapToTargetNotIncludingScale,HandBone);
 SetActorRelativeTransform(GripOffset);SetActorScale3D(FVector::OneVector);bDropped=false;
 for(int32 I=0;I<MushroomTransforms.Num();++I)
 {
  if(MushroomMeshes.IsEmpty()||!MushroomMeshes[I%MushroomMeshes.Num()])continue;
  if(!Mushrooms.IsValidIndex(I))Mushrooms.SetNum(I+1);
  if(!IsValid(Mushrooms[I]))
  {
   FActorSpawnParameters P;P.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
   Mushrooms[I]=GetWorld()->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(),GetActorTransform(),P);
  }
  auto* A=Mushrooms[I].Get();if(!A)continue;
  auto* M=A->GetStaticMeshComponent();ConfigureProp(M);M->SetSimulatePhysics(false);M->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  M->SetStaticMesh(MushroomMeshes[I%MushroomMeshes.Num()]);A->SetOwner(nullptr);A->SetLifeSpan(0.f);A->SetActorHiddenInGame(false);
  A->AttachToActor(this,FAttachmentTransformRules::SnapToTargetNotIncludingScale);A->SetActorRelativeTransform(MushroomTransforms[I]);
 }
 return true;
}
void ALittleGirlBasketActor::Drop(FVector ReleaseVelocity)
{
 if(bDropped)return;
 bDropped=true;DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);SetOwner(nullptr);
 BasketMesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);BasketMesh->SetSimulatePhysics(true);
 BasketMesh->SetPhysicsLinearVelocity(ReleaseVelocity);BasketMesh->SetPhysicsAngularVelocityInDegrees(FVector(0,30,12));
 for(int32 I=0;I<Mushrooms.Num();++I)
 {
  auto* A=Mushrooms[I].Get();if(!IsValid(A))continue;
  A->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);A->SetOwner(nullptr);
  auto* M=A->GetStaticMeshComponent();M->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);M->SetSimulatePhysics(true);
  const float Angle=I*2.399963f;
  M->SetPhysicsLinearVelocity(ReleaseVelocity+FVector(FMath::Cos(Angle)*16,FMath::Sin(Angle)*16,8));
  M->SetPhysicsAngularVelocityInDegrees(FVector(30+I*3,20,-15));
 }
}


