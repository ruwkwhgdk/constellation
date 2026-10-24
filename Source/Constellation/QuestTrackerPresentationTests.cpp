#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "QuestTrackerPresentation.h"
#include "QuestSubsystem.h"
#include "QuestDefinition.h"
#include "Engine/GameInstance.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FQuestTrackerQuantityTest,"Constellation.Quest.TrackerQuantity",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FQuestTrackerQuantityTest::RunTest(const FString&)
{
 FQuestDisplayInfo Info;
 Info.State=EQuestState::Progressed;Info.bVisible=true;
 Info.Progress=2;Info.MaxProgress=9;Info.InnerProgress=1;Info.MaxInnerProgress=3;
 TestTrue(TEXT("Sequential sub-objectives and overall steps never become a quantity"),QuestTrackerPresentation::QuantityText(Info).IsEmpty());
 Info.bShowObjectiveQuantity=true;
 TestEqual(TEXT("Explicit quantity uses current objective units only"),QuestTrackerPresentation::QuantityText(Info).ToString(),FString(TEXT("1/3")));
 Info.InnerProgress=0;
 TestEqual(TEXT("Quantity starts at zero, not one-based stage progress"),QuestTrackerPresentation::QuantityText(Info).ToString(),FString(TEXT("0/3")));
 Info.InnerProgress=8;
 TestEqual(TEXT("Invalid excess count is clamped"),QuestTrackerPresentation::QuantityText(Info).ToString(),FString(TEXT("3/3")));
 Info.bVisible=false;
 TestTrue(TEXT("Hidden quest has no count"),QuestTrackerPresentation::QuantityText(Info).IsEmpty());
 Info.bVisible=true;Info.State=EQuestState::Complete;
 TestTrue(TEXT("Completed quest has no ongoing count"),QuestTrackerPresentation::QuantityText(Info).IsEmpty());
 Info.State=EQuestState::Progressed;Info.MaxInnerProgress=0;
 TestTrue(TEXT("Unconfigured denominator is hidden"),QuestTrackerPresentation::QuantityText(Info).IsEmpty());
 return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FQuestTrackerDisplayInfoTest,"Constellation.Quest.TrackerDisplayInfo",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FQuestTrackerDisplayInfoTest::RunTest(const FString&)
{
 // Populate a transient catalog/state directly: this test must never load or write player saves.
 UGameInstance* GI=NewObject<UGameInstance>();
 UQuestSubsystem* Sub=NewObject<UQuestSubsystem>(GI);
 UQuestDefinition* Quest=NewObject<UQuestDefinition>(Sub);
 Quest->QuestID=TEXT("TrackerQuantityTest");Quest->Title=FText::FromString(TEXT("actual authored title"));
 Quest->Objective={FText::FromString(TEXT("sequential objective")),FText::FromString(TEXT("quantity objective"))};
 Quest->ProgressSteps.SetNum(2);
 for(auto& Step:Quest->ProgressSteps)Step.InnerProgressCount=3;
 Quest->ProgressSteps[1].bShowObjectiveQuantity=true;
 Sub->QuestDefinitions.Add(Quest->QuestID,Quest);
 FQuestRuntimeState& State=Sub->RuntimeStates.Add(Quest->QuestID);
 State.State=EQuestState::Progressed;State.Progress=1;State.InnerProgress=1;
 Sub->TrackedQuestID=Quest->QuestID;
 auto Info=Sub->GetTrackedQuestDisplayInfo();
 TestFalse(TEXT("Existing sequential definition opts out"),Info.bShowObjectiveQuantity);
 TestTrue(TEXT("Existing title preserved"),Info.Title.EqualTo(Quest->Title));
 State.Progress=2;Info=Sub->GetTrackedQuestDisplayInfo();
 TestTrue(TEXT("Current step's explicit count intent reaches display snapshot"),Info.bShowObjectiveQuantity);
 TestTrue(TEXT("Current objective remains authoritative"),Info.CurrentObjectiveText.EqualTo(Quest->Objective[1]));
 TestEqual(TEXT("Tracker renders objective count, not overall stage 2/2"),QuestTrackerPresentation::QuantityText(Info).ToString(),FString(TEXT("1/3")));
 State.State=EQuestState::Complete;Info=Sub->GetTrackedQuestDisplayInfo();
 TestFalse(TEXT("Completed display does not retain quantity intent"),Info.bShowObjectiveQuantity);
 Sub->TrackedQuestID=NAME_None;
 TestFalse(TEXT("No tracked quest remains hidden"),Sub->GetTrackedQuestDisplayInfo().bVisible);
 return true;
}
#endif
