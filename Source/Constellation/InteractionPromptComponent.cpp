#include "InteractionPromptComponent.h"
#include "InteractionPromptWidget.h"
#include "Internationalization/StringTable.h"
#include "Internationalization/StringTableCore.h"
#include "CarryComponent.h"
#include "HoldableComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/World.h"
#include "Engine/LocalPlayer.h"
#include "Engine/GameViewportClient.h"
#include "EnhancedInputSubsystems.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "InputAction.h"
#include "UObject/UnrealType.h"

namespace
{
    bool ReadBool(const UObject* Object, FName Name, bool Default=false)
    {
        const FBoolProperty* Property=Object ? FindFProperty<FBoolProperty>(Object->GetClass(),Name) : nullptr;
        return Property ? Property->GetPropertyValue_InContainer(Object) : Default;
    }
}

UInteractionPromptComponent::UInteractionPromptComponent()
{
    PrimaryComponentTick.bCanEverTick=true;
    // A nonzero interval cannot advance while game time is paused.
    PrimaryComponentTick.bTickEvenWhenPaused=true;
}
EInteractionAction UInteractionPromptComponent::GetTargetAction(AActor* Target, UPrimitiveComponent* HitComponent) const
{
    if(!IsValid(Target) || Target->IsHidden()) return EInteractionAction::None;
    for(const FInteractionPromptRule& Rule:Rules)
    {
        if(!Rule.ActorClass || !Target->IsA(Rule.ActorClass)) continue;
        if(!Rule.CompletedProperty.IsNone() && ReadBool(Target,Rule.CompletedProperty)) return EInteractionAction::None;
        if(!Rule.EnabledProperty.IsNone() && !ReadBool(Target,Rule.EnabledProperty)) return EInteractionAction::None;
        if(Rule.bRespectInteractOnce && ReadBool(Target,TEXT("InteractOnce")) && ReadBool(Target,TEXT("bIsInteracted"))) return EInteractionAction::None;
        if(!Rule.RequiredOverlapComponent.IsNone())
        {
            const FObjectPropertyBase* Property=FindFProperty<FObjectPropertyBase>(Target->GetClass(),Rule.RequiredOverlapComponent);
            const UPrimitiveComponent* Region=Property ? Cast<UPrimitiveComponent>(Property->GetObjectPropertyValue_InContainer(Target)) : nullptr;
            if(!Region || !Region->IsOverlappingActor(GetOwner())) return EInteractionAction::None;
        }
        const bool bAlternate=(!Rule.ToggleProperty.IsNone() && ReadBool(Target,Rule.ToggleProperty))
            || (!Rule.AlternateComponentTag.IsNone() && IsValid(HitComponent) && HitComponent->ComponentHasTag(Rule.AlternateComponentTag));
        return bAlternate ? Rule.AlternateAction : Rule.Action;
    }
    return EInteractionAction::None;
}
EInteractionAction UInteractionPromptComponent::QueryAction(AActor*& Target) const
{
    Target=nullptr;
    const ACharacter* Character=Cast<ACharacter>(GetOwner());
    if(!Character || !GetWorld() || GetWorld()->IsPaused()) return EInteractionAction::None;
    const APlayerController* PC=Cast<APlayerController>(Character->GetController());
    if(PC && PC->IsMoveInputIgnored()) return EInteractionAction::None;
    // A visible cursor is also valid in gameplay (the school controller uses it).
    // UIOnly input mode suppresses game input through the viewport instead.
    const ULocalPlayer* LocalPlayer=PC ? PC->GetLocalPlayer() : nullptr;
    if(LocalPlayer && LocalPlayer->ViewportClient && LocalPlayer->ViewportClient->IgnoreInput()) return EInteractionAction::None;
    const UCarryComponent* Carry=Character->FindComponentByClass<UCarryComponent>();
    if(Carry && Carry->BlocksOtherActions())
    {
        EInteractionAction Action=EInteractionAction::None;
        if(Carry->State==ECarryState::Aiming) Action=EInteractionAction::CancelAim;
        else if(Carry->CanPlace()) Action=EInteractionAction::PutDown;
        if(Action!=EInteractionAction::None) Target=Carry->GetHeldActor();
        return Action;
    }
    for(FName Name:{FName("IsAttacking"),FName("IsPushing"),FName("IsClimbing"),FName("bIsJumping")})
        if(ReadBool(Character,Name)) return EInteractionAction::None;
    if(Carry)
    {
        if(UHoldableComponent* Item=Carry->FindInteractionItem())
        {
            // Input consumes this hit even if lifting fails: never advertise a different object behind it.
            if(!Carry->CanPickUp(Item)) return EInteractionAction::None;
            Target=Item->GetOwner(); return EInteractionAction::PickUp;
        }
    }
    // Same socket, distance, radius and channel as Ac_Interact's Do Interact graph.
    const FVector Start=Character->GetMesh()->GetSocketLocation(TEXT("Hips"));
    FHitResult Hit;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(InteractionPrompt),false,GetOwner());
    if(GetWorld()->SweepSingleByChannel(Hit,Start,Start+Character->GetActorForwardVector()*120.f,
        FQuat::Identity,ECC_GameTraceChannel1,FCollisionShape::MakeSphere(45.f),Params))
    {
        const EInteractionAction Action=GetTargetAction(Hit.GetActor(),Hit.GetComponent());
        if(Action!=EInteractionAction::None) Target=Hit.GetActor();
        return Action;
    }
    return EInteractionAction::None;
}
FText UInteractionPromptComponent::GetInteractionKeyText() const
{
    const APawn* Pawn=Cast<APawn>(GetOwner());
    const APlayerController* PC=Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
    if(PC && PC->GetLocalPlayer() && InteractInputAction)
    {
        if(const auto* Input=PC->GetLocalPlayer()->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
        {
            for(const FKey& Key:Input->QueryKeysMappedToAction(InteractInputAction))
                if(Key.IsValid() && !Key.IsGamepadKey()) return Key.GetDisplayName();
            return FText::GetEmpty(); // Explicitly unbound actions must not advertise a stale F key.
        }
    }
    return FText::FromString(TEXT("F"));
}
FText UInteractionPromptComponent::GetActionText(EInteractionAction Action) const
{
    const UEnum* Actions=StaticEnum<EInteractionAction>();
    if(!ActionStrings || Action==EInteractionAction::None || !Actions->IsValidEnumValue(static_cast<int64>(Action)))
        return FText::GetEmpty();
    const FString Key=Actions->GetNameStringByValue(static_cast<int64>(Action));
    if(!ActionStrings->GetStringTable()->FindEntry(Key).IsValid()) return FText::GetEmpty();
    return FText::FromStringTable(ActionStrings->GetStringTableId(),Key);
}
void UInteractionPromptComponent::TickComponent(float D,ELevelTick T,FActorComponentTickFunction* F)
{
    Super::TickComponent(D,T,F);
    const APawn* Pawn=Cast<APawn>(GetOwner());
    APlayerController* PC=Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
    if(!PC || !PC->IsLocalController())
    {
        if(Prompt) Prompt->SetVisibility(ESlateVisibility::Collapsed);
        CurrentAction=EInteractionAction::None; CurrentTarget=nullptr; return;
    }
    AActor* Target=nullptr;
    CurrentAction=QueryAction(Target); CurrentTarget=Target;
    if(!Prompt && CurrentAction!=EInteractionAction::None)
    {
        UInteractionPromptWidget* Widget=CreateWidget<UInteractionPromptWidget>(PC);
        Prompt=Widget;
        if(Widget) { Widget->SetBackgroundTexture(BackgroundTexture); Widget->SetKeyBackgroundTexture(KeyBackgroundTexture); Widget->AddToPlayerScreen(20); }
    }
    if(auto* Widget=Cast<UInteractionPromptWidget>(Prompt))
        Widget->SetPrompt(GetInteractionKeyText(),GetActionText(CurrentAction));
}
void UInteractionPromptComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    if(Prompt) Prompt->RemoveFromParent();
    Prompt=nullptr; CurrentTarget=nullptr; CurrentAction=EInteractionAction::None;
    Super::EndPlay(Reason);
}
