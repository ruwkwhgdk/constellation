#include "CombatAttributes.h"
#include "GameplayEffectExtension.h"
UCombatAttributes::UCombatAttributes() { InitHealth(MaxHealth); InitStamina(MaxStamina); InitUltimateCharge(0.f); }
void UCombatAttributes::InitializeResources(float HealthLimit, float StaminaLimit)
{
    MaxHealth = FMath::IsFinite(HealthLimit) && HealthLimit > 0.f ? HealthLimit : 100.f;
    MaxStamina = FMath::IsFinite(StaminaLimit) && StaminaLimit > 0.f ? StaminaLimit : 100.f;
    InitHealth(MaxHealth);
    InitStamina(MaxStamina);
    InitUltimateCharge(0.f);
}
void UCombatAttributes::PreAttributeBaseChange(const FGameplayAttribute& Attribute,float& Value) const
{
    Super::PreAttributeBaseChange(Attribute,Value);
    if(Attribute==GetUltimateChargeAttribute()) Value=FMath::IsFinite(Value)?FMath::Clamp(Value,0.f,100.f):0.f;
}
void UCombatAttributes::PreAttributeChange(const FGameplayAttribute& Attribute, float& Value)
{
    Super::PreAttributeChange(Attribute, Value);
    if(Attribute==GetUltimateChargeAttribute()) Value=FMath::IsFinite(Value)?FMath::Clamp(Value,0.f,100.f):0.f;
    if (Attribute == GetHealthAttribute())
        Value = FMath::IsFinite(Value) ? FMath::Clamp(Value, 0.f, MaxHealth) : 0.f;
    if (Attribute == GetStaminaAttribute())
        Value = FMath::IsFinite(Value) ? FMath::Clamp(Value, 0.f, MaxStamina) : 0.f;
}
void UCombatAttributes::PostGameplayEffectExecute(const FGameplayEffectModCallbackData& Data)
{
    Super::PostGameplayEffectExecute(Data);
    if(Data.EvaluatedData.Attribute==GetUltimateChargeAttribute()) SetUltimateCharge(FMath::IsFinite(GetUltimateCharge())?FMath::Clamp(GetUltimateCharge(),0.f,100.f):0.f);
    if (Data.EvaluatedData.Attribute == GetHealthAttribute()) SetHealth(FMath::IsFinite(GetHealth()) ? FMath::Clamp(GetHealth(), 0.f, MaxHealth) : 0.f);
    if (Data.EvaluatedData.Attribute == GetStaminaAttribute()) SetStamina(FMath::IsFinite(GetStamina()) ? FMath::Clamp(GetStamina(), 0.f, MaxStamina) : 0.f);
}