#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "CombatActionDefinition.generated.h"
class UAnimMontage;

UCLASS(BlueprintType)
class COMBATRUNTIME_API UCombatActionDefinition : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Action") FText DisplayName;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Action") TObjectPtr<UAnimMontage> Montage;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Action", meta=(ClampMin="0")) float Damage = 20.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Action", meta=(ClampMin="0")) float StaminaCost = 10.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Action", meta=(ClampMin="0")) float Cooldown = .4f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Action", meta=(ClampMin=".1")) float PlayRate = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Action", meta=(ClampMin="0", ClampMax="100")) float UltimateCost=0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Action", meta=(ClampMin="0", ClampMax="100")) float UltimateGain=10.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Hit") bool bRadialHit=false;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Movement", meta=(ClampMin="0", Units="cm")) float DashDistance=0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Movement", meta=(ClampMin="0.01", Units="s")) float DashDuration=.25f;
    // Core prototype: visible forward sphere sweep, not final weapon-socket tracing.
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Hit", meta=(ClampMin="1", Units="cm")) float Reach = 140.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Hit", meta=(ClampMin="1", Units="cm")) float Radius = 30.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Follow Up") TObjectPtr<UCombatActionDefinition> NextAction;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Follow Up", meta=(ClampMin="0", Units="s")) float InputWindowStart = .5f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Follow Up", meta=(ClampMin="0", Units="s")) float InputWindowEnd = .65f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Dodge Cancel") bool bAllowDodgeCancel = false;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Dodge Cancel", meta=(ClampMin="0", Units="s")) float DodgeCancelStart = .5f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Dodge Cancel", meta=(ClampMin="0", Units="s")) float DodgeCancelEnd = .7f;
    bool Validate(FString& Reason) const;
#if WITH_EDITOR
    virtual EDataValidationResult IsDataValid(FDataValidationContext& Context) const override;
#endif
};
