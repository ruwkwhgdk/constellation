#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "InteractionPromptComponent.generated.h"

class UStringTable;
class UUserWidget;
class UInputAction;
class UTexture2D;
class UPrimitiveComponent;

UENUM(BlueprintType)
enum class EInteractionAction : uint8
{
    None, PickUp, PutDown, CancelAim, Open, Close, Read, Climb,
    Activate, Deactivate, Collect, Play, Restore, Reset, Inspect, Interact, Descend
};

// Ordered most-specific class first. Content owns the action and state names.
USTRUCT(BlueprintType)
struct FInteractionPromptRule
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TSubclassOf<AActor> ActorClass;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) EInteractionAction Action = EInteractionAction::Interact;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) EInteractionAction AlternateAction = EInteractionAction::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName ToggleProperty;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName AlternateComponentTag;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName CompletedProperty;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName EnabledProperty;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName RequiredOverlapComponent;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bRespectInteractOnce = false;
};

UCLASS(ClassGroup=(Interaction), meta=(BlueprintSpawnableComponent))
class CONSTELLATION_API UInteractionPromptComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UInteractionPromptComponent();
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Interaction") TObjectPtr<UStringTable> ActionStrings;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Interaction") TArray<FInteractionPromptRule> Rules;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Interaction") TObjectPtr<UInputAction> InteractInputAction;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Interaction") TObjectPtr<UTexture2D> BackgroundTexture;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Interaction") TObjectPtr<UTexture2D> KeyBackgroundTexture;
    UPROPERTY(BlueprintReadOnly, Transient, Category="Interaction") EInteractionAction CurrentAction = EInteractionAction::None;
    UPROPERTY(BlueprintReadOnly, Transient, Category="Interaction") TObjectPtr<AActor> CurrentTarget;
    UFUNCTION(BlueprintPure, Category="Interaction") EInteractionAction QueryAction(AActor*& Target) const;
    UFUNCTION(BlueprintPure, Category="Interaction") EInteractionAction GetTargetAction(AActor* Target, UPrimitiveComponent* HitComponent = nullptr) const;
    UFUNCTION(BlueprintPure, Category="Interaction") FText GetInteractionKeyText() const;
    UFUNCTION(BlueprintPure, Category="Interaction") FText GetActionText(EInteractionAction Action) const;
protected:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* Function) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    UPROPERTY(Transient) TObjectPtr<UUserWidget> Prompt;
};
