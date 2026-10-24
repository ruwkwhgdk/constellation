#if WITH_DEV_AUTOMATION_TESTS
#include "TextManagementEditing.h"
#include "Misc/AutomationTest.h"
#include "SceneDirectorSpeaker.h"
#include "Internationalization/StringTable.h"
#include "Internationalization/StringTableCore.h"
#include "Internationalization/StringTableRegistry.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Editor.h"
using namespace ConstellationText;
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTextCategoryTest,"Constellation.TextManagement.CategoryOverrides",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTextCategoryTest::RunTest(const FString&)
{
    FEntry Entry;Entry.Location.Kind=ELocationKind::DataTable;Entry.Location.Asset=FSoftObjectPath(TEXT("/Game/Constellation/Gameplay/Quests/Data/DT_Test.DT_Test"));Entry.Location.Row=TEXT("First");Entry.Origin=Entry.Location;
    const FString File=FPaths::ProjectSavedDir()/TEXT("TextManagementTests/")+FGuid::NewGuid().ToString()+TEXT(".ini");FText Message;
    TestEqual(TEXT("Quest sources are suggested as quests"),SuggestedCategory(Entry),FString(TEXT("퀘스트")));
    TestTrue(TEXT("User category persists"),SetCategory(Entry,TEXT("튜토리얼"),File,Message));
    TestEqual(TEXT("Manual classification overrides automatic suggestion"),Category(Entry,File),FString(TEXT("튜토리얼")));
    FEntry Consumer=Entry;Consumer.Location.Kind=ELocationKind::Director;
    TestEqual(TEXT("A shared origin keeps the same category"),Category(Consumer,File),FString(TEXT("튜토리얼")));
    TestTrue(TEXT("Empty category resets to automatic"),SetCategory(Entry,TEXT(""),File,Message));
    TestEqual(TEXT("Automatic category restored"),Category(Entry,File),FString(TEXT("퀘스트")));
    IFileManager::Get().Delete(*File);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTextEditTest,"Constellation.TextManagement.EditPreservesIdentity",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTextEditTest::RunTest(const FString&)
{
    auto* Table=NewObject<UDataTable>(GetTransientPackage(),NAME_None,RF_Transactional);Table->RowStruct=FDirectorSpeakerRow::StaticStruct();
    FDirectorSpeakerRow Row;Row.DisplayName=NSLOCTEXT("TextEditingTest","Name","원래 이름");Table->AddRow(TEXT("Speaker"),Row);
    FIndex Index;Index.Collect(Table);FEditSnapshot Snapshot;FText Message;
    if(!TestTrue(TEXT("Table text supports editing"),ReadEdit(*Index.Entries[0],Snapshot,Message)))return false;
    TestTrue(TEXT("Apply updates original cell"),ApplyEdit(Snapshot,TEXT("새 이름"),Message));
    auto Read=[&](){return Table->FindRow<FDirectorSpeakerRow>(TEXT("Speaker"),TEXT("Test"))->DisplayName;};
    TestEqual(TEXT("Original changed"),Read().ToString(),FString(TEXT("새 이름")));
    TestEqual(TEXT("Localization namespace retained"),FTextInspector::GetNamespace(Read()).GetValue(),FString(TEXT("TextEditingTest")));
    TestEqual(TEXT("Localization key retained"),FTextInspector::GetKey(Read()).GetValue(),FString(TEXT("Name")));
    TestFalse(TEXT("Stale edit cannot overwrite newer text"),ApplyEdit(Snapshot,TEXT("다른 이름"),Message));
    GEditor->UndoTransaction();TestEqual(TEXT("Undo restores original cell"),Read().ToString(),FString(TEXT("원래 이름")));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTextSharedEditTest,"Constellation.TextManagement.EditSharedStringTable",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTextSharedEditTest::RunTest(const FString&)
{
    auto* Strings=NewObject<UStringTable>(GetTransientPackage(),NAME_None,RF_Transactional);FStringTableRegistry::Get().RegisterStringTable(Strings->GetStringTableId(),Strings->GetMutableStringTable());
    Strings->GetMutableStringTable()->SetSourceString(TEXT("Key"),TEXT("원문"),TEXT("Keep note"));
    auto* Table=NewObject<UDataTable>();Table->RowStruct=FDirectorSpeakerRow::StaticStruct();FDirectorSpeakerRow Row;Row.DisplayName=FText::FromStringTable(Strings->GetStringTableId(),TEXT("Key"));Table->AddRow(TEXT("Row"),Row);
    FIndex Index;Index.Collect(Table);FEditSnapshot Snapshot;FText Message;
    if(TestTrue(TEXT("Linked cell edits actual String Table"),ReadEdit(*Index.Entries[0],Snapshot,Message)))
    {
        TestTrue(TEXT("Shared source update succeeds"),ApplyEdit(Snapshot,TEXT("공유 수정"),Message));
        TestEqual(TEXT("Developer notes preserved"),Strings->GetStringTable()->FindEntry(TEXT("Key"))->GetDevNotes(),FString(TEXT("Keep note")));
        TestEqual(TEXT("Source is updated"),Strings->GetStringTable()->FindEntry(TEXT("Key"))->GetSourceString(),FString(TEXT("공유 수정")));
        TestTrue(TEXT("Table still holds its String Table reference"),Table->FindRow<FDirectorSpeakerRow>(TEXT("Row"),TEXT("Test"))->DisplayName.IsFromStringTable());
    }
    FStringTableRegistry::Get().UnregisterStringTable(Strings->GetStringTableId());return true;
}
#endif
