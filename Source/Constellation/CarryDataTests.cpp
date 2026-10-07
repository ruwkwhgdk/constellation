#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR
#include "Misc/AutomationTest.h"
#include "CarryComponent.h"
#include "HoldableComponent.h"
#include "Internationalization/StringTable.h"
#include "Internationalization/StringTableCore.h"
#include "Internationalization/StringTableRegistry.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarryDataTest,"Constellation.Carry.DataTablesAndMessages",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FCarryDataTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    ACharacter* Character=World->SpawnActor<ACharacter>();
    UCarryComponent* Carry=NewObject<UCarryComponent>(Character);
    UDataTable* Settings=NewObject<UDataTable>(); Settings->RowStruct=FCarrySettingsRow::StaticStruct();
    UStringTable* Messages=NewObject<UStringTable>();
    FStringTableRegistry::Get().RegisterStringTable(Messages->GetStringTableId(),Messages->GetMutableStringTable());
    Messages->GetMutableStringTable()->SetSourceString(TEXT("TooHeavy"),TEXT("Designer message"),TEXT(""));
    FCarrySettingsRow Row; Row.Reach=245; Row.PickupPlayRate=3; Row.PlacePlayRate=4; Row.Messages=Messages;
    Settings->AddRow(TEXT("Tuned"),Row); Carry->SettingsRow.DataTable=Settings; Carry->SettingsRow.RowName=TEXT("Tuned");
    TestTrue(TEXT("Valid common row applies"),Carry->ApplySettings());
    TestEqual(TEXT("Reach comes from row"),Carry->Reach,245.f);
    TestEqual(TEXT("Pickup rate comes from row"),Carry->PickupPlayRate,3.f);
    TestEqual(TEXT("Place rate comes from row"),Carry->PlacePlayRate,4.f);
    TestEqual(TEXT("Message comes from String Table"),Carry->GetCarryMessage(TEXT("TooHeavy")).ToString(),FString(TEXT("Designer message")));
    Messages->GetMutableStringTable()->SetSourceString(TEXT("TooHeavy"),TEXT("Edited message"),TEXT(""));
    TestEqual(TEXT("Text edits are used"),Carry->GetCarryMessage(TEXT("TooHeavy")).ToString(),FString(TEXT("Edited message")));
    Row.Reach=310; Settings->AddRow(TEXT("Tuned"),Row); Carry->ApplySettings();
    TestEqual(TEXT("Row edits are used"),Carry->Reach,310.f);
    Carry->State=ECarryState::Carrying; TestFalse(TEXT("Do not retune an active carry"),Carry->ApplySettings());
    UHoldableComponent* Hold=NewObject<UHoldableComponent>(Character);
    UDataTable* Items=NewObject<UDataTable>(); Items->RowStruct=FHoldableItemRow::StaticStruct();
    FHoldableItemRow Item; Item.bCanThrow=false; Item.CarryOffset=FTransform(FVector(45,0,12));
    Items->AddRow(TEXT("Prop"),Item); Hold->ItemRow.DataTable=Items; Hold->ItemRow.RowName=TEXT("Prop");
    TestTrue(TEXT("Valid item row applies"),Hold->ApplySettings());
    TestFalse(TEXT("Throw permission comes from row"),Hold->bCanThrow);
    TestTrue(TEXT("Carry position comes from row"),Hold->CarryOffset.GetLocation().Equals(FVector(45,0,12)));
    FStringTableRegistry::Get().UnregisterStringTable(Messages->GetStringTableId());
    World->DestroyWorld(false); return true;
}
#endif
