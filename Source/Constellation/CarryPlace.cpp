#include "CarryComponent.h"
#include "HoldableComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "GameFramework/Character.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"

FTransform UCarryComponent::GetFittedPlaceTransform() const
{
    const FHoldableItemRow* Row=GetFittedProfile();
    float Progress=0.f;
    if(Row&&Row->FittedPlaceProgress.Num()>1)
    {
        const float Phase=FMath::Clamp((GetWorld()->GetTimeSeconds()-PlaceStartTime)/FMath::Clamp(PlaceActionSeconds,.5f,.9f),0.f,1.f);
        const float Index=Phase*(Row->FittedPlaceProgress.Num()-1);
        const int32 Lower=FMath::Min(FMath::FloorToInt(Index),Row->FittedPlaceProgress.Num()-2);
        Progress=FMath::Clamp(FMath::Lerp(Row->FittedPlaceProgress[Lower],Row->FittedPlaceProgress[Lower+1],Index-Lower),0.f,1.f);
    }
    FTransform Result; Result.Blend(PlaceStartTransform,PlaceTransform,Progress); return Result;
}

float UCarryComponent::GetFittedPlaceAlpha() const
{
    return bFittedPlacing&&State==ECarryState::Placing&&IsValid(HeldItem)&&!bContactOccurred?1.f:0.f;
}

void UCarryComponent::UpdateFittedPlace()
{
    if(!IsValid(HeldItem)) return;
    const FTransform Next=GetFittedPlaceTransform();
    FHitResult Hit;
    if(!IsSpaceFree(Next)||!IsPathFree(HeldItem->GetHoldMesh()->GetComponentLocation(),Next.GetLocation(),Next.GetRotation(),Hit))
    {
        ShowFailure(GetCarryMessage(TEXT("PlaceBlocked"))); FinishAction(); return;
    }
    GetHeldActor()->SetActorTransform(Next);
    if(bPlaceReleasePending)
    {
        // Notify is evaluated during the mesh tick; release only after its matching prop pose.
        if(!Next.GetLocation().Equals(PlaceTransform.GetLocation(),.2f)) return;
        bPlaceReleasePending=false; bContactOccurred=true;
        ReleaseHeld(Next,FVector::ZeroVector,0.f);
    }
}
