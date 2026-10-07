#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "UObject/UObjectGlobals.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSceneEventContractTest,"Constellation.SceneDirector.EventAuthoringContract",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSceneEventContractTest::RunTest(const FString&)
{
 auto* Binding=FindObject<UClass>(nullptr,TEXT("/Script/SceneDirectorRuntime.SceneEventBinding"));
 TestNotNull(TEXT("Level event binding available to designers"),Binding);
 TestNotNull(TEXT("World event coordinator registered"),FindObject<UClass>(nullptr,TEXT("/Script/SceneDirectorRuntime.SceneEventSubsystem")));
 if(Binding){TestNotNull(TEXT("Trigger type editable"),Binding->FindPropertyByName(TEXT("Trigger")));TestNotNull(TEXT("Cinematic asset selectable"),Binding->FindPropertyByName(TEXT("Director")));}
 return true;
}
#endif
#if WITH_DEV_AUTOMATION_TESTS
#include "SceneEventBinding.h"
#include "SceneEventSubsystem.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorPlayer.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Camera/CameraActor.h"
struct FEventFixture
{
 UWorld* W;USceneEventSubsystem* S;USceneDirectorAsset* Asset;
 FEventFixture(){W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());auto* PC=W->SpawnActor<APlayerController>();PC->Possess(W->SpawnActor<APawn>());S=W->GetSubsystem<USceneEventSubsystem>();Asset=NewObject<USceneDirectorAsset>();Asset->EventKey=TEXT("Event");for(auto T:{EDirectorNodeType::Start,EDirectorNodeType::SpawnNPC,EDirectorNodeType::CinematicMode,EDirectorNodeType::Wait,EDirectorNodeType::End}){FDirectorStep Step;Step.Type=T;Step.ActorClass=ACameraActor::StaticClass();Step.Role=TEXT("Prop");Step.Duration=1;Asset->Steps.Add(Step);}for(int I=0;I<4;++I)Asset->Steps[I].NextNodes={Asset->Steps[I+1].Id};FString Error;FSceneDirectorCompiler::Compile(*Asset,Error);}
 ASceneEventBinding* Add(ESceneEventTrigger Trigger){auto* B=W->SpawnActor<ASceneEventBinding>();B->Trigger=Trigger;B->Director=Asset;B->CombatKey=TEXT("Fight");S->Register(B);return B;}
 ~FEventFixture(){S->CancelActive();GEngine->DestroyWorldContext(W);W->DestroyWorld(false);}
};
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSceneEventQueueTest,"Constellation.SceneDirector.EventQueueLifecycle",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSceneEventQueueTest::RunTest(const FString&)
{
 FEventFixture F;auto* A=F.Add(ESceneEventTrigger::Combat);auto* B=F.Add(ESceneEventTrigger::Combat);B->Repeat=ESceneEventRepeat::OncePerVisit;
 TestTrue(TEXT("First starts"),F.S->Request(A));TestTrue(TEXT("Second queued"),F.S->Request(B));TestFalse(TEXT("Duplicate rejected"),F.S->Request(B));TestEqual(TEXT("One queued"),F.S->PendingCount(),1);
 F.S->CancelActive();TestFalse(TEXT("Cancel not consumed"),F.S->IsConsumed(A->EventId));F.S->Tick(0);if(TestNotNull(TEXT("Queue drained"),F.S->ActivePlayer.Get()))F.S->ActivePlayer->Tick(2);
 TestTrue(TEXT("Natural finish consumed"),F.S->IsConsumed(B->EventId));TestFalse(TEXT("One-shot cannot replay"),F.S->Request(B));
 auto* V=F.Add(ESceneEventTrigger::Volume);F.S->Request(A);F.S->Request(V);F.S->CancelActive();F.S->Tick(0);TestNull(TEXT("Volume exit cancels queued request"),F.S->ActivePlayer.Get());
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSceneEventSignalTest,"Constellation.SceneDirector.EventSignals",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSceneEventSignalTest::RunTest(const FString&)
{
 FEventFixture F;auto* B=F.Add(ESceneEventTrigger::Combat);auto Id=FGuid::NewGuid();F.S->NotifyCombatFinished(TEXT("Fight"),Id,ESceneCombatResult::Defeat);TestNull(TEXT("Defeat does not trigger victory"),F.S->ActivePlayer.Get());F.S->NotifyCombatFinished(TEXT("Fight"),Id,ESceneCombatResult::Victory);if(TestNotNull(TEXT("Victory starts"),F.S->ActivePlayer.Get()))F.S->ActivePlayer->Tick(2);F.S->NotifyCombatFinished(TEXT("Fight"),Id,ESceneCombatResult::Victory);TestNull(TEXT("Duplicate victory ignored"),F.S->ActivePlayer.Get());
 auto* L=F.Add(ESceneEventTrigger::LevelReady);F.S->NotifyLevelReady();TestNotNull(TEXT("Explicit ready starts level event"),F.S->ActivePlayer.Get());F.S->CancelActive();F.S->NotifyLevelReady();TestNull(TEXT("Ready latch once"),F.S->ActivePlayer.Get());
 auto* D=F.Add(ESceneEventTrigger::Destroyed);D->Source=F.W->SpawnActor<ACameraActor>();D->Source->SetActorLocation(FVector(12,34,56));D->Origin=ESceneEventOrigin::Source;
 D->DispatchBeginPlay();F.S->Request(B);D->Source->Destroy();TestEqual(TEXT("Real OnDestroyed callback queued"),F.S->PendingCount(),1);F.S->CancelActive();F.S->Tick(0);if(TestNotNull(TEXT("Source loss does not lose request"),F.S->ActivePlayer.Get()))TestTrue(TEXT("Origin captured"),F.S->ActivePlayer->OriginTransform.GetLocation().Equals(FVector(12,34,56)));return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSceneEventValidationTest,"Constellation.SceneDirector.EventValidation",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSceneEventValidationTest::RunTest(const FString&)
{
 FEventFixture F;auto* B=F.Add(ESceneEventTrigger::Destroyed);FString Error;TestFalse(TEXT("Missing source rejected"),B->Validate(Error));B->Source=F.W->SpawnActor<ACameraActor>();B->Objects.Add(TEXT("Gone"),B->Source);TestFalse(TEXT("Destroyed source cannot be reused"),B->Validate(Error));B->Objects.Reset();TestTrue(TEXT("Valid binding"),B->Validate(Error));auto* Other=F.Add(ESceneEventTrigger::Combat);Other->EventId=B->EventId;TestFalse(TEXT("Duplicate id rejected"),Other->Validate(Error));return true;
}
#endif


#if WITH_DEV_AUTOMATION_TESTS
#include "TimerManager.h"
#include "GameFramework/WorldSettings.h"
#include "Tests/AutomationCommon.h"
#include "Components/SphereComponent.h"
#include "Components/BoxComponent.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSceneEventInitialOverlapTest,"Constellation.SceneDirector.EventInitialOverlap",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSceneEventInitialOverlapTest::RunTest(const FString&)
{
 auto Fixture=MakeShared<FEventFixture>();auto& F=*Fixture;APawn* Pawn=F.W->GetFirstPlayerController()->GetPawn();auto* Shape=NewObject<USphereComponent>(Pawn);Pawn->SetRootComponent(Shape);Pawn->AddInstanceComponent(Shape);Shape->InitSphereRadius(30);Shape->SetCollisionProfileName(TEXT("Pawn"));Shape->SetGenerateOverlapEvents(true);Shape->RegisterComponent();Pawn->DispatchBeginPlay();Pawn->SetActorLocation(FVector::ZeroVector);
 auto* B=F.Add(ESceneEventTrigger::Volume);B->Area->SetCollisionEnabled(ECollisionEnabled::NoCollision);B->DispatchBeginPlay();F.W->GetWorldSettings()->NotifyBeginPlay();B->Area->SetCollisionEnabled(ECollisionEnabled::QueryOnly);B->Area->UpdateOverlaps();
 TestTrue(TEXT("Initial physical overlap established"),B->PlayerInside());TestNull(TEXT("Initial overlap never auto fires before ready"),F.S->ActivePlayer.Get());
 ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(.05f));
 ADD_LATENT_AUTOMATION_COMMAND(FDelayedFunctionLatentCommand([this,Fixture,B,Pawn,Shape]{
 auto& F=*Fixture;F.W->GetTimerManager().Tick(.05f);TestTrue(TEXT("Next-frame overlap armed"),B->bVolumeArmed);F.S->NotifyLevelReady();TestNull(TEXT("Initial overlap requires opt-in"),F.S->ActivePlayer.Get());
 Pawn->SetActorLocation(FVector(1000,0,0));Shape->UpdateOverlaps();TestFalse(TEXT("Physical exit"),B->PlayerInside());TestFalse(TEXT("Logical exit"),B->bInside);Pawn->SetActorLocation(FVector::ZeroVector);Shape->UpdateOverlaps();TestTrue(TEXT("Physical reentry"),B->PlayerInside());TestNotNull(TEXT("Exit then enter fires"),F.S->ActivePlayer.Get());AddInfo(B->Status);
 }));return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSceneEventDistinctBattlesTest,"Constellation.SceneDirector.EventDistinctBattles",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSceneEventDistinctBattlesTest::RunTest(const FString&)
{
 FEventFixture F;auto* Busy=F.Add(ESceneEventTrigger::Combat);Busy->CombatKey=TEXT("Busy");auto* B=F.Add(ESceneEventTrigger::Combat);F.S->Request(Busy);auto I1=FGuid::NewGuid(),I2=FGuid::NewGuid();F.S->NotifyCombatFinished(TEXT("Fight"),I1,ESceneCombatResult::Victory);F.S->NotifyCombatFinished(TEXT("Fight"),I2,ESceneCombatResult::Victory);TestEqual(TEXT("Separate battle instances retained"),F.S->PendingCount(),2);F.S->CancelActive();F.S->Tick(0);if(F.S->ActivePlayer)F.S->ActivePlayer->Tick(2);F.S->Tick(0);TestNotNull(TEXT("Second battle plays"),F.S->ActivePlayer.Get());return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSceneEventDestroyedGCTest,"Constellation.SceneDirector.EventDestroyedGC",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSceneEventDestroyedGCTest::RunTest(const FString&)
{
 FEventFixture F;auto* Busy=F.Add(ESceneEventTrigger::Combat);auto* B=F.Add(ESceneEventTrigger::Destroyed);B->Source=F.W->SpawnActor<ACameraActor>();B->Source->SetActorLocation(FVector(44,55,66));B->Origin=ESceneEventOrigin::Source;B->DispatchBeginPlay();F.S->Request(Busy);B->Source->Destroy();CollectGarbage(RF_NoFlags);F.S->CancelActive();F.S->Tick(0);if(TestNotNull(TEXT("GC does not invalidate saved destruction"),F.S->ActivePlayer.Get()))TestTrue(TEXT("Destroyed snapshot retained across GC"),F.S->ActivePlayer->OriginTransform.GetLocation().Equals(FVector(44,55,66)));return true;
}
#endif





#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSceneEventPersistenceTest,"Constellation.SceneDirector.EventPersistence",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSceneEventPersistenceTest::RunTest(const FString&)
{
 FEventFixture F;auto* B=F.Add(ESceneEventTrigger::Combat);B->bPersistVariables=true;B->Repeat=ESceneEventRepeat::OncePerSave;TestFalse(TEXT("Cannot run persistent event before storage is ready"),F.S->Request(B));int32 Saves=0;FSceneEventSaveData Saved;
 F.S->SaveHandler.BindLambda([&](const FSceneEventSaveData& D,FString&){++Saves;Saved.Merge(D);return true;});TestTrue(TEXT("Persistent event starts"),F.S->Request(B));F.S->CancelActive();TestEqual(TEXT("Cancel does not save"),Saves,0);F.S->Request(B);if(F.S->ActivePlayer){F.S->ActivePlayer->BoolValues.Add(TEXT("HasInteracted"),true);F.S->ActivePlayer->Tick(2);}TestEqual(TEXT("Natural end saves once"),Saves,1);TestTrue(TEXT("Completion durable key"),Saved.Completed.Contains(F.S->PersistentKey(B->EventId.ToString())));TestTrue(TEXT("Variable durable state"),Saved.States[F.S->PersistentKey(B->StateKey())].Bools.FindRef(TEXT("HasInteracted")));
 auto* Other=F.Add(ESceneEventTrigger::Combat);Other->Repeat=ESceneEventRepeat::OncePerSave;Saved.Completed.Add(F.S->PersistentKey(Other->EventId.ToString()));F.S->RestorePersistence(Saved);TestFalse(TEXT("Restored one-shot refuses replay"),F.S->Request(Other));
 auto* Fail=F.Add(ESceneEventTrigger::Combat);Fail->bPersistVariables=true;F.S->SaveHandler.BindLambda([](const FSceneEventSaveData&,FString& Error){Error=TEXT("Simulated disk failure");return false;});F.S->Request(Fail);if(F.S->ActivePlayer)F.S->ActivePlayer->Tick(2);TestFalse(TEXT("Save error exposed"),F.S->LastSaveError.IsEmpty());F.S->SaveHandler.BindLambda([&](const FSceneEventSaveData& D,FString&){Saved.Merge(D);return true;});TestTrue(TEXT("Pending save can retry"),F.S->RetryPendingSave());TestTrue(TEXT("Save error cleared"),F.S->LastSaveError.IsEmpty());return true;
}
#endif
