#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CombatAbilitySystem.h"
#include "CombatAttributes.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "GameplayEffect.h"
#include <limits>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatResourceLimitsTest, "Constellation.CombatCore.ResourceLimits",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatResourceLimitsTest::RunTest(const FString&)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
    auto MakeCombat = [World](float Health, float Stamina)
    {
        AActor* Actor = World->SpawnActor<AActor>();
        auto* Combat = NewObject<UCombatAbilitySystem>(Actor);
        Actor->AddInstanceComponent(Combat);
        Combat->RegisterComponent();
        Combat->MaxHealth = Health;
        Combat->MaxStamina = Stamina;
        Combat->InitializeCombat(Actor);
        return Combat;
    };
    auto Modify = [](UCombatAbilitySystem* Combat, const FGameplayAttribute& Attribute, float Delta)
    {
        UGameplayEffect* Effect = NewObject<UGameplayEffect>();
        Effect->DurationPolicy = EGameplayEffectDurationType::Instant;
        FGameplayModifierInfo& Modifier = Effect->Modifiers.AddDefaulted_GetRef();
        Modifier.Attribute = Attribute;
        Modifier.ModifierOp = EGameplayModOp::Additive;
        Modifier.ModifierMagnitude = FScalableFloat(Delta);
        Combat->ApplyGameplayEffectSpecToSelf(FGameplayEffectSpec(Effect, Combat->MakeEffectContext(), 1.f));
    };
    UCombatAbilitySystem* Combat = MakeCombat(250.f, 60.f);
    TestEqual(TEXT("Configured health is initialized"), Combat->GetHealth(), 250.f);
    TestEqual(TEXT("Configured stamina is initialized"), Combat->GetStamina(), 60.f);
    TestEqual(TEXT("Actual health maximum"), Combat->GetMaxHealth(), 250.f);
    TestEqual(TEXT("Actual stamina maximum"), Combat->GetMaxStamina(), 60.f);
    TestTrue(TEXT("Damage applies above the old health cap"), Combat->ReceiveCombatDamage(30.f, nullptr));
    TestEqual(TEXT("Damage preserves health above 100"), Combat->GetHealth(), 220.f);
    Modify(Combat, UCombatAttributes::GetHealthAttribute(), 1000.f);
    TestEqual(TEXT("Healing effect clamps to configured health maximum"), Combat->GetHealth(), 250.f);
    Modify(Combat, UCombatAttributes::GetStaminaAttribute(), -1000.f);
    TestEqual(TEXT("Stamina effect clamps to zero"), Combat->GetStamina(), 0.f);
    Combat->TickComponent(20.f, LEVELTICK_All, nullptr);
    TestEqual(TEXT("Recovery stops at configured stamina maximum"), Combat->GetStamina(), 60.f);
    Modify(Combat, UCombatAttributes::GetStaminaAttribute(), 1000.f);
    TestEqual(TEXT("Stamina effect clamps to configured maximum"), Combat->GetStamina(), 60.f);
    Combat->ReceiveCombatDamage(90.f, nullptr);
    Modify(Combat, UCombatAttributes::GetStaminaAttribute(), -40.f);
    Combat->ResetAfterReturn();
    TestEqual(TEXT("Return restores configured health"), Combat->GetHealth(), 250.f);
    TestEqual(TEXT("Return restores configured stamina"), Combat->GetStamina(), 60.f);
    Combat->MaxHealth = 10.f;
    Combat->MaxStamina = 10.f;
    Combat->InitializeCombat(Combat->GetOwner());
    TestEqual(TEXT("Initialization remains idempotent"), Combat->GetMaxHealth(), 250.f);
    TestEqual(TEXT("Initialized stamina maximum remains authoritative"), Combat->GetMaxStamina(), 60.f);
    Combat->ReceiveCombatDamage(1000.f, nullptr);
    TestEqual(TEXT("Overkill clamps health to zero"), Combat->GetHealth(), 0.f);
    Combat->ResetAfterReturn();
    TestEqual(TEXT("Return never resurrects a dead actor"), Combat->GetHealth(), 0.f);
    for (float Invalid : {0.f, -1.f, std::numeric_limits<float>::quiet_NaN(), std::numeric_limits<float>::infinity()})
    {
        UCombatAbilitySystem* InvalidCombat = MakeCombat(Invalid, Invalid);
        TestEqual(TEXT("Invalid health maximum falls back to 100"), InvalidCombat->GetMaxHealth(), 100.f);
        TestEqual(TEXT("Invalid stamina maximum falls back to 100"), InvalidCombat->GetMaxStamina(), 100.f);
        TestEqual(TEXT("Fallback health starts full"), InvalidCombat->GetHealth(), 100.f);
        TestEqual(TEXT("Fallback stamina starts full"), InvalidCombat->GetStamina(), 100.f);
    }
    World->DestroyWorld(false);
    return true;
}
#endif