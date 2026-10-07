#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CombatLabCharacter.h"
#include "CombatAbilitySystem.h"
#include "CombatActionDefinition.h"
#include "CarryComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatCarryIntegrationTest,"Constellation.CombatCore.ProjectCarryPriority",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatCarryIntegrationTest::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);
 auto* A=W->SpawnActor<ACombatLabCharacter>(FVector(0,0,100),FRotator::ZeroRotator);
 A->GetMesh()->SetSkeletalMeshAsset(LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/SK_player_heroine_new_RunPreview.SK_player_heroine_new_RunPreview")));
 A->GetMesh()->SetAnimationMode(EAnimationMode::AnimationSingleNode);A->GetMesh()->InitAnim(true);
 auto* Carry=NewObject<UCarryComponent>(A);A->AddInstanceComponent(Carry);Carry->RegisterComponent();
 A->DispatchBeginPlay();
 auto* Action=LoadObject<UCombatActionDefinition>(nullptr,TEXT("/Game/Constellation/Review/CombatCore/DA_PlayerSlash.DA_PlayerSlash"));
 A->SkillAction=Action;A->UltimateAction=Action;Carry->State=ECarryState::Carrying;
 TestFalse(TEXT("Carry consumes basic combat"),A->Combat->TryStartAction(Action));
 TestFalse(TEXT("Carry blocks Q"),A->UseSpecialAction(false));
 TestFalse(TEXT("Carry blocks E"),A->UseSpecialAction(true));
 A->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
 TestFalse(TEXT("Carry blocks dodge"),A->Combat->TryDodge(FVector::ForwardVector));
 TestEqual(TEXT("Blocked inputs spend no SP"),A->Combat->GetStamina(),100.f);
 Carry->State=ECarryState::Idle;A->Combat->CancelAction();A->Combat->CancelDodge();
 auto* PC=W->SpawnActor<APlayerController>();PC->Possess(A);PC->SetIgnoreMoveInput(true);
 TestFalse(TEXT("Scene movement lock blocks combat"),A->Combat->TryStartAction(Action));
 PC->SetIgnoreMoveInput(false);
 TestTrue(TEXT("Combat resumes after carry"),A->Combat->TryStartAction(Action));
 Carry->State=ECarryState::Carrying;
 TestTrue(TEXT("Combat damage accepted"),A->Combat->ReceiveCombatDamage(5,nullptr));
 TestEqual(TEXT("Real any-damage event aborts carry"),Carry->State,ECarryState::Idle);
 W->DestroyWorld(false);return true;
}
#endif
