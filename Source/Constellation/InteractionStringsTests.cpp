#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR
#include "Misc/AutomationTest.h"
#include "InteractionPromptComponent.h"
#include "Internationalization/StringTable.h"
#include "Internationalization/StringTableCore.h"
#include "Internationalization/StringTableRegistry.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInteractionStringsTest,"Constellation.InteractionPrompt.StringTableEdits",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FInteractionStringsTest::RunTest(const FString&)
{
    UInteractionPromptComponent* Prompt=NewObject<UInteractionPromptComponent>();
    TestTrue(TEXT("Unassigned table hides text"),Prompt->GetActionText(EInteractionAction::PickUp).IsEmpty());
    UStringTable* Table=NewObject<UStringTable>();
    FStringTableRegistry::Get().RegisterStringTable(Table->GetStringTableId(),Table->GetMutableStringTable());
    Prompt->ActionStrings=Table;
    auto Strings=Table->GetMutableStringTable();
    Strings->SetSourceString(TEXT("PickUp"),TEXT("Designer pickup"),TEXT(""));
    TestEqual(TEXT("Uses designer text"),Prompt->GetActionText(EInteractionAction::PickUp).ToString(),FString(TEXT("Designer pickup")));
    Strings->SetSourceString(TEXT("PickUp"),TEXT("Edited pickup"),TEXT(""));
    TestEqual(TEXT("Edits reflected without code changes"),Prompt->GetActionText(EInteractionAction::PickUp).ToString(),FString(TEXT("Edited pickup")));
    TestTrue(TEXT("Missing key hides text"),Prompt->GetActionText(EInteractionAction::Open).IsEmpty());
    TestTrue(TEXT("None has no label"),Prompt->GetActionText(EInteractionAction::None).IsEmpty());
    TestTrue(TEXT("Invalid action has no label"),Prompt->GetActionText(static_cast<EInteractionAction>(255)).IsEmpty());
    FStringTableRegistry::Get().UnregisterStringTable(Table->GetStringTableId());
    return true;
}
#endif
