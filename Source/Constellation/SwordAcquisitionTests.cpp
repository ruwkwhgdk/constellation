#include "Misc/AutomationTest.h"
#include "SwordAcquisitionStage.h"
#include "SceneDirectorPlayer.h"
#include "ItemAcquisitionDefinition.h"
#include "Blueprint/UserWidget.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/Texture2D.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "UObject/UnrealType.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSwordAcquisitionInputTest,"Constellation.SwordAcquisition.InputOwnership",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSwordAcquisitionInputTest::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());auto* PC=W->SpawnActor<APlayerController>();W->AddController(PC);auto* C=W->SpawnActor<ACharacter>();PC->Possess(C);
 auto* Class=LoadClass<UActorComponent>(nullptr,TEXT("/Game/Constellation/Gameplay/Interaction/Components/Ac_Ability.Ac_Ability_C"));
 if(!TestNotNull(TEXT("Existing ability schema"),Class)){GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return false;}
 auto* Ability=NewObject<UActorComponent>(C,Class);C->AddInstanceComponent(Ability);
 FindFProperty<FBoolProperty>(Class,TEXT("IsJumpUnlocked"))->SetPropertyValue_InContainer(Ability,true);
 FindFProperty<FBoolProperty>(Class,TEXT("IsCombatUnlocked"))->SetPropertyValue_InContainer(Ability,false);
 FindFProperty<FBoolProperty>(Class,TEXT("IsAttackUnlocked"))->SetPropertyValue_InContainer(Ability,false);
 for(bool InitiallyEnabled:{true,false})
 {
  if(InitiallyEnabled)C->EnableInput(PC);else C->DisableInput(PC);
  auto* Stage=W->SpawnActor<ASwordAcquisitionStage>();auto* Runner=W->SpawnActor<ASceneDirectorPlayer>();Stage->Sword=W->SpawnActor<AActor>();Stage->ItemDefinition=NewObject<UItemAcquisitionDefinition>();Stage->ItemDefinition->Presentation.Sprite=NewObject<UTexture2D>();
  TestTrue(TEXT("Begin acquisition"),Stage->RunCue(Runner,TEXT("Begin")));
  TestFalse(TEXT("Gameplay attack input disabled through scene"),C->InputEnabled());
  TestFalse(TEXT("Cannot commit before item confirmation"),Stage->RunCue(Runner,TEXT("Commit")));
  Runner->OnDirectorStopped.Broadcast(false);
  TestEqual(TEXT("Original pawn input restored on cancellation"),C->InputEnabled(),InitiallyEnabled);
  TestFalse(TEXT("Cancellation does not grant combat"),FindFProperty<FBoolProperty>(Class,TEXT("IsCombatUnlocked"))->GetPropertyValue_InContainer(Ability));
  TestFalse(TEXT("Cancellation does not grant attack"),FindFProperty<FBoolProperty>(Class,TEXT("IsAttackUnlocked"))->GetPropertyValue_InContainer(Ability));
  Stage->Destroy();Runner->Destroy();
 }
 GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
