#include "HoldableComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Actor.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "PhysicsEngine/BodySetup.h"

UHoldableComponent::UHoldableComponent() { PrimaryComponentTick.bCanEverTick=true; PrimaryComponentTick.bStartWithTickEnabled=false; }
void UHoldableComponent::BeginPlay() { Super::BeginPlay(); ApplySettings(); }
bool UHoldableComponent::ApplySettings()
{
    if(Carrier.IsValid() || bFlight || bPendingRestore) return false;
    if(!ItemRow.DataTable) return true;
    const FHoldableItemRow* Row=ItemRow.GetRow<FHoldableItemRow>(TEXT("Holdable item"));
    if(!Row) return false;
    CarryOffset=Row->CarryOffset;
    LeftHandGrip=Row->LeftHandGrip;
    RightHandGrip=Row->RightHandGrip;
    bCanThrow=Row->bCanThrow;
    PlaceRotation=Row->PlaceRotation;
    return true;
}
void UHoldableComponent::BeginBallisticFlight()
{
    UStaticMeshComponent* Mesh=GetHoldMesh(); if(!Mesh) return;
    EndBallisticFlight();
    FlightLinearDamping=Mesh->GetLinearDamping(); FlightAngularDamping=Mesh->GetAngularDamping();
    bSavedHitNotifications=Mesh->BodyInstance.bNotifyRigidBodyCollision;
    bHasThrowContact=false; bFlight=true;
    Mesh->SetLinearDamping(0); Mesh->SetAngularDamping(0);
    Mesh->SetNotifyRigidBodyCollision(true); Mesh->OnComponentHit.AddUniqueDynamic(this,&UHoldableComponent::OnFlightHit);
}
void UHoldableComponent::OnFlightHit(UPrimitiveComponent*,AActor*,UPrimitiveComponent*,FVector,const FHitResult&)
{
    UStaticMeshComponent* Mesh=GetHoldMesh(); if(!bFlight||!Mesh) return;
    bHasThrowContact=true; ThrowContactLocation=Mesh->GetComponentLocation(); EndBallisticFlight();
}
void UHoldableComponent::EndBallisticFlight()
{
    UStaticMeshComponent* Mesh=GetHoldMesh(); if(!bFlight||!Mesh) return; bFlight=false;
    Mesh->SetLinearDamping(FlightLinearDamping); Mesh->SetAngularDamping(FlightAngularDamping);
    Mesh->SetNotifyRigidBodyCollision(bSavedHitNotifications); Mesh->OnComponentHit.RemoveDynamic(this,&UHoldableComponent::OnFlightHit);
}
void UHoldableComponent::RestoreWhenClear(ECollisionEnabled::Type Collision,bool bGravity,bool bPhysics)
{
    RestoreCollision=Collision; bRestoreGravity=bGravity; bRestorePhysics=bPhysics; bPendingRestore=true;
    SetComponentTickEnabled(true); TickComponent(0,LEVELTICK_All,&PrimaryComponentTick);
}
void UHoldableComponent::TickComponent(float Dt,ELevelTick Type,FActorComponentTickFunction* Fn)
{
    Super::TickComponent(Dt,Type,Fn); UStaticMeshComponent* Mesh=GetHoldMesh();
    if(!bPendingRestore||!Mesh||!Mesh->GetStaticMesh()) return;
    const FBox Box=Mesh->GetStaticMesh()->GetBoundingBox(); FCollisionQueryParams Params(SCENE_QUERY_STAT(CarryDropRecovery),false,GetOwner());
    if(GetWorld()->OverlapBlockingTestByChannel(Mesh->GetComponentTransform().TransformPosition(Box.GetCenter()),Mesh->GetComponentQuat(),Mesh->GetCollisionObjectType(),
        FCollisionShape::MakeBox(Box.GetExtent()*Mesh->GetComponentScale().GetAbs()),Params,FCollisionResponseParams(Mesh->GetCollisionResponseToChannels()))) return;
    Mesh->SetCollisionEnabled(RestoreCollision); Mesh->SetEnableGravity(bRestoreGravity); Mesh->SetSimulatePhysics(bRestorePhysics);
    bPendingRestore=false; SetComponentTickEnabled(false);
}

UStaticMeshComponent* UHoldableComponent::GetHoldMesh() const
{
    return HoldMesh ? HoldMesh.Get() : (GetOwner() ? Cast<UStaticMeshComponent>(GetOwner()->GetRootComponent()) : nullptr);
}
float UHoldableComponent::GetWeightKg() const
{
    UStaticMeshComponent* Mesh=GetHoldMesh();
    if(!Mesh) return 0.f;
    // Pickup removes the collision body. CalculateMass still honors the body's
    // authored override (or shape/material-derived mass) while it is absent.
    return Mesh->GetCollisionEnabled()!=ECollisionEnabled::NoCollision && Mesh->BodyInstance.IsValidBodyInstance() ? Mesh->GetMass() : Mesh->CalculateMass();
}
bool UHoldableComponent::IsUsable() const
{
    UStaticMeshComponent* Mesh = GetHoldMesh();
    return !bPendingRestore && IsValid(GetOwner()) && Mesh && Mesh->GetStaticMesh() && Mesh == GetOwner()->GetRootComponent()
        && Mesh->Mobility == EComponentMobility::Movable && Mesh->GetCollisionEnabled()==ECollisionEnabled::QueryAndPhysics
        && Mesh->GetBodySetup() && Mesh->GetBodySetup()->CollisionTraceFlag!=CTF_UseComplexAsSimple && Mesh->GetBodySetup()->AggGeom.GetElementCount()>0
        && FMath::IsFinite(GetWeightKg()) && GetWeightKg() > 0;
}
