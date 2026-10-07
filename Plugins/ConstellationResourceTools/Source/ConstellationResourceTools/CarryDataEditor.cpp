#include "CarryEditorLibrary.h"
#include "CarryComponent.h"
#include "HoldableComponent.h"
#include "CarryData.h"
#include "Animation/AnimBlueprint.h"
#include "Engine/SimpleConstructionScript.h"
#include "Engine/SCS_Node.h"
#include "Internationalization/StringTable.h"
#include "Internationalization/StringTableCore.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Kismet2/BlueprintEditorUtils.h"

namespace {
template<class T> T* CarryTemplate(UBlueprint* BP)
{
    if(BP && BP->SimpleConstructionScript)
        for(USCS_Node* N:BP->SimpleConstructionScript->GetAllNodes())
            if(T* C=Cast<T>(N->ComponentTemplate)) return C;
    return nullptr;
}
}
FString UCarryEditorLibrary::CreateCarryTables(UBlueprint* Hero,UBlueprint* Chair,UBlueprint* Desk,UBlueprint* Box)
{
    UCarryComponent* Carry=CarryTemplate<UCarryComponent>(Hero);
    if(!Carry || !CarryTemplate<UHoldableComponent>(Chair) || !CarryTemplate<UHoldableComponent>(Desk) || !CarryTemplate<UHoldableComponent>(Box)) return TEXT("ERROR: component template missing");
    const FString Folder=TEXT("/Game/Constellation/Gameplay/Interaction/Data/");
    auto Table=[&](const TCHAR* Name,UScriptStruct* Struct)
    {
        const FString Path=Folder+Name;
        UDataTable* T=LoadObject<UDataTable>(nullptr,*(Path+TEXT(".")+Name),nullptr,LOAD_NoWarn);
        if(!T) { T=NewObject<UDataTable>(CreatePackage(*Path),Name,RF_Public|RF_Standalone); T->RowStruct=Struct; FAssetRegistryModule::AssetCreated(T); T->MarkPackageDirty(); }
        return T->RowStruct==Struct?T:nullptr;
    };
    UDataTable* Settings=Table(TEXT("DT_CarrySettings"),FCarrySettingsRow::StaticStruct());
    UDataTable* Items=Table(TEXT("DT_HoldableItems"),FHoldableItemRow::StaticStruct());
    if(!Settings || !Items) return TEXT("ERROR: unexpected row struct");
    const FString StringPath=Folder+TEXT("ST_CarryMessages");
    UStringTable* Messages=LoadObject<UStringTable>(nullptr,*(StringPath+TEXT(".ST_CarryMessages")),nullptr,LOAD_NoWarn);
    if(!Messages)
    {
        Messages=NewObject<UStringTable>(CreatePackage(*StringPath),TEXT("ST_CarryMessages"),RF_Public|RF_Standalone);
        auto Strings=Messages->GetMutableStringTable(); Strings->SetNamespace(TEXT("Carry"));
        Strings->SetSourceString(TEXT("TooHeavy"),TEXT("너무 무거워서 들 수 없습니다."),TEXT(""));
        Strings->SetSourceString(TEXT("PickupUnreachable"),TEXT("물건에 닿을 수 없습니다."),TEXT(""));
        Strings->SetSourceString(TEXT("PlaceBlocked"),TEXT("공간이 부족해 내려놓을 수 없습니다."),TEXT(""));
        Strings->SetSourceString(TEXT("ThrowBlocked"),TEXT("이 위치로 던질 수 없습니다."),TEXT(""));
        FAssetRegistryModule::AssetCreated(Messages); Messages->MarkPackageDirty();
    }
    if(!Settings->FindRow<FCarrySettingsRow>(TEXT("Default"),TEXT("Migration"),false))
    {
        FCarrySettingsRow Row;
        Row.CharacterWeightKg=Carry->CharacterWeightKg;
        Row.LiftWeightRatio=Carry->LiftWeightRatio;
        Row.Reach=Carry->Reach;
        Row.MaxThrowDistance=Carry->MaxThrowDistance;
        Row.MinFlightTime=Carry->MinFlightTime;
        Row.MaxFlightTime=Carry->MaxFlightTime;
        Row.CarrySocket=Carry->CarrySocket;
        Row.WeaponComponentName=Carry->WeaponComponentName;
        Row.ReleaseOffset=Carry->ReleaseOffset;
        Row.PickupMontage=Carry->PickupMontage;
        Row.PlaceMontage=Carry->PlaceMontage;
        Row.ThrowMontage=Carry->ThrowMontage;
        Row.HoldMontage=Carry->HoldMontage;
        Row.AimMontage=Carry->AimMontage;
        Row.PreviewMaterial=Carry->PreviewMaterial;
        Row.PickupPlayRate=Carry->PickupPlayRate;
        Row.PlacePlayRate=Carry->PlacePlayRate;
        Row.ThrowPlayRate=Carry->ThrowPlayRate;
        Row.PickupContactTime=Carry->PickupContactTime;
        Row.PickupDuration=Carry->PickupDuration;
        Row.PlaceContactTime=Carry->PlaceContactTime;
        Row.PlaceDuration=Carry->PlaceDuration;
        Row.ThrowContactTime=Carry->ThrowContactTime;
        Row.ThrowDuration=Carry->ThrowDuration;
        Row.NoticeDuration=Carry->NoticeDuration;
        Row.Messages=Messages; Settings->AddRow(TEXT("Default"),Row); Settings->MarkPackageDirty();
    }
    Carry->SettingsRow.DataTable=Settings; Carry->SettingsRow.RowName=TEXT("Default");
    FBlueprintEditorUtils::MarkBlueprintAsModified(Hero);
    auto LinkItem=[&](UBlueprint* BP,FName Name)
    {
        UHoldableComponent* Hold=CarryTemplate<UHoldableComponent>(BP);
        if(!Items->FindRow<FHoldableItemRow>(Name,TEXT("Migration"),false))
        {
            FHoldableItemRow Row;
            Row.CarryOffset=Hold->CarryOffset;
            Row.LeftHandGrip=Hold->LeftHandGrip;
            Row.RightHandGrip=Hold->RightHandGrip;
            Row.bCanThrow=Hold->bCanThrow;
            Row.PlaceRotation=Hold->PlaceRotation;
            Items->AddRow(Name,Row); Items->MarkPackageDirty();
        }
        Hold->ItemRow.DataTable=Items; Hold->ItemRow.RowName=Name;
        FBlueprintEditorUtils::MarkBlueprintAsModified(BP);
    };
    LinkItem(Chair,TEXT("SchoolChair")); LinkItem(Desk,TEXT("SchoolDesk")); LinkItem(Box,TEXT("TestBox"));
    return TEXT("OK: tables created/linked; existing rows and translations preserved");
}

FString UCarryEditorLibrary::CreateInteractionStrings(const FString& SourceCSV)
{
    const FString Path=TEXT("/Game/Constellation/Gameplay/Interaction/Data/ST_InteractionActions");
    if(LoadObject<UStringTable>(nullptr,*(Path+TEXT(".ST_InteractionActions")),nullptr,LOAD_NoWarn))
        return TEXT("OK: existing designer strings preserved");
    // Validate the source before creating a persistent asset.
    FStringTableRef Source=MakeShared<FStringTable,ESPMode::ThreadSafe>();
    if(!Source->ImportStringsFromCSVFile(SourceCSV)) return TEXT("ERROR: cannot read action strings CSV");
    UStringTable* Table=NewObject<UStringTable>(CreatePackage(*Path),TEXT("ST_InteractionActions"),RF_Public|RF_Standalone);
    Table->GetMutableStringTable()->SetNamespace(TEXT("InteractionPrompt"));
    if(!Table->GetMutableStringTable()->ImportStringsFromCSVFile(SourceCSV)) return TEXT("ERROR: cannot import action strings");
    FAssetRegistryModule::AssetCreated(Table);
    Table->MarkPackageDirty();
    return TEXT("OK: action strings imported");
}
