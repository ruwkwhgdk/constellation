#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "ConstellationSaveGame.h"
#include "UObject/UnrealType.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSceneGameContractTest,"Constellation.SceneIntegration.Contract",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSceneGameContractTest::RunTest(const FString&)
{
 TestNotNull(TEXT("Scene event state is part of shared save"),FindFProperty<FProperty>(UConstellationSaveGame::StaticClass(),TEXT("SceneEvents")));
 TestNotNull(TEXT("Project scene bridge exists"),FindObject<UClass>(nullptr,TEXT("/Script/Constellation.SceneGameSubsystem")));
 return true;
}
#endif
#if WITH_DEV_AUTOMATION_TESTS
#include "SceneGameSubsystem.h"
#include "Kismet/GameplayStatics.h"
#include "CurrencySubsystem.h"
#include "QuestSubsystem.h"
#include "Engine/GameInstance.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSceneSharedSaveTest,"Constellation.SceneIntegration.SharedSave",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSceneSharedSaveTest::RunTest(const FString&)
{
 const FString Slot=TEXT("SceneEventTest_")+FGuid::NewGuid().ToString(EGuidFormats::Digits);auto* Initial=NewObject<UConstellationSaveGame>();Initial->StarCoin=37;Initial->OpenedChestIDs.Add(TEXT("ChestA"));TestTrue(TEXT("Seed isolated save"),UGameplayStatics::SaveGameToSlot(Initial,Slot,0));
 FSceneEventSaveData Delta;FSceneEventSavedState State;State.AssetPath=TEXT("/Game/SceneDirector/Statue/DA_StatueInteraction.DA_StatueInteraction");State.Bools.Add(TEXT("HasInteracted"),true);State.Ints.Add(TEXT("Visits"),2);Delta.States.Add(TEXT("/Game/Test:Statue"),State);Delta.Completed.Add(TEXT("/Game/Test:Once"));FString Error;
 TestTrue(TEXT("Merge cinematic state"),USceneGameSubsystem::MergeSave(Slot,Delta,Error));auto* Saved=Cast<UConstellationSaveGame>(UGameplayStatics::LoadGameFromSlot(Slot,0));if(TestNotNull(TEXT("Read merged save"),Saved)){TestEqual(TEXT("Currency preserved"),Saved->StarCoin,37);TestTrue(TEXT("Chest preserved"),Saved->OpenedChestIDs.Contains(TEXT("ChestA")));TestTrue(TEXT("Bool persisted"),Saved->SceneEvents.States[TEXT("/Game/Test:Statue")].Bools[TEXT("HasInteracted")]);TestEqual(TEXT("Int persisted"),Saved->SceneEvents.States[TEXT("/Game/Test:Statue")].Ints[TEXT("Visits")],2);TestTrue(TEXT("Once persisted"),Saved->SceneEvents.Completed.Contains(TEXT("/Game/Test:Once")));}
 TestFalse(TEXT("Future save format not overwritten"),[&]{Delta.Version=99;return USceneGameSubsystem::MergeSave(Slot,Delta,Error);}());
 UGameplayStatics::DeleteGameInSlot(Slot,0);return true;
}
#endif
#if WITH_DEV_AUTOMATION_TESTS
#include "SceneGameTestTypes.h"
#include "SceneEventSubsystem.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorPlayer.h"
#include "LevelSequence.h"
#include "LevelSequencePlayer.h"
#include "LevelSequenceActor.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "UObject/StructOnScope.h"
#endif
#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSceneInteractionOwnershipTest,"Constellation.SceneIntegration.InteractionOwnership",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSceneInteractionOwnershipTest::RunTest(const FString&)
{
 auto* SourceClass=LoadClass<AActor>(nullptr,TEXT("/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object_Sequence.BP_Star_Object_Sequence_C"));auto* ManagerClass=LoadClass<AActor>(nullptr,TEXT("/Game/Constellation/Gameplay/Sequences/BP_SequenceManager.BP_SequenceManager_C"));if(!SourceClass||!ManagerClass)return false;
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());W->SetGameInstance(NewObject<UGameInstance>(W));auto* PC=W->SpawnActor<APlayerController>();auto* Pawn=W->SpawnActor<APawn>();PC->Possess(Pawn);auto* Manager=W->SpawnActor<AActor>(ManagerClass);
 auto* Source=NewObject<ULevelSequence>();Source->Initialize();auto* A=NewObject<USceneDirectorAsset>();for(auto Type:{EDirectorNodeType::Start,EDirectorNodeType::Wait,EDirectorNodeType::GameplayReturn,EDirectorNodeType::End}){FDirectorStep S;S.Type=Type;S.Duration=1;A->Steps.Add(S);}for(int I=0;I<3;++I)A->Steps[I].NextNodes={A->Steps[I+1].Id};FString Error;FSceneDirectorCompiler::Compile(*A,Error);
 auto* B=W->SpawnActor<ASceneEventBinding>();B->Trigger=ESceneEventTrigger::LegacySequence;B->OriginalSequence=Source;B->Director=A;auto* E=W->GetSubsystem<USceneEventSubsystem>();E->Register(B);
 auto MakeSource=[&](){auto* Actor=W->SpawnActor<AActor>(SourceClass);FindFProperty<FObjectPropertyBase>(SourceClass,TEXT("TargetLevelSequence"))->SetObjectPropertyValue_InContainer(Actor,Source);FindFProperty<FBoolProperty>(SourceClass,TEXT("IsHiddenAtSequenceStart"))->SetPropertyValue_InContainer(Actor,true);Actor->SetActorHiddenInGame(false);return Actor;};auto* First=MakeSource();auto* Second=MakeSource();
 First->ProcessEvent(First->FindFunction(TEXT("Event After UI")),nullptr);TestNotNull(TEXT("Real source starts native request before legacy effects"),E->ActivePlayer.Get());TestTrue(TEXT("Accepted source hides"),First->IsHidden());auto* Running=E->ActivePlayer.Get();
 Second->ProcessEvent(Second->FindFunction(TEXT("Event After UI")),nullptr);TestEqual(TEXT("Rejected source does not replace running scene"),E->ActivePlayer.Get(),Running);TestFalse(TEXT("Rejected source remains visible"),Second->IsHidden());
 for(FName Name:{FName(TEXT("OnBlendCameraStart")),FName(TEXT("OnSequenceFinished"))}){auto* D=FindFProperty<FMulticastDelegateProperty>(ManagerClass,Name);FMulticastScriptDelegate Copy;D->CopyCompleteValue(&Copy,D->ContainerPtrToValuePtr<void>(Manager));TestFalse(TEXT("No rejected source callbacks on shared manager"),Copy.IsBound());}
 E->CancelActive();TestFalse(TEXT("Cancel restores accepted pickup"),First->IsHidden());
 auto* Interact=Second->FindFunction(TEXT("Interact"));FStructOnScope Args(Interact);FindFProperty<FObjectPropertyBase>(Interact,TEXT("Interactor"))->SetObjectPropertyValue_InContainer(Args.GetStructMemory(),Pawn);Second->ProcessEvent(Interact,Args.GetStructMemory());TestNotNull(TEXT("Retry resumes without replaying consumed item UI"),E->ActivePlayer.Get());E->CancelActive();TestFalse(TEXT("Retry cancellation restores source"),Second->IsHidden());
 auto* Observer=NewObject<USceneGameTestCallbacks>(Manager);First->ProcessEvent(First->FindFunction(TEXT("Event After UI")),nullptr);if(auto* R=E->ActivePlayer.Get()){R->OnGameplayReturned.AddDynamic(Observer,&USceneGameTestCallbacks::OnReturned);R->OnDirectorStopped.AddDynamic(Observer,&USceneGameTestCallbacks::OnStopped);for(int I=0;I<100&&E->ActivePlayer;++I)R->Tick(.1f);}TestEqual(TEXT("Return callback once"),Observer->Returned,1);TestEqual(TEXT("Completion callback once"),Observer->Finished,1);TestTrue(TEXT("Original source completion event runs"),First->IsActorBeingDestroyed());
 GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
#endif
