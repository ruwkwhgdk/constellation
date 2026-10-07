#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CurrencySubsystem.h"
#include "QuestSubsystem.h"
#include "QuestDefinition.h"
#include "QuestAuditTestTypes.h"
#include "ConstellationSaveGame.h"
#include "Engine/GameInstance.h"
#include "Kismet/GameplayStatics.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FConstellationAuditPersistenceTest,
    "Constellation.Audit.PersistenceAndQuestBoundaries",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FConstellationAuditPersistenceTest::RunTest(const FString&)
{
    // Never read or write the user's gameplay slot. Each run has its own file.
    const FString Slot = TEXT("Audit_") + FGuid::NewGuid().ToString(EGuidFormats::Digits);
    UGameInstance* GI = NewObject<UGameInstance>();
    GI->AddToRoot();
    UCurrencySubsystem* Currency = NewObject<UCurrencySubsystem>(GI);
    UQuestSubsystem* Quests = NewObject<UQuestSubsystem>(GI);
    Currency->SaveSlotName = Slot;
    Quests->SaveSlotName = Slot;
    Currency->CurrentSaveGame = NewObject<UConstellationSaveGame>();
    Quests->CurrentSaveGame = NewObject<UConstellationSaveGame>();

    UQuestDefinition* Quest = NewObject<UQuestDefinition>();
    Quest->QuestID = TEXT("AuditQuest");
    Quest->ProgressSteps.SetNum(2);
    Quest->ProgressSteps[0].InnerProgressCount = 5;
    Quest->ProgressSteps[1].InnerProgressCount = 5;
    Quests->QuestDefinitions.Add(Quest->QuestID, Quest);
    TestTrue(TEXT("Unlock"), Quests->TryUnlockQuest(Quest->QuestID));
    TestTrue(TEXT("Accept"), Quests->AcceptQuest(Quest->QuestID));

    Currency->AddStarCoin(12);
    Currency->AddDummyItem(3);
    auto Load = [&]() { return Cast<UConstellationSaveGame>(UGameplayStatics::LoadGameFromSlot(Slot, 0)); };
    UConstellationSaveGame* Saved = Load();
    if (TestNotNull(TEXT("Save exists"), Saved))
    {
        TestEqual(TEXT("Coin grant persists immediately"), Saved->StarCoin, 12);
        TestEqual(TEXT("Item grant persists immediately"), Saved->DummyItemCount, 3);
    }
    Currency->MarkChestIDOpened(TEXT("AuditChest"));
    Saved = Load();
    if (TestNotNull(TEXT("Chest save remains readable"), Saved))
        TestEqual(TEXT("Currency save retains quest rows"), Saved->QuestStates.Num(), 1);

    Quests->SetQuestInnerProgress(Quest->QuestID, 2);
    Saved = Load();
    if (TestNotNull(TEXT("Quest save remains readable"), Saved))
    {
        TestEqual(TEXT("Quest save retains coins"), Saved->StarCoin, 12);
        TestEqual(TEXT("Quest save retains items"), Saved->DummyItemCount, 3);
        TestTrue(TEXT("Quest save retains opened chests"), Saved->OpenedChestIDs.Contains(TEXT("AuditChest")));
    }

    UQuestSubsystem* Reloaded = NewObject<UQuestSubsystem>(GI);
    Reloaded->SaveSlotName = Slot;
    FSubsystemCollection<UGameInstanceSubsystem> Collection;
    Reloaded->Initialize(Collection);
    TestEqual(TEXT("Inner progress survives reload"), Reloaded->GetQuestInnerProgress(Quest->QuestID), 2);

    TestTrue(TEXT("Spend succeeds"), Currency->TrySpendStarCoin(2));
    Saved = Load();
    if (TestNotNull(TEXT("Spend save remains readable"), Saved))
        TestEqual(TEXT("Spending persists immediately"), Saved->StarCoin, 10);

    Currency->AddGold(MAX_int32);
    Currency->AddGold(1);
    TestEqual(TEXT("Gold addition saturates without wrapping"), Currency->GetGold(), MAX_int32);
    Currency->AddStarCoin(MAX_int32);
    TestEqual(TEXT("Coin addition saturates without wrapping"), Currency->GetStarCoin(), MAX_int32);
    Currency->AddDummyItem(MAX_int32);
    TestEqual(TEXT("Item addition saturates without wrapping"), Currency->GetDummyItemCount(), MAX_int32);
    Quests->AddQuestProgress(Quest->QuestID, MAX_int32);
    TestEqual(TEXT("Large progress addition clamps to final step"), Quests->GetQuestProgress(Quest->QuestID), 2);
    Quests->SetQuestInnerProgress(Quest->QuestID, 1);
    Quests->AddQuestInnerProgress(Quest->QuestID, MAX_int32);
    TestEqual(TEXT("Large inner addition clamps to final unit"), Quests->GetQuestInnerProgress(Quest->QuestID), 5);

    UQuestAuditReentrantDefinition* Reentrant = NewObject<UQuestAuditReentrantDefinition>();
    Reentrant->QuestID = TEXT("AuditReentrantQuest");
    Reentrant->Subsystem = Quests;
    Reentrant->Database = NewObject<UQuestDatabase>();
    Reentrant->Database->Quests.Add(Reentrant);
    Quests->RegisterQuestDatabase(Reentrant->Database);
    TestEqual(TEXT("Unlock condition is not recursively evaluated"), Reentrant->Calls, 1);
    TestEqual(TEXT("Reentrant registration still unlocks quest"), Quests->GetQuestState(Reentrant->QuestID), EQuestState::Available);

    UGameplayStatics::DeleteGameInSlot(Slot, 0);
    GI->RemoveFromRoot();
    return true;
}
#endif
