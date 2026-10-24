#include "Misc/AutomationTest.h"
#include "AbilityAcquisitionSubsystem.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Components/ActorComponent.h"
#include "UObject/UnrealType.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJumpAcquisitionGrantTest,"Constellation.JumpAcquisition.GrantWithoutDuplicateUI",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FJumpAcquisitionGrantTest::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);auto* PC=W->SpawnActor<APlayerController>();auto* Pawn=W->SpawnActor<APawn>();PC->Possess(Pawn);
 auto* Class=LoadClass<UActorComponent>(nullptr,TEXT("/Game/Constellation/Gameplay/Interaction/Components/Ac_Ability.Ac_Ability_C"));
 if(!TestNotNull(TEXT("Existing ability component"),Class)){W->DestroyWorld(false);return false;}
 auto* C=NewObject<UActorComponent>(Pawn,Class);auto* S=W->GetSubsystem<UAbilityAcquisitionSubsystem>();
 auto* Flag=FindFProperty<FBoolProperty>(Class,TEXT("IsJumpUnlocked"));Flag->SetPropertyValue_InContainer(C,false);
 TestTrue(TEXT("Cinematic commit calls existing unlock"),S->GrantPresentedAbility(C,0));TestTrue(TEXT("Jump flag set"),Flag->GetPropertyValue_InContainer(C));
 TestEqual(TEXT("Already presented UI not queued again"),S->PendingCount(),0);
 TestFalse(TEXT("Invalid slot does not grant"),S->GrantPresentedAbility(C,3));
 TestFalse(TEXT("No owner cannot take UI lease"),S->PresentForScene(nullptr,0,0));
 S->Enqueue(1,1);TestEqual(TEXT("Ordinary acquisition still queued"),S->PendingCount(),1);
 S->CancelScene(nullptr);TestEqual(TEXT("Unowned cancellation must not remove ordinary UI"),S->PendingCount(),1);
 W->DestroyWorld(false);return true;
}
