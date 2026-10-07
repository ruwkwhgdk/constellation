#pragma once
#include "CoreMinimal.h"
#include "Abilities/GameplayAbility.h"
#include "CombatAbilitySystem.h"
#include "CombatActionAbility.generated.h"
UCLASS()
class COMBATRUNTIME_API UCombatActionAbility : public UGameplayAbility
{
    GENERATED_BODY()
public:
    UCombatActionAbility();
    virtual bool CanActivateAbility(FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* Info,
        const FGameplayTagContainer* SourceTags=nullptr, const FGameplayTagContainer* TargetTags=nullptr,
        FGameplayTagContainer* RelevantTags=nullptr) const override;
    virtual void ActivateAbility(FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* Info,
        FGameplayAbilityActivationInfo Activation, const FGameplayEventData* Event) override;
    virtual void EndAbility(FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* Info,
        FGameplayAbilityActivationInfo Activation, bool Replicate, bool Cancelled) override;
private:
    UFUNCTION() void MontageCompleted();
    UFUNCTION() void MontageInterrupted();
    bool bFinishing = false;
    ECombatActionResult Result = ECombatActionResult::Failed;
};
