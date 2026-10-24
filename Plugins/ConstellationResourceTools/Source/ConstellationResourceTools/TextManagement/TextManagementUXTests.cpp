#if WITH_DEV_AUTOMATION_TESTS
#include "TextManagementPresentation.h"
#include "TextManagementHistory.h"
#include "Misc/AutomationTest.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "SceneDirectorSpeaker.h"
using namespace ConstellationText;
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTextUsageGroupingTest,"Constellation.TextManagement.UX.UsageGrouping",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTextUsageGroupingTest::RunTest(const FString&)
{
    FIndex Index;
    auto Source=MakeShared<FEntry>();Source->Location.Kind=ELocationKind::DataTable;Source->Location.Asset=FSoftObjectPath(TEXT("/Game/DT.DT"));Source->Location.Row=TEXT("Hello");Source->Location.Field=TEXT("Description");Source->Origin=Source->Location;Source->Source=TEXT("같은 문구");Index.Entries.Add(Source);
    auto Use=MakeShared<FEntry>(*Source);Use->Location.Kind=ELocationKind::Director;Use->Location.Asset=FSoftObjectPath(TEXT("/Game/SceneDirector/School/DA_S0_Opening.DA_S0_Opening"));Use->Location.Event=Use->Location.Asset;Use->Location.Node=FGuid::NewGuid();Index.Entries.Add(Use);
    Index.Usages.Add({Source->Location,Use->Location,EReferenceKind::Exact,TEXT("test")});
    auto Other=MakeShared<FEntry>(*Source);Other->Location.Row=TEXT("Different");Other->Origin=Other->Location;Index.Entries.Add(Other);
    FLocation Dynamic=Use->Location;Dynamic.Asset=FSoftObjectPath(TEXT("/Game/BP_Dynamic.BP_Dynamic"));
    FLocation Whole=Source->Location;Whole.Row=NAME_None;Whole.Field.Reset();Index.Usages.Add({Whole,Dynamic,EReferenceKind::Dynamic,TEXT("test")});
    const auto Items=BuildTextItems(Index);
    TestEqual(TEXT("Source and its consumer merge, equal text with different source remains separate"),Items.Num(),2);
    auto Item=Items.FindByPredicate([](const TSharedPtr<FTextItem>& I){return I->Key==TEXT("Hello");});
    if(TestTrue(TEXT("Row key has its own display field"),Item!=nullptr))
    {
        TestTrue(TEXT("Exact S0 use is navigable as a usage group"),(*Item)->Groups.Contains(TEXT("폐교 (AbandonedSchool)/S0")));
        TestFalse(TEXT("Dynamic table access does not prove this row belongs to that consumer"),(*Item)->Groups.Contains(UsageGroup(Dynamic)));
    }
    const auto Unknown=Items.FindByPredicate([](const TSharedPtr<FTextItem>& I){return I->Key==TEXT("Different");});
    TestTrue(TEXT("Dynamic-only row remains usage-unknown"),Unknown&&(*Unknown)->Groups.Contains(TEXT("사용처 미확인")));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTextHistoryWorkflowTest,"Constellation.TextManagement.UX.HistoryAndRetry",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTextHistoryWorkflowTest::RunTest(const FString&)
{
    const FString Directory=FPaths::ProjectSavedDir()/TEXT("TextManagementTests")/FGuid::NewGuid().ToString();
    auto* Table=NewObject<UDataTable>(GetTransientPackage(),NAME_None,RF_Transactional);Table->RowStruct=FDirectorSpeakerRow::StaticStruct();FDirectorSpeakerRow Row;Row.DisplayName=FText::FromString(TEXT("처음"));Table->AddRow(TEXT("Row"),Row);
    FIndex Index;Index.Collect(Table);FTextDraft Draft;FText Message;
    if(!ReadEdit(*Index.Entries[0],Draft.Base,Message))return false;Draft.Text=TEXT("수정");
    TestFalse(TEXT("Cancelled asset save does not claim success"),CommitTextDraft(Draft,Directory,Message,[](const FLocation&,FText&){return false;}));
    TestTrue(TEXT("Draft remains retryable after in-memory apply"),Draft.IsDirty());
    TestEqual(TEXT("Applied source becomes retry snapshot"),Draft.Base.Source,FString(TEXT("수정")));
    TestTrue(TEXT("Retry saves the same revision"),CommitTextDraft(Draft,Directory,Message,[](const FLocation&,FText&){return true;}));
    auto History=ReadTextHistory(Directory,Draft.Base.Target.Id());
    if(TestEqual(TEXT("Retry does not duplicate revision"),History.Num(),1))
    {
        TestEqual(TEXT("Original value survives failed save retry"),History[0].Before,FString(TEXT("처음")));
        TestEqual(TEXT("Only completed save is marked saved"),History[0].State,FString(TEXT("Saved")));
        TestTrue(TEXT("Restore stages prior value"),StageTextRestore(Draft,History[0],Message));
        TestEqual(TEXT("Restored text"),Draft.Text,FString(TEXT("처음")));
        TestTrue(TEXT("Restore uses the normal save flow"),CommitTextDraft(Draft,Directory,Message,[](const FLocation&,FText&){return true;}));
        TestEqual(TEXT("Restore adds a new revision"),ReadTextHistory(Directory,Draft.Base.Target.Id()).Num(),2);
        TestTrue(TEXT("Saved after-version can also be restored"),StageTextRestore(Draft,History[0],Message,false));
        TestEqual(TEXT("After-version is distinct from before-version"),Draft.Text,FString(TEXT("수정")));
        TestTrue(TEXT("After-version restore saves"),CommitTextDraft(Draft,Directory,Message,[](const FLocation&,FText&){return true;}));
        Draft.Text=TEXT("  첫째 줄\n\"둘째 줄\" \\path\t끝  ");
        const FString Multiline=Draft.Text;
        TestTrue(TEXT("Multiline revision saves"),CommitTextDraft(Draft,Directory,Message,[](const FLocation&,FText&){return true;}));
        auto MultilineHistory=ReadTextHistory(Directory,Draft.Base.Target.Id());
        TestTrue(TEXT("History preserves whitespace, quotes and newlines"),MultilineHistory.ContainsByPredicate([&](const FTextRevision& R){return R.After==Multiline;}));
        Row.DisplayName=FText::FromString(TEXT("외부 수정"));Table->AddRow(TEXT("Row"),Row);
        TestFalse(TEXT("Restore rejects external changes"),StageTextRestore(Draft,History[0],Message));
    }
    // Remove only files created by this fixture; never touch compiler working files.
    TArray<FString> Files;IFileManager::Get().FindFiles(Files,*(Directory/TEXT("*.ini")),true,false);
    for(const FString& File:Files)IFileManager::Get().Delete(*(Directory/File));IFileManager::Get().DeleteDirectory(*Directory,false,false);
    return true;
}
#endif
