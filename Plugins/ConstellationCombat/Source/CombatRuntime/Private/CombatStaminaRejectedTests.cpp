#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CombatAbilitySystem.h"
#include "CombatAttributes.h"
#include "CombatActionDefinition.h"
#include "CombatLabCharacter.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/World.h"
#include <limits>

namespace CombatTest
{
    UCombatActionDefinition* Action(UObject*);
    ACombatLabCharacter* Actor(UWorld*,FVector,int32);
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatActionStaminaRejectedTest,"Constellation.CombatCore.StaminaRejected.Action",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatActionStaminaRejectedTest::RunTest(const FString&)
{
    auto* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* Combat=Actor->Combat.Get();
    auto* Action=CombatTest::Action(Actor);Action->StaminaCost=20.f;
    Actor->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    int32 Notifications=0;
    Combat->OnStaminaActionRejected.AddLambda([&]{++Notifications;});
    FString Reason;
    if(!TestTrue(TEXT("Fixture is otherwise eligible"),Combat->CanStart(Action,Reason)))
    {AddError(Reason);World->DestroyWorld(false);return false;}
    const float Health=Combat->GetHealth(),Charge=Combat->GetUltimateCharge();
    const uint64 Execution=Combat->GetExecutionId();
    for(float Stamina:{0.f,10.f})
    {
        Combat->SetNumericAttributeBase(UCombatAttributes::GetStaminaAttribute(),Stamina);
        const int32 Before=Notifications;
        TestFalse(TEXT("Insufficient stamina query rejects"),Combat->CanStart(Action,Reason));
        TestEqual(TEXT("Query never notifies"),Notifications,Before);
        TestFalse(TEXT("Actual insufficient stamina attempt rejects"),Combat->TryStartAction(Action));
        TestEqual(TEXT("Actual attempt notifies once"),Notifications,Before+1);
        TestEqual(TEXT("Original failure reason retained"),Combat->LastReason,FString(TEXT("Not enough stamina")));
        TestEqual(TEXT("Rejected action preserves stamina"),Combat->GetStamina(),Stamina);
        TestEqual(TEXT("Rejected action preserves health"),Combat->GetHealth(),Health);
        TestEqual(TEXT("Rejected action preserves ultimate"),Combat->GetUltimateCharge(),Charge);
        TestEqual(TEXT("Rejected action never begins execution"),Combat->GetExecutionId(),Execution);
    }
    const int32 BeforeOtherFailures=Notifications;
    TestFalse(TEXT("Missing action rejected"),Combat->TryStartAction(nullptr));
    Action->UltimateCost=100.f;
    TestFalse(TEXT("Missing ultimate also blocks"),Combat->TryStartAction(Action));Action->UltimateCost=0.f;
    Action->DashDistance=200.f;Action->DashDuration=.2f;
    Actor->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    TestFalse(TEXT("Airborne dash also blocks"),Combat->TryStartAction(Action));
    TestEqual(TEXT("Airborne still retains original stamina reason"),Combat->LastReason,FString(TEXT("Not enough stamina")));
    Actor->GetCharacterMovement()->SetMovementMode(MOVE_Walking);Action->DashDistance=0.f;
    auto* Mesh=Actor->GetMesh()->GetSkeletalMeshAsset();Actor->GetMesh()->SetSkeletalMesh(nullptr);
    TestFalse(TEXT("Missing compatible mesh also blocks"),Combat->TryStartAction(Action));
    Actor->GetMesh()->SetSkeletalMesh(Mesh);Actor->GetMesh()->InitAnim(true);
    TestEqual(TEXT("Other simultaneous failures are silent"),Notifications,BeforeOtherFailures);

    Combat->SetNumericAttributeBase(UCombatAttributes::GetStaminaAttribute(),100.f);Action->Cooldown=5.f;
    if(TestTrue(TEXT("Eligible action starts for cooldown fixture"),Combat->TryStartAction(Action)))
    {
        Combat->SetNumericAttributeBase(UCombatAttributes::GetStaminaAttribute(),0.f);
        TestFalse(TEXT("Active action plus exhaustion rejected silently"),Combat->TryStartAction(Action));
        Combat->CancelAction();
        TestTrue(TEXT("Cooldown is active"),Combat->GetCooldownRemaining(Action)>0.f);
        TestFalse(TEXT("Cooldown plus exhaustion rejected"),Combat->TryStartAction(Action));
        TestEqual(TEXT("Cooldown keeps original reason precedence"),Combat->LastReason,FString(TEXT("Not enough stamina")));
        TestEqual(TEXT("Cooldown and active action never flash stamina"),Notifications,BeforeOtherFailures);
        TestEqual(TEXT("Cooldown rejection preserves zero stamina"),Combat->GetStamina(),0.f);
    }
    Combat->OnStaminaActionRejected.Clear();World->DestroyWorld(false);return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDodgeStaminaRejectedTest,"Constellation.CombatCore.StaminaRejected.Dodge",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatDodgeStaminaRejectedTest::RunTest(const FString&)
{
    auto* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* Combat=Actor->Combat.Get();auto* Movement=Actor->GetCharacterMovement();
    Movement->SetMovementMode(MOVE_Walking);Combat->DodgeStaminaCost=20.f;
    int32 Notifications=0;Combat->OnStaminaActionRejected.AddLambda([&]{++Notifications;});
    const FVector Position=Actor->GetActorLocation();
    const float Health=Combat->GetHealth(),Charge=Combat->GetUltimateCharge();
    for(float Stamina:{0.f,10.f})
    {
        Combat->SetNumericAttributeBase(UCombatAttributes::GetStaminaAttribute(),Stamina);
        const int32 Before=Notifications;
        TestFalse(TEXT("Grounded dodge rejects insufficient stamina"),Combat->TryDodge(FVector::ForwardVector));
        TestEqual(TEXT("Rejected grounded dodge notifies once"),Notifications,Before+1);
        TestEqual(TEXT("Dodge rejection preserves stamina"),Combat->GetStamina(),Stamina);
        TestEqual(TEXT("Dodge rejection preserves health"),Combat->GetHealth(),Health);
        TestEqual(TEXT("Dodge rejection preserves ultimate"),Combat->GetUltimateCharge(),Charge);
        TestEqual(TEXT("Dodge rejection does not move actor"),Actor->GetActorLocation(),Position);
        TestFalse(TEXT("Rejected dodge never activates"),Combat->IsDodging());
    }
    const int32 BeforeOtherFailures=Notifications;
    Movement->SetMovementMode(MOVE_Falling);
    TestFalse(TEXT("Airborne exhausted dodge rejects"),Combat->TryDodge(FVector::ForwardVector));
    TestEqual(TEXT("Airborne preserves original stamina-first reason"),Combat->LastReason,FString(TEXT("Not enough stamina")));
    Movement->SetMovementMode(MOVE_Walking);
    TestFalse(TEXT("Invalid direction exhausted dodge rejects"),Combat->TryDodge(FVector(std::numeric_limits<double>::quiet_NaN(),0,0)));
    const float Duration=Combat->DodgeDuration;Combat->DodgeDuration=-1.f;
    TestFalse(TEXT("Invalid settings exhausted dodge rejects"),Combat->TryDodge(FVector::ForwardVector));Combat->DodgeDuration=Duration;
    TestEqual(TEXT("Other dodge failures stay silent"),Notifications,BeforeOtherFailures);
    TestEqual(TEXT("All failed attempts preserve partial stamina"),Combat->GetStamina(),10.f);
    Combat->SetNumericAttributeBase(UCombatAttributes::GetStaminaAttribute(),100.f);
    if(TestTrue(TEXT("Eligible dodge succeeds"),Combat->TryDodge(FVector::ForwardVector)))
    {
        TestEqual(TEXT("Successful dodge spends existing cost"),Combat->GetStamina(),80.f);
        TestEqual(TEXT("Successful dodge emits no rejection"),Notifications,BeforeOtherFailures);
        Combat->SetNumericAttributeBase(UCombatAttributes::GetStaminaAttribute(),0.f);
        TestFalse(TEXT("Already dodging exhaustion rejected"),Combat->TryDodge(FVector::ForwardVector));
        TestEqual(TEXT("Already dodging stays silent"),Notifications,BeforeOtherFailures);
        Combat->CancelDodge();
    }
    Combat->SetNumericAttributeBase(UCombatAttributes::GetStaminaAttribute(),100.f);
    auto* Action=CombatTest::Action(Actor);Action->StaminaCost=0.f;
    Action->bAllowDodgeCancel=true;Action->DodgeCancelStart=0.f;Action->DodgeCancelEnd=.5f;
    if(TestTrue(TEXT("Action starts for dodge handoff fixture"),Combat->TryStartAction(Action)))
    {
        const FDelegateHandle Drain=Combat->OnPresentationReset.AddLambda([Combat]
        {Combat->SetNumericAttributeBase(UCombatAttributes::GetStaminaAttribute(),0.f);});
        TestFalse(TEXT("Stamina spent by cancellation callback rejects handoff"),Combat->TryDodge(FVector::ForwardVector));
        TestEqual(TEXT("Stamina-only handoff failure notifies once"),Notifications,BeforeOtherFailures+1);
        TestEqual(TEXT("Handoff preserves original failure reason"),Combat->LastReason,FString(TEXT("Dodge transition interrupted")));
        TestEqual(TEXT("Failed handoff spends no extra stamina"),Combat->GetStamina(),0.f);
        Combat->OnPresentationReset.Remove(Drain);
    }
    Combat->OnStaminaActionRejected.Clear();World->DestroyWorld(false);return true;
}
#endif
