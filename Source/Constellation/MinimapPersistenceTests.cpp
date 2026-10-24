#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "MinimapExplorationSubsystem.h"
#include "ConstellationSaveGame.h"
#include "SceneGameSubsystem.h"
#include "Engine/GameInstance.h"
#include "Kismet/GameplayStatics.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMinimapPersistenceTest,"Constellation.Minimap.Persistence",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMinimapPersistenceTest::RunTest(const FString&)
{
    const FString Slot=TEXT("MinimapTest_")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    auto* GI=NewObject<UGameInstance>(); GI->AddToRoot();
    auto* Exploration=NewObject<UMinimapExplorationSubsystem>(GI);
    Exploration->SetSaveSlotForTesting(Slot);
    FSubsystemCollection<UGameInstanceSubsystem> Collection;
    Exploration->Initialize(Collection);
    const FName Region(TEXT("School")), Floor(TEXT("Ground"));
    Exploration->RevealCells(Region,Floor,50,{FIntPoint(-2,3),FIntPoint(1,1)});
    TestTrue(TEXT("Current exploration exists before disk save"),Exploration->IsRevealed(Region,Floor,50,FIntPoint(-2,3)));
    TestFalse(TEXT("Other floors stay hidden"),Exploration->IsRevealed(Region,TEXT("Upper"),50,FIntPoint(-2,3)));
    TestFalse(TEXT("Other cell sizes do not reinterpret discovery"),Exploration->IsRevealed(Region,Floor,100,FIntPoint(-2,3)));
    TestFalse(TEXT("Revealing cells does not write every update"),UGameplayStatics::DoesSaveGameExist(Slot,0));

    auto* Seed=NewObject<UConstellationSaveGame>(); Seed->StarCoin=37; Seed->DummyItemCount=4;
    Seed->OpenedChestIDs.Add(TEXT("ChestA")); Seed->CollectedStarCoinIDs.Add(TEXT("CoinA"));
    FQuestSaveEntry Quest; Quest.QuestID=TEXT("QuestA"); Quest.Progress=2; Seed->QuestStates.Add(Quest);
    Seed->SceneEvents.Completed.Add(TEXT("SceneA"));
    FMinimapExploredFloor Old; Old.RegionId=Region; Old.FloorId=Floor; Old.CellSize=50; Old.Cells.Add(FIntPoint(7,7));
    Seed->Minimap.Floors.Add(Old);
    TestTrue(TEXT("Seed isolated shared save"),UGameplayStatics::SaveGameToSlot(Seed,Slot,0));
    TestTrue(TEXT("Flush merges pending discovery into latest shared save"),Exploration->Flush());
    auto* PartialReload=NewObject<UMinimapExplorationSubsystem>(GI); PartialReload->SetSaveSlotForTesting(Slot); PartialReload->Initialize(Collection);
    TestTrue(TEXT("Fresh session restores partial discovery"),PartialReload->IsRevealed(Region,Floor,50,FIntPoint(-2,3)));
    TestTrue(TEXT("Fresh session restores preexisting disk discovery"),PartialReload->IsRevealed(Region,Floor,50,FIntPoint(7,7)));
    TestFalse(TEXT("Partial restore does not expose unvisited cells"),PartialReload->IsRevealed(Region,Floor,50,FIntPoint(8,8)));
    auto Load=[&](){return Cast<UConstellationSaveGame>(UGameplayStatics::LoadGameFromSlot(Slot,0));};
    auto* Saved=Load();
    if(TestNotNull(TEXT("Merged save readable"),Saved))
    {
        TestEqual(TEXT("Currency preserved"),Saved->StarCoin,37);
        TestEqual(TEXT("Items preserved"),Saved->DummyItemCount,4);
        TestTrue(TEXT("Chest preserved"),Saved->OpenedChestIDs.Contains(TEXT("ChestA")));
        TestTrue(TEXT("Pickup preserved"),Saved->CollectedStarCoinIDs.Contains(TEXT("CoinA")));
        TestEqual(TEXT("Quest preserved"),Saved->QuestStates.Num(),1);
        TestTrue(TEXT("Scene preserved"),Saved->SceneEvents.Completed.Contains(TEXT("SceneA")));
        if(TestEqual(TEXT("One floor record"),Saved->Minimap.Floors.Num(),1))TestEqual(TEXT("Old and new cells union"),Saved->Minimap.Floors[0].Cells.Num(),3);
        Exploration->MergeIntoSave(Saved); Exploration->MergeIntoSave(Saved);
        if(Saved->Minimap.Floors.Num()==1)TestEqual(TEXT("Repeated merges idempotent"),Saved->Minimap.Floors[0].Cells.Num(),3);
    }
    // An older checkpoint object may be read, but merging it must not replace live discovery.
    Exploration->MergeIntoSave(Seed);
    TestTrue(TEXT("Older checkpoint cannot roll live discovery back"),Exploration->IsRevealed(Region,Floor,50,FIntPoint(1,1)));
    Exploration->RevealCells(Region,Floor,50,{FIntPoint(9,9)});
    FSceneEventSaveData Delta; Delta.Completed.Add(TEXT("SceneB")); FString Error;
    TestTrue(TEXT("Existing scene save joins pending discovery"),USceneGameSubsystem::MergeSave(Slot,Delta,Error,Exploration));
    Saved=Load();
    if(TestNotNull(TEXT("Scene merge readable"),Saved))
    {
        if(TestEqual(TEXT("Scene retains floor record"),Saved->Minimap.Floors.Num(),1))TestEqual(TEXT("Scene save includes pending cell"),Saved->Minimap.Floors[0].Cells.Num(),4);
        TestTrue(TEXT("Previous scene retained"),Saved->SceneEvents.Completed.Contains(TEXT("SceneA")));
        TestTrue(TEXT("New scene retained"),Saved->SceneEvents.Completed.Contains(TEXT("SceneB")));
    }
    Exploration->UnlockRegion(Region); Exploration->UnlockRegion(Region);
    TestTrue(TEXT("Full region includes previously hidden floors"),Exploration->IsRevealed(Region,TEXT("Upper"),50,FIntPoint(200,200)));
    TestFalse(TEXT("Full region does not unlock another region"),Exploration->IsRegionUnlocked(TEXT("Other")));
    TestTrue(TEXT("Unlock persists"),Exploration->Flush());
    auto* Reloaded=NewObject<UMinimapExplorationSubsystem>(GI); Reloaded->SetSaveSlotForTesting(Slot); Reloaded->Initialize(Collection);
    TestTrue(TEXT("Fresh session restores full unlock"),Reloaded->IsRegionUnlocked(Region));
    Saved=Load();
    if(Saved)TestEqual(TEXT("Repeated unlock stores one region"),Saved->Minimap.UnlockedRegions.Num(),1);
    Exploration->Deinitialize(); Reloaded->Deinitialize(); PartialReload->Deinitialize();
    UGameplayStatics::DeleteGameInSlot(Slot,0); GI->RemoveFromRoot();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMinimapSavePolicyTest,"Constellation.Minimap.SavePolicy",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMinimapSavePolicyTest::RunTest(const FString&)
{
    const FString Slot=TEXT("MinimapPolicy_")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    const FString OtherSlot=Slot+TEXT("_Other");
    auto* GI=NewObject<UGameInstance>(); GI->AddToRoot();
    auto* Exploration=NewObject<UMinimapExplorationSubsystem>(GI); Exploration->SetSaveSlotForTesting(Slot);
    FSubsystemCollection<UGameInstanceSubsystem> Collection; Exploration->Initialize(Collection);
    Exploration->RevealCells(TEXT("School"),TEXT("Ground"),50,{FIntPoint(1,2)});
    Exploration->TickFlush(14.f);
    TestFalse(TEXT("Dirty state waits for batch interval"),UGameplayStatics::DoesSaveGameExist(Slot,0));
    Exploration->TickFlush(1.f);
    TestTrue(TEXT("Dirty state flushes at interval"),UGameplayStatics::DoesSaveGameExist(Slot,0));
    FSceneEventSaveData Delta; Delta.Completed.Add(TEXT("OtherScene")); FString Error;
    TestTrue(TEXT("Separate scene slot still saves"),USceneGameSubsystem::MergeSave(OtherSlot,Delta,Error,Exploration));
    auto* Other=Cast<UConstellationSaveGame>(UGameplayStatics::LoadGameFromSlot(OtherSlot,0));
    if(TestNotNull(TEXT("Separate slot readable"),Other))TestTrue(TEXT("Separate slot gets no exploration from another session slot"),Other->Minimap.Floors.IsEmpty());
    auto* Future=NewObject<UConstellationSaveGame>(); Future->Minimap.Version=99; Future->StarCoin=72;
    TestTrue(TEXT("Seed unsupported version in isolated slot"),UGameplayStatics::SaveGameToSlot(Future,Slot,0));
    Exploration->RevealCells(TEXT("School"),TEXT("Ground"),50,{FIntPoint(3,4)});
    AddExpectedError(TEXT("Minimap save aborted:"),EAutomationExpectedErrorFlags::Contains,1);
    TestFalse(TEXT("Unsupported save is not overwritten"),Exploration->Flush());
    auto* Preserved=Cast<UConstellationSaveGame>(UGameplayStatics::LoadGameFromSlot(Slot,0));
    if(TestNotNull(TEXT("Unsupported save retained"),Preserved))
    {
        TestEqual(TEXT("Future version retained"),Preserved->Minimap.Version,99);
        TestEqual(TEXT("Other future save fields retained"),Preserved->StarCoin,72);
    }
    // Remove only this test's incompatible file so teardown can prove retained dirty data is retried.
    UGameplayStatics::DeleteGameInSlot(Slot,0);
    Exploration->Deinitialize();
    auto* Final=Cast<UConstellationSaveGame>(UGameplayStatics::LoadGameFromSlot(Slot,0));
    if(TestNotNull(TEXT("Teardown retries dirty save"),Final) && TestEqual(TEXT("Teardown retains floor"),Final->Minimap.Floors.Num(),1))TestEqual(TEXT("Failed flush retained both explored cells"),Final->Minimap.Floors[0].Cells.Num(),2);
    UGameplayStatics::DeleteGameInSlot(Slot,0); UGameplayStatics::DeleteGameInSlot(OtherSlot,0); GI->RemoveFromRoot();
    return true;
}
#endif
