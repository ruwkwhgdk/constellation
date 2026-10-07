#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CombatEncounterDirector.h"
#include "CombatLabCharacter.h"
#include "CombatAbilitySystem.h"
#include "CombatActionDefinition.h"
#include "Engine/World.h"
namespace CombatTest {
 UCombatActionDefinition* Action(UObject*);
 ACombatLabCharacter* Actor(UWorld*,FVector,int32);
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDirectorTest,"Constellation.CombatCore.EncounterConcurrency",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatDirectorTest::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);auto* D=W->SpawnActor<ACombatEncounterDirector>();
 D->Player=CombatTest::Actor(W,FVector(-1000,0,100),0);
 for(int32 I=0;I<3;++I)
 {
  auto* A=CombatTest::Actor(W,FVector(I*500,0,100),1);A->bTrainingEnemy=true;
  A->EncounterDirector=D;A->Action=CombatTest::Action(A);A->Action->StaminaCost=0;D->Enemies.Add(A);
 }
 auto* A=D->Enemies[0]->Combat.Get();auto* B=D->Enemies[1]->Combat.Get();auto* C=D->Enemies[2]->Combat.Get();
 TestTrue(TEXT("First gets attack slot"),A->TryStartAction(D->Enemies[0]->Action));
 TestFalse(TEXT("Second waits with concurrency one"),B->TryStartAction(D->Enemies[1]->Action));
 TestEqual(TEXT("One attacker retained"),D->ActiveAttackers(),1);
 A->CancelAction();
 TestTrue(TEXT("Cancellation releases slot"),B->TryStartAction(D->Enemies[1]->Action));
 B->ReceiveCombatDamage(1000,nullptr);
 TestTrue(TEXT("Death releases slot"),C->TryStartAction(D->Enemies[2]->Action));
 D->MaxAttackers=2;
 TestTrue(TEXT("Two simultaneous allowed"),A->TryStartAction(D->Enemies[0]->Action));
 TestEqual(TEXT("Two holders"),D->ActiveAttackers(),2);
 A->ResetAfterReturn();TestEqual(TEXT("Return reset releases slot"),D->ActiveAttackers(),1);
 A->ReceiveCombatDamage(1000,nullptr);C->ReceiveCombatDamage(1000,nullptr);D->Tick(.1f);
 TestEqual(TEXT("All defeated completes encounter"),D->Outcome,ECombatEncounterOutcome::Completed);
 D->Player->Combat->ReceiveCombatDamage(1000,nullptr);D->Tick(.1f);
 TestEqual(TEXT("Final outcome is stable"),D->Outcome,ECombatEncounterOutcome::Completed);
 TestFalse(TEXT("Completed encounter rejects acquisition"),D->CanAcquire(A));
 W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDirectorFailureTest,"Constellation.CombatCore.EncounterFailureCleanup",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatDirectorFailureTest::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);auto* D=W->SpawnActor<ACombatEncounterDirector>();
 D->Player=CombatTest::Actor(W,FVector(-1000,0,100),0);
 auto* A=CombatTest::Actor(W,FVector(0,0,100),1);A->bTrainingEnemy=true;A->EncounterDirector=D;D->Enemies.Add(A);
 auto* Action=CombatTest::Action(A);TestTrue(TEXT("Enemy starts"),A->Combat->TryStartAction(Action));
 D->Player->Combat->ReceiveCombatDamage(1000,nullptr);D->Tick(.1f);
 TestEqual(TEXT("Player death fails encounter"),D->Outcome,ECombatEncounterOutcome::Failed);
 TestFalse(TEXT("Failure cancels active enemy"),A->Combat->IsActing());
 TestEqual(TEXT("No leaked slot after failure"),D->ActiveAttackers(),0);
 W->DestroyWorld(false);return true;
}
#include "SceneEventSubsystem.h"
#include "SceneEventBinding.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorPlayer.h"
#include "GameFramework/PlayerController.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatSceneBridgeTest,"Constellation.CombatCore.EncounterSceneSignal",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatSceneBridgeTest::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);
 GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());
 auto* D=W->SpawnActor<ACombatEncounterDirector>();D->BattleZoneKey=TEXT("CombatTest");D->bNotifySceneEvents=true;
 D->Player=CombatTest::Actor(W,FVector(-1000,0,100),0);
 auto* PC=W->SpawnActor<APlayerController>();PC->Possess(D->Player);
 auto* Enemy=CombatTest::Actor(W,FVector(0,0,100),1);D->Enemies.Add(Enemy);
 auto* Events=W->GetSubsystem<USceneEventSubsystem>();
 auto* Asset=NewObject<USceneDirectorAsset>();Asset->EventKey=TEXT("CombatTest");
 for(auto Type:{EDirectorNodeType::Start,EDirectorNodeType::Wait,EDirectorNodeType::End})
 {FDirectorStep Step;Step.Type=Type;Step.Duration=.1f;Asset->Steps.Add(Step);}
 Asset->Steps[0].NextNodes={Asset->Steps[1].Id};Asset->Steps[1].NextNodes={Asset->Steps[2].Id};
 FString Error;TestTrue(TEXT("Scene fixture compiles"),FSceneDirectorCompiler::Compile(*Asset,Error));
 auto* Binding=W->SpawnActor<ASceneEventBinding>();Binding->Trigger=ESceneEventTrigger::Combat;
 Binding->CombatKey=D->BattleZoneKey;Binding->Director=Asset;Events->Register(Binding);
 Enemy->Combat->ReceiveCombatDamage(1000,nullptr);D->Tick(.1f);
 TestTrue(TEXT("Encounter has unique completion identity"),D->BattleInstance.IsValid());
 if(TestNotNull(TEXT("Victory reaches existing scene event system"),Events->ActivePlayer.Get()))Events->ActivePlayer->StopDirector();
 D->Tick(.1f);TestNull(TEXT("No duplicate completion signal"),Events->ActivePlayer.Get());
 Events->CancelActive();GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
#endif
