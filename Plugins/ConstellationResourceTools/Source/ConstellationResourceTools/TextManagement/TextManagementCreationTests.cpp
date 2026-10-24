#if WITH_DEV_AUTOMATION_TESTS
#include "TextManagementCreation.h"
#include "SceneDirectorSpeaker.h"
#include "Misc/AutomationTest.h"
using namespace ConstellationText;
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDialogueCreationTest,"Constellation.TextManagement.Creation",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDialogueCreationTest::RunTest(const FString&)
{
    auto* Table=NewObject<UDataTable>(GetTransientPackage(),NAME_None,RF_Transactional);
    Table->RowStruct=FDirectorSpeakerRow::StaticStruct();FTextDraft Draft;FText Message;
    TestFalse(TEXT("Invalid field cannot add a row"),CreateDialogueDraft(Table,TEXT("New"),TEXT("Missing"),TEXT("Hello"),Draft,Message));
    TestEqual(TEXT("Validation does not mutate"),Table->GetRowMap().Num(),0);
    TestTrue(TEXT("Create empty row and content draft"),CreateDialogueDraft(Table,TEXT("New"),TEXT("DisplayName"),TEXT("Hello"),Draft,Message));
    TestTrue(TEXT("New content awaits normal save/history"),Draft.IsDirty());
    TestEqual(TEXT("Content preserved"),Draft.Text,FString(TEXT("Hello")));
    TestFalse(TEXT("FName case-insensitive duplicate rejected"),CreateDialogueDraft(Table,TEXT("new"),TEXT("DisplayName"),TEXT("Overwrite"),Draft,Message));
    TestEqual(TEXT("Existing row never overwritten"),Table->GetRowMap().Num(),1);
    TestFalse(TEXT("None key rejected"),CreateDialogueDraft(Table,TEXT("None"),TEXT("DisplayName"),TEXT("Hello"),Draft,Message));
    TestFalse(TEXT("Empty content rejected"),CreateDialogueDraft(Table,TEXT("Other"),TEXT("DisplayName"),TEXT("  "),Draft,Message));
    TestTrue(TEXT("Draft applies through existing identity-preserving editor"),ApplyEdit(Draft.Base,Draft.Text,Message));
    FEntry Entry;Entry.Origin=Draft.Base.Target;FEditSnapshot Snapshot;
    TestTrue(TEXT("Created row resolves"),ReadEdit(Entry,Snapshot,Message));
    TestEqual(TEXT("Applied content"),Snapshot.Source,FString(TEXT("Hello")));
    FTextDraft Inserted;
    TestTrue(TEXT("Insert independent key without renumbering"),CreateDialogueDraft(Table,TEXT("Dialogue_Independent"),TEXT("DisplayName"),TEXT("Inserted line"),Inserted,Message));
    FEditSnapshot Unchanged;
    TestTrue(TEXT("Old reference still resolves after insertion"),ReadEdit(Entry,Unchanged,Message));
    TestEqual(TEXT("Existing content survives insertion"),Unchanged.Source,Snapshot.Source);
    TestTrue(TEXT("Existing localization identity survives insertion"),Unchanged.Original.IdenticalTo(Snapshot.Original));
    return true;
}
#endif
