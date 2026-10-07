#pragma once
#include "CoreMinimal.h"
#include "AttributeSet.h"
#include "AbilitySystemComponent.h"
#include "CombatAttributes.generated.h"

#define COMBAT_ATTRIBUTE(Name) \
    GAMEPLAYATTRIBUTE_PROPERTY_GETTER(UCombatAttributes, Name) \
    GAMEPLAYATTRIBUTE_VALUE_GETTER(Name) \
    GAMEPLAYATTRIBUTE_VALUE_SETTER(Name) \
    GAMEPLAYATTRIBUTE_VALUE_INITTER(Name)

UCLASS()
class COMBATRUNTIME_API UCombatAttributes : public UAttributeSet
{
    GENERATED_BODY()
public:
    UCombatAttributes();
    void InitializeResources(float HealthLimit, float StaminaLimit);
    float GetMaxHealth() const { return MaxHealth; }
    float GetMaxStamina() const { return MaxStamina; }
    UPROPERTY(BlueprintReadOnly, Category="Combat") FGameplayAttributeData Health;
    UPROPERTY(BlueprintReadOnly, Category="Combat") FGameplayAttributeData Stamina;
    UPROPERTY(BlueprintReadOnly, Category="Combat") FGameplayAttributeData UltimateCharge;
    COMBAT_ATTRIBUTE(UltimateCharge)
    COMBAT_ATTRIBUTE(Health)
    COMBAT_ATTRIBUTE(Stamina)
    virtual void PreAttributeBaseChange(const FGameplayAttribute& Attribute, float& NewValue) const override;
    virtual void PreAttributeChange(const FGameplayAttribute& Attribute, float& NewValue) override;
    virtual void PostGameplayEffectExecute(const FGameplayEffectModCallbackData& Data) override;
private:
    float MaxHealth = 100.f;
    float MaxStamina = 100.f;
};
#undef COMBAT_ATTRIBUTE
