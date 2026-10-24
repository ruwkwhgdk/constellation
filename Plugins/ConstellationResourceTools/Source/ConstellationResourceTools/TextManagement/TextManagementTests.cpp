#if WITH_DEV_AUTOMATION_TESTS
#include "TextManagementIndex.h"
#include "Misc/AutomationTest.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorSpeaker.h"
#include "SceneDirectorNavigation.h"
#include "Internationalization/StringTable.h"
#include "Internationalization/StringTableCore.h"
#include "Internationalization/StringTableRegistry.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_GetDataTableRow.h"
#include "K2Node_CallFunction.h"
#include "Kismet/KismetTextLibrary.h"
#include "Framework/Docking/TabManager.h"
#include "Widgets/Docking/SDockTab.h"
#include "Editor.h"
#include "Subsystems/AssetEditorSubsystem.h"

using namespace ConstellationText;
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTextManagementSourcesTest,"Constellation.TextManagement.Sources",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTextManagementSourcesTest::RunTest(const FString&)
{
    auto* Table=NewObject<UDataTable>();Table->RowStruct=FDirectorSpeakerRow::StaticStruct();
    FDirectorSpeakerRow Row;Row.DisplayName=NSLOCTEXT("TextManagementTest","Speaker","같은 문구");
    Table->AddRow(TEXT("First"),Row);Table->AddRow(TEXT("Second"),Row);
    FIndex Index;Index.Collect(Table);
    TestEqual(TEXT("Two authored rows remain separate even with identical FText identity"),Index.Entries.Num(),2);
    TestTrue(TEXT("Collector preserves original FText identity"),Table->FindRow<FDirectorSpeakerRow>(TEXT("First"),TEXT("test"))->DisplayName.IdenticalTo(Row.DisplayName));
    auto* Director=NewObject<USceneDirectorAsset>();FDirectorStep Step;Step.Type=EDirectorNodeType::Dialogue;
    Step.DialogueText=FText::FromString(TEXT("Old direct value"));Step.DialogueRow.DataTable=Table;Step.DialogueRow.RowName=TEXT("First");Director->Steps.Add(Step);
    Index.Collect(Director);
    TestTrue(TEXT("Row-backed dialogue has an exact reference"),Index.Usages.ContainsByPredicate([](const FUsage& U){return U.Kind==EReferenceKind::Exact&&U.Source.Row==TEXT("First");}));
    FIndex Broken;Director->Steps[0].DialogueRow.RowName=TEXT("Missing");Broken.Collect(Director);
    TestTrue(TEXT("Broken reference is reported instead of silently using direct text"),Broken.Usages.ContainsByPredicate([](const FUsage& U){return U.Kind==EReferenceKind::Broken;}));
    TestFalse(TEXT("Old direct text is not advertised as active"),Broken.Entries.ContainsByPredicate([](const TSharedPtr<FEntry>& E){return E->Source==TEXT("Old direct value")&&!E->bShadowed;}));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTextManagementBlueprintTest,"Constellation.TextManagement.DynamicBlueprint",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTextManagementBlueprintTest::RunTest(const FString&)
{
    auto* Table=NewObject<UDataTable>();Table->RowStruct=FDirectorSpeakerRow::StaticStruct();FDirectorSpeakerRow Row;Row.DisplayName=FText::FromString(TEXT("지역 이름"));Table->AddRow(TEXT("School"),Row);
    auto* BP=NewObject<UBlueprint>();auto* Graph=NewObject<UEdGraph>(BP);Graph->Schema=UEdGraphSchema_K2::StaticClass();BP->FunctionGraphs.Add(Graph);
    auto* Node=NewObject<UK2Node_GetDataTableRow>(Graph);Graph->Nodes.Add(Node);Node->CreateNewGuid();Node->AllocateDefaultPins();
    Node->GetDataTablePin()->DefaultObject=Table;Node->GetRowNamePin()->DefaultValue=TEXT("School");
    auto* Producer=NewObject<UEdGraphNode>(Graph);Graph->Nodes.Add(Producer);auto* Output=Producer->CreatePin(EGPD_Output,TEXT("name"),TEXT("Result"));Node->GetRowNamePin()->MakeLinkTo(Output);
    FIndex Dynamic;Dynamic.Collect(Table);Dynamic.Collect(BP);
    TestTrue(TEXT("Linked row pin is dynamic, even if a valid default remains"),Dynamic.Usages.ContainsByPredicate([](const FUsage& U){return U.Kind==EReferenceKind::Dynamic;}));
    TestFalse(TEXT("Linked row pin does not prove School is used"),Dynamic.Usages.ContainsByPredicate([](const FUsage& U){return U.Kind==EReferenceKind::Exact;}));
    Node->GetRowNamePin()->BreakAllPinLinks();FIndex Exact;Exact.Collect(BP);
    TestTrue(TEXT("Unlinked constant row identifies exact usage"),Exact.Usages.ContainsByPredicate([](const FUsage& U){return U.Kind==EReferenceKind::Exact&&U.Source.Row==TEXT("School");}));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTextManagementChainTest,"Constellation.TextManagement.StringTableChain",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTextManagementChainTest::RunTest(const FString&)
{
    auto* Strings=NewObject<UStringTable>();FStringTableRegistry::Get().RegisterStringTable(Strings->GetStringTableId(),Strings->GetMutableStringTable());
    Strings->GetMutableStringTable()->SetSourceString(TEXT("Greeting"),TEXT("안녕 작은 별"),TEXT(""));
    auto* Table=NewObject<UDataTable>();Table->RowStruct=FDirectorSpeakerRow::StaticStruct();FDirectorSpeakerRow Row;Row.DisplayName=FText::FromStringTable(Strings->GetStringTableId(),TEXT("Greeting"));Table->AddRow(TEXT("Hello"),Row);
    auto* Director=NewObject<USceneDirectorAsset>();FDirectorStep Step;Step.Type=EDirectorNodeType::Dialogue;Step.DialogueRow.DataTable=Table;Step.DialogueRow.RowName=TEXT("Hello");Director->Steps.Add(Step);
    FIndex Index;Index.Collect(Strings);Index.Collect(Table);Index.Collect(Director);
    const auto* Cell=Index.Entries.FindByPredicate([](const TSharedPtr<FEntry>& E){return E->Location.Kind==ELocationKind::DataTable;});
    TestTrue(TEXT("Table cell opens actual String Table origin"),Cell&&(*Cell)->Origin.Key==TEXT("Greeting")&&(*Cell)->Origin.Kind==ELocationKind::StringTable);
    const auto* Source=Index.Entries.FindByPredicate([](const TSharedPtr<FEntry>& E){return E->Location.Kind==ELocationKind::StringTable;});
    TestTrue(TEXT("String Table usage chain reaches the Director node"),Source&&Index.FindUsages(**Source).ContainsByPredicate([](const FUsage& U){return U.Consumer.Kind==ELocationKind::Director;}));
    if(Source){TestTrue(TEXT("Quoted Korean phrase and key can be searched together"),FIndex::Matches(**Source,TEXT("\"작은 별\" Greeting")));TestFalse(TEXT("Quoted phrase retains word order"),FIndex::Matches(**Source,TEXT("\"별 작은\"")));}
    TestTrue(TEXT("Read-only collection keeps the String Table binding"),Table->FindRow<FDirectorSpeakerRow>(TEXT("Hello"),TEXT("test"))->DisplayName.IdenticalTo(Row.DisplayName));
    FStringTableRegistry::Get().UnregisterStringTable(Strings->GetStringTableId());return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTextManagementInvalidTest,"Constellation.TextManagement.InvalidReferences",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTextManagementInvalidTest::RunTest(const FString&)
{
    auto* BP=NewObject<UBlueprint>();auto* Graph=NewObject<UEdGraph>(BP);Graph->Schema=UEdGraphSchema_K2::StaticClass();BP->FunctionGraphs.Add(Graph);
    auto* Call=NewObject<UK2Node_CallFunction>(Graph);Graph->Nodes.Add(Call);Call->FunctionReference.SetExternalMember(TEXT("TextFromStringTable"),UKismetTextLibrary::StaticClass());Call->AllocateDefaultPins();Call->CreateNewGuid();
    Call->FindPin(TEXT("TableId"))->DefaultValue=TEXT("/Game/MissingStringTable.MissingStringTable");Call->FindPin(TEXT("Key"))->DefaultValue=TEXT("Missing");
    FIndex Index;Index.Collect(BP);
    TestTrue(TEXT("Missing constant table is broken, not an exact resolved reference"),Index.Usages.ContainsByPredicate([](const FUsage& U){return U.Kind==EReferenceKind::Broken;}));
    TestFalse(TEXT("Missing constant String Table does not inflate exact count"),Index.Usages.ContainsByPredicate([](const FUsage& U){return U.Kind==EReferenceKind::Exact;}));
    auto* Director=NewObject<USceneDirectorAsset>();FDirectorStep Step;Step.Type=EDirectorNodeType::Dialogue;Step.DialogueText=FText::FromString(TEXT("대사"));Step.SpeakerSource=EDirectorSpeakerSource::Table;Director->Steps.Add(Step);
    FIndex Speaker;Speaker.Collect(Director);
    TestTrue(TEXT("Table speaker with no handle is broken"),Speaker.Usages.ContainsByPredicate([](const FUsage& U){return U.Kind==EReferenceKind::Broken&&U.Consumer.Field==TEXT("SpeakerName");}));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTextManagementUITest,"Constellation.TextManagement.WindowAndNavigation",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTextManagementUITest::RunTest(const FString&)
{
    auto Tab=FGlobalTabmanager::Get()->TryInvokeTab(FName(TEXT("Constellation.TextManagement")));
    TestTrue(TEXT("User-facing dock tab is registered and constructs"),Tab.IsValid());
    if(Tab)Tab->RequestCloseTab();
    auto* Table=NewObject<UDataTable>();Table->RowStruct=FDirectorSpeakerRow::StaticStruct();FDirectorSpeakerRow Row;Row.DisplayName=FText::FromString(TEXT("이동"));Table->AddRow(TEXT("Target"),Row);
    FLocation Loc;Loc.Kind=ELocationKind::DataTable;Loc.Asset=FSoftObjectPath(Table);Loc.Row=TEXT("Target");FText Message;
    TestTrue(TEXT("Open original table and select the row"),Navigate(Loc,Message));
    Loc.Row=TEXT("Deleted");TestFalse(TEXT("Deleted row cannot navigate to an unrelated row"),Navigate(Loc,Message));
    GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->CloseAllEditorsForAsset(Table);
    FIndex Scan;Scan.Start();TestTrue(TEXT("Maps are explicitly unscanned"),Scan.Coverage.ContainsByPredicate([](const FCoverage& C){return C.State==TEXT("미검사")&&C.Reason.Contains(TEXT("맵"));}));
    Scan.Cancel();TestFalse(TEXT("Cancellation stops further asset loading"),Scan.IsScanning());
    auto* Root=NewObject<USceneDirectorAsset>();
    auto* Child=NewObject<USceneDirectorAsset>(Root);auto* Nested=NewObject<USceneDirectorAsset>(Child);
    Root->EventGraphs.Add(Child);Child->EventGraphs.Add(Nested);
    FDirectorStep Step;Step.Type=EDirectorNodeType::Dialogue;Step.DialogueText=FText::FromString(TEXT("Nested text"));Nested->Steps.Add(Step);
    TestTrue(TEXT("Persistent Step ID navigates into a nested event"),OpenDirectorTextLocation(Root,FSoftObjectPath(Nested),Step.Id,NAME_None,TEXT("DialogueText"),Message));
    TestFalse(TEXT("Deleted choice cannot select a different choice"),OpenDirectorTextLocation(Root,FSoftObjectPath(Nested),Step.Id,TEXT("Deleted"),TEXT("Text"),Message));
    GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->CloseAllEditorsForAsset(Root);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTextManagementProductionTest,"Constellation.TextManagement.ProductionSources",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTextManagementProductionTest::RunTest(const FString&)
{
    FIndex Index;
    const TCHAR* Paths[]={
        TEXT("/Game/Constellation/Gameplay/Quests/Data/ST_QuestString.ST_QuestString"),
        TEXT("/Game/Constellation/Gameplay/Interaction/Data/ST_InteractionActions.ST_InteractionActions"),
        TEXT("/Game/Constellation/Gameplay/Interaction/Data/ST_CarryMessages.ST_CarryMessages"),
        TEXT("/Game/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData.DT_SequenceStringData"),
        TEXT("/Game/Constellation/Gameplay/Sequences/Data/DT_RegionStringData.DT_RegionStringData"),
        TEXT("/Game/Constellation/Gameplay/Sequences/Data/DT_SpeakerData.DT_SpeakerData")};
    for(const TCHAR* Path:Paths)
    {
        UObject* Object=LoadObject<UObject>(nullptr,Path);if(!TestNotNull(Path,Object))continue;
        const bool bDirty=Object->GetOutermost()->IsDirty();
        UDataTable* Table=Cast<UDataTable>(Object);const FString Before=Table?Table->GetTableAsJSON(EDataTableExportFlags::UseJsonObjectsForStructs):FString();
        const int32 Count=Index.Entries.Num();Index.Collect(Object);
        TestTrue(TEXT("Production source contributes searchable text"),Index.Entries.Num()>Count);
        TestEqual(TEXT("Scan preserves package dirty state"),Object->GetOutermost()->IsDirty(),bDirty);
        if(Table)TestEqual(TEXT("Scan preserves complete serialized table text"),Table->GetTableAsJSON(EDataTableExportFlags::UseJsonObjectsForStructs),Before);
        AddInfo(FString::Printf(TEXT("%s: %d text entries"),Path,Index.Entries.Num()-Count));
    }
    for(const TCHAR* Path:{TEXT("/Game/Constellation/UI/Blueprints/BP_HUD.BP_HUD"),TEXT("/Game/Constellation/Gameplay/Interaction/Actors/BP_RegionTrigger.BP_RegionTrigger")})
    {
        auto* Blueprint=LoadObject<UBlueprint>(nullptr,Path);if(!TestNotNull(Path,Blueprint))continue;
        const bool bDirty=Blueprint->GetOutermost()->IsDirty();Index.Collect(Blueprint);
        TestEqual(TEXT("Blueprint collection preserves dirty state"),Blueprint->GetOutermost()->IsDirty(),bDirty);
        TestTrue(TEXT("Project getter uses dynamic row names"),Index.Usages.ContainsByPredicate([&](const FUsage& U){return U.Consumer.Asset==FSoftObjectPath(Blueprint)&&U.Kind==EReferenceKind::Dynamic;}));
    }
    return true;
}
#endif
