#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CombatAbilitySystem.h"
#include "CombatAttributes.h"
#include "CombatActionDefinition.h"
#include "CombatLabCharacter.h"
#include "CombatWorkbenchSubsystem.h"
#include "Engine/GameInstance.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/World.h"
#include <limits>
namespace CombatTest {
UCombatActionDefinition* Action(UObject* Outer);
ACombatLabCharacter* Actor(UWorld* World,FVector Location,int32 Team);
int32 Instance(ACombatLabCharacter* Actor,UCombatActionDefinition* Action);
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatUltimateResourceTest,"Constellation.CombatCore.UltimateResource",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatUltimateResourceTest::RunTest(const FString&)
{
    UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);
    auto* A=CombatTest::Actor(W,FVector(0,0,100),0);
    auto* V=CombatTest::Actor(W,FVector(1000,0,100),1);
    auto* C=A->Combat.Get();auto* Ultimate=CombatTest::Action(A);
    Ultimate->UltimateCost=100;Ultimate->UltimateGain=0;Ultimate->StaminaCost=20;Ultimate->Cooldown=10;
    TestEqual(TEXT("Charge initially empty"),C->GetUltimateCharge(),0.f);
    TestFalse(TEXT("Empty charge rejects ultimate"),C->TryStartAction(Ultimate));
    TestEqual(TEXT("Rejected cast keeps stamina"),C->GetStamina(),100.f);
    TestEqual(TEXT("Rejected cast starts no cooldown"),C->GetCooldownRemaining(Ultimate),0.f);
    C->CancelAction();
    auto* Basic=CombatTest::Action(A);Basic->UltimateGain=15;
    TestTrue(TEXT("Basic attack starts"),C->TryStartAction(Basic));
    const int32 Id=CombatTest::Instance(A,Basic);
    C->OpenHitWindow(TEXT("Charge"),Id);
    TestTrue(TEXT("Damaging hit accepted"),C->ApplyHit(TEXT("Charge"),V));
    TestEqual(TEXT("Hit grants configured charge"),C->GetUltimateCharge(),15.f);
    TestFalse(TEXT("Duplicate hit rejected"),C->ApplyHit(TEXT("Charge"),V));
    TestEqual(TEXT("Duplicate grants nothing"),C->GetUltimateCharge(),15.f);
    V->Combat->TickComponent(1,LEVELTICK_All,nullptr);
    V->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    V->Combat->TryDodge(FVector::ForwardVector);
    V->Combat->TickComponent(.15f,LEVELTICK_All,nullptr);
    C->OpenHitWindow(TEXT("Immune"),Id);
    TestFalse(TEXT("Invulnerable hit rejected"),C->ApplyHit(TEXT("Immune"),V));
    TestEqual(TEXT("Avoided hit grants nothing"),C->GetUltimateCharge(),15.f);
    V->Combat->CancelDodge();
    Basic->Damage=0;C->OpenHitWindow(TEXT("Zero"),Id);
    TestFalse(TEXT("Zero damage grants no hit"),C->ApplyHit(TEXT("Zero"),V));
    TestEqual(TEXT("Zero damage grants no charge"),C->GetUltimateCharge(),15.f);
    C->CancelAction();
    C->SetNumericAttributeBase(UCombatAttributes::GetUltimateChargeAttribute(),200);
    TestEqual(TEXT("Charge capped at100"),C->GetUltimateCharge(),100.f);
    TestTrue(TEXT("Funded ultimate starts"),C->TryStartAction(Ultimate));
    TestEqual(TEXT("Ultimate cost consumed"),C->GetUltimateCharge(),0.f);
    TestEqual(TEXT("Both accepted costs consumed"),C->GetStamina(),70.f);
    C->CancelAction();
    C->SetNumericAttributeBase(UCombatAttributes::GetUltimateChargeAttribute(),100);
    TestFalse(TEXT("Cooldown still blocks with charge"),C->TryStartAction(Ultimate));
    TestEqual(TEXT("Cooldown failure keeps charge"),C->GetUltimateCharge(),100.f);
    C->SetNumericAttributeBase(UCombatAttributes::GetUltimateChargeAttribute(),-10);
    TestEqual(TEXT("Charge lower bound"),C->GetUltimateCharge(),0.f);
    C->SetNumericAttributeBase(UCombatAttributes::GetUltimateChargeAttribute(),std::numeric_limits<float>::quiet_NaN());
    TestEqual(TEXT("Nonfinite charge contained"),C->GetUltimateCharge(),0.f);
    W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatUltimateCommitTest,"Constellation.CombatCore.UltimateCommitReentry",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatUltimateCommitTest::RunTest(const FString&)
{
    UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);
    auto* A=CombatTest::Actor(W,FVector(0,0,100),0);auto* C=A->Combat.Get();
    A->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    auto* Ultimate=CombatTest::Action(A);Ultimate->UltimateCost=100;Ultimate->StaminaCost=30;Ultimate->Cooldown=10;
    auto* Next=CombatTest::Action(A);Next->StaminaCost=0;
    C->SetNumericAttributeBase(UCombatAttributes::GetUltimateChargeAttribute(),100);
    bool Nested=false,Dodge=false,Entered=false;
    auto Handle=C->GetGameplayAttributeValueChangeDelegate(UCombatAttributes::GetStaminaAttribute()).AddLambda(
        [&](const FOnAttributeChangeData& Change){
            if(Change.NewValue>=Change.OldValue) return;
            Entered=true;C->CancelAction();
            Nested=C->TryStartAction(Next);Dodge=C->TryDodge(FVector::ForwardVector);
            Ultimate->UltimateCost=0;
        });
    TestFalse(TEXT("Cancellation during commit is not active success"),C->TryStartAction(Ultimate));
    TestTrue(TEXT("Cost callback ran"),Entered);
    TestFalse(TEXT("No attack can exploit half-committed resources"),Nested);
    TestFalse(TEXT("No dodge can exploit half-committed resources"),Dodge);
    TestEqual(TEXT("Stamina paid once"),C->GetStamina(),70.f);
    TestEqual(TEXT("Charge uses accepted snapshot"),C->GetUltimateCharge(),0.f);
    TestFalse(TEXT("No action left"),C->IsActing());
    TestTrue(TEXT("Committed cooldown retained"),C->GetCooldownRemaining(Ultimate)>0);
    C->GetGameplayAttributeValueChangeDelegate(UCombatAttributes::GetStaminaAttribute()).Remove(Handle);
    W->DestroyWorld(false);return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatSpecialSlotsTest,"Constellation.CombatCore.SpecialSlots",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatSpecialSlotsTest::RunTest(const FString&)
{
    UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);
    auto* A=CombatTest::Actor(W,FVector(0,0,100),0);auto* C=A->Combat.Get();
    TestFalse(TEXT("Empty skill slot rejects"),A->UseSpecialAction(false));
    A->SkillAction=CombatTest::Action(A);A->SkillAction->StaminaCost=15;A->SkillAction->Cooldown=5;
    A->UltimateAction=CombatTest::Action(A);A->UltimateAction->StaminaCost=0;A->UltimateAction->UltimateCost=100;
    A->bWorkbenchOpen=true;
    TestFalse(TEXT("Editor focus blocks skill"),A->UseSpecialAction(false));A->bWorkbenchOpen=false;
    TestTrue(TEXT("Skill slot starts configured action"),A->UseSpecialAction(false));
    TestTrue(TEXT("Uses assigned skill"),C->GetActiveAction()==A->SkillAction);
    TestEqual(TEXT("Skill pays configured SP"),C->GetStamina(),85.f);
    TestFalse(TEXT("Another cast cannot overlap"),A->UseSpecialAction(true));
    C->CancelAction();
    TestFalse(TEXT("Cooldown blocks skill"),A->UseSpecialAction(false));
    TestFalse(TEXT("Charge blocks ultimate"),A->UseSpecialAction(true));
    TestEqual(TEXT("Rejected casts preserve SP"),C->GetStamina(),85.f);
    C->SetNumericAttributeBase(UCombatAttributes::GetUltimateChargeAttribute(),100);
    TestTrue(TEXT("Charged ultimate slot starts"),A->UseSpecialAction(true));
    TestTrue(TEXT("Uses assigned ultimate"),C->GetActiveAction()==A->UltimateAction);
    TestEqual(TEXT("Ultimate consumes charge"),C->GetUltimateCharge(),0.f);
    W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatSlotCloneTest,"Constellation.CombatCore.SpecialSlotClone",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatSlotCloneTest::RunTest(const FString&)
{
    UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);
    auto* First=CombatTest::Actor(W,FVector(0,0,100),0);
    auto* Second=CombatTest::Actor(W,FVector(1000,0,100),0);
    auto* Shared=CombatTest::Action(W);
    auto* Model=NewObject<UCombatWorkbenchSubsystem>(NewObject<UGameInstance>());
    for(auto* A:{First,Second})
    {
        A->Action=Shared;A->SkillAction=Shared;
        A->UltimateAction=CombatTest::Action(W);
        Model->PrepareActor(A);
    }
    TestTrue(TEXT("Same source remains same runtime action within actor"),First->Action==First->SkillAction);
    TestTrue(TEXT("Different actors never share slot clones"),First->SkillAction!=Second->SkillAction);
    TestTrue(TEXT("Original skill not edited"),First->SkillAction!=Shared);
    TestTrue(TEXT("Ultimate is a runtime clone"),First->UltimateAction->GetOuter()==Model);
    First->SkillAction->Damage=53;
    TestEqual(TEXT("Other player's slot stays unchanged"),Second->SkillAction->Damage,20.f);
    TestEqual(TEXT("Source stays unchanged"),Shared->Damage,20.f);
    W->DestroyWorld(false);return true;
}

#endif
