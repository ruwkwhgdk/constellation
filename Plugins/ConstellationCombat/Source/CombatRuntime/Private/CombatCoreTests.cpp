#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include <limits>
#include "CombatHitLedger.h"
#include "CombatAbilitySystem.h"
#include "CombatActionDefinition.h"
#include "CombatLabCharacter.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatLedgerTest, "Constellation.CombatCore.HitLedger",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatLedgerTest::RunTest(const FString&)
{
    FCombatHitLedger Ledger;
    UObject* Target = NewObject<UCombatActionDefinition>();
    TestFalse(TEXT("Inactive execution rejects window"), Ledger.Open("Swing"));
    const uint64 First = Ledger.Begin();
    TestTrue(TEXT("Window opens"), Ledger.Open("Swing"));
    TestTrue(TEXT("First target contact"), Ledger.Claim("Swing", Target));
    TestFalse(TEXT("Multiple colliders and frames do not repeat hit"), Ledger.Claim("Swing", Target));
    Ledger.Close("Swing");
    Ledger.Open("Swing");
    TestFalse(TEXT("Reopening same window does not reset hit history"), Ledger.Claim("Swing", Target));
    Ledger.Open("Second");
    TestTrue(TEXT("Explicit second hit window permits next hit"), Ledger.Claim("Second", Target));
    Ledger.End();
    TestFalse(TEXT("Cancellation clears active window"), Ledger.Claim("Second", Target));
    TestFalse(TEXT("Late notification cannot reopen ended execution"), Ledger.Open("Swing"));
    TestTrue(TEXT("Next execution has a new ID"), Ledger.Begin() > First);
    Ledger.Open("Swing");
    TestTrue(TEXT("New attack may hit same target"), Ledger.Claim("Swing", Target));
    TestFalse(TEXT("Null target rejected"), Ledger.Claim("Swing", nullptr));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDamageTest, "Constellation.CombatCore.DamageAndDeath",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatDamageTest::RunTest(const FString&)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
    ACombatLabCharacter* Victim = World->SpawnActor<ACombatLabCharacter>();
    UCombatAbilitySystem* ASC = Victim->Combat;
    ASC->InitializeCombat(Victim);
    int32 Deaths = 0;
    ASC->OnDied.AddLambda([&Deaths]() { ++Deaths; });
    TestEqual(TEXT("Initial health"), ASC->GetHealth(), 100.f);
    TestFalse(TEXT("Negative damage cannot heal"), ASC->ReceiveCombatDamage(-10.f, nullptr));
    TestFalse(TEXT("NaN damage rejected"), ASC->ReceiveCombatDamage(std::numeric_limits<float>::quiet_NaN(), nullptr));
    TestTrue(TEXT("Damage accepted"), ASC->ReceiveCombatDamage(30.f, nullptr));
    TestEqual(TEXT("Single health source"), ASC->GetHealth(), 70.f);
    TestTrue(TEXT("Lethal damage accepted"), ASC->ReceiveCombatDamage(200.f, nullptr));
    TestEqual(TEXT("Health clamps to zero"), ASC->GetHealth(), 0.f);
    TestFalse(TEXT("Dead actor cannot receive more damage"), ASC->ReceiveCombatDamage(1.f, nullptr));
    TestEqual(TEXT("Death fires once"), Deaths, 1);
    ASC->InitializeCombat(Victim);
    TestEqual(TEXT("Idempotent initialization never resurrects"), ASC->GetHealth(), 0.f);
    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatInvalidActionTest, "Constellation.CombatCore.InvalidAction",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatInvalidActionTest::RunTest(const FString&)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
    ACombatLabCharacter* Actor = World->SpawnActor<ACombatLabCharacter>();
    Actor->Combat->InitializeCombat(Actor);
    UCombatActionDefinition* Action = NewObject<UCombatActionDefinition>();
    FString Reason;
    TestFalse(TEXT("Missing montage is invalid"), Action->Validate(Reason));
    TestFalse(TEXT("Invalid action cannot activate"), Actor->Combat->TryStartAction(Action));
    TestEqual(TEXT("Failure preserves stamina"), Actor->Combat->GetStamina(), 100.f);
    TestFalse(TEXT("No active action"), Actor->Combat->IsActing());
    TestFalse(TEXT("Null action rejected"), Actor->Combat->TryStartAction(nullptr));
    World->DestroyWorld(false);
    return true;
}
#endif
