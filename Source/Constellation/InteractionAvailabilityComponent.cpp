#include "InteractionAvailabilityComponent.h"
#include "GameFramework/Actor.h"
#include "UObject/UnrealType.h"
#include "Engine/World.h"
#include "SceneEventSubsystem.h"

namespace
{
    bool InteractionBool(const UObject* Object,FName Name)
    {
        const auto* Property=Object ? FindFProperty<FBoolProperty>(Object->GetClass(),Name) : nullptr;
        return Property && Property->GetPropertyValue_InContainer(Object);
    }
}
UInteractionAvailabilityComponent::UInteractionAvailabilityComponent()
{
    PrimaryComponentTick.bCanEverTick=true;
    PrimaryComponentTick.TickInterval=.1f;
    CompletedProperty=TEXT("IsOpened");
}
void UInteractionAvailabilityComponent::BeginPlay()
{
    Super::BeginPlay();
    RefreshAvailability();
}
void UInteractionAvailabilityComponent::TickComponent(float D,ELevelTick T,FActorComponentTickFunction* F)
{
    Super::TickComponent(D,T,F);
    RefreshAvailability();
}
bool UInteractionAvailabilityComponent::RefreshAvailability()
{
    AActor* Owner=GetOwner();
    if(!IsValid(Owner)) return true;
    if(bInteractionUnavailable) return true;
    const bool bLegacyCompleted=(!CompletedProperty.IsNone() && InteractionBool(Owner,CompletedProperty))
        || (bRespectInteractOnce && InteractionBool(Owner,TEXT("InteractOnce")) && InteractionBool(Owner,TEXT("bIsInteracted")));
    const auto* Events=GetWorld() ? GetWorld()->GetSubsystem<USceneEventSubsystem>() : nullptr;
    bInteractionUnavailable=bLegacyCompleted || (Events && Events->HasCompletedInteraction(Owner));
    return bInteractionUnavailable;
}
bool UInteractionAvailabilityComponent::CanActorInteract(UObject* Target)
{
    AActor* Actor=Cast<AActor>(Target);
    if(!IsValid(Actor) || Actor->IsHidden()) return false;
    if(auto* State=Actor->FindComponentByClass<UInteractionAvailabilityComponent>())
        return !State->RefreshAvailability();
    return true;
}
