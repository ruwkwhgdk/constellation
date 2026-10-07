#include "PhysicsPropComponent.h"
#include "Components/PrimitiveComponent.h"
#include "GameFramework/Actor.h"

void UPhysicsPropComponent::BeginPlay()
{
    Super::BeginPlay();
    if(PhysicsRow.DataTable && !ApplyInitialSettings())
        UE_LOG(LogTemp, Warning, TEXT("Physics settings were not applied to %s"), *GetNameSafe(GetOwner()));
}
bool UPhysicsPropComponent::ApplyInitialSettings()
{
    if(bApplied || !GetOwner() || !PhysicsRow.DataTable) return false;
    const FPhysicsPropRow* Row=PhysicsRow.GetRow<FPhysicsPropRow>(TEXT("Physics prop"));
    if(!Row || !FMath::IsFinite(Row->MassKg) || Row->MassKg<=0
        || !FMath::IsFinite(Row->LinearDamping) || Row->LinearDamping<0
        || !FMath::IsFinite(Row->AngularDamping) || Row->AngularDamping<0) return false;
    UPrimitiveComponent* Mesh=Cast<UPrimitiveComponent>(GetOwner()->GetRootComponent());
    if(!MeshComponentName.IsNone())
    {
        Mesh=nullptr;
        TInlineComponentArray<UPrimitiveComponent*> Components(GetOwner());
        for(UPrimitiveComponent* Component:Components)
            if(Component->GetFName()==MeshComponentName) { Mesh=Component; break; }
    }
    if(!Mesh || !Mesh->IsRegistered() || Mesh->Mobility!=EComponentMobility::Movable) return false;
    Mesh->SetPhysMaterialOverride(Row->PhysicalMaterial);
    Mesh->SetMassOverrideInKg(NAME_None,Row->MassKg,true);
    Mesh->SetLinearDamping(Row->LinearDamping);
    Mesh->SetAngularDamping(Row->AngularDamping);
    Mesh->SetEnableGravity(Row->bEnableGravity);
    Mesh->SetSimulatePhysics(Row->bSimulatePhysics);
    bApplied=true;
    return true;
}
