#include "CarryAnimNotify.h"
#include "CarryComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Actor.h"
void UCarryAnimNotify::Notify(USkeletalMeshComponent* Mesh, UAnimSequenceBase*, const FAnimNotifyEventReference&)
{
    if (Mesh && Mesh->GetOwner()) if (UCarryComponent* Carry=Mesh->GetOwner()->FindComponentByClass<UCarryComponent>())
    {
        if(Contact==ECarryContact::Pickup) Carry->OnPickupContact();
        else if(Contact==ECarryContact::Place) Carry->OnPlaceRelease();
        else Carry->OnThrowRelease();
    }
}
