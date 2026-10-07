#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CombatWorkbenchSubsystem.h"
#include "CombatLabCharacter.h"
#include "CombatAbilitySystem.h"
#include "CombatActionDefinition.h"
#include "Animation/AnimMontage.h"
namespace CombatTest { UCombatActionDefinition* Action(UObject* Outer); }
#include "CombatPatternProfile.h"
#include "CombatEncounterProfile.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "HAL/FileManager.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"
#include <limits>

namespace
{
UCombatWorkbenchSubsystem* MakeWorkbench()
{
    return NewObject<UCombatWorkbenchSubsystem>(NewObject<UGameInstance>());
}
ACombatLabCharacter* SpawnWorkbenchActor(UWorld* World, FName Name=NAME_None)
{
    FActorSpawnParameters Params;
    Params.Name=Name;
    Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    return World->SpawnActor<ACombatLabCharacter>(FVector::ZeroVector,FRotator::ZeroRotator,Params);
}
int32 FieldIndex(const UCombatWorkbenchSubsystem* Model, const UObject* Object, FName Property)
{
    return Model->Fields.IndexOfByPredicate([Object,Property](const FCombatTuningField& Field)
    { return Field.Object.Get()==Object && Field.Property==Property; });
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatWorkbenchIsolationTest,"Constellation.CombatCore.WorkbenchCloneIsolation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatWorkbenchIsolationTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Model=MakeWorkbench();
    auto* First=SpawnWorkbenchActor(World);
    auto* Second=SpawnWorkbenchActor(World);
    auto* Action=NewObject<UCombatActionDefinition>();
    auto* Followup=NewObject<UCombatActionDefinition>();
    Action->Damage=17.f; Action->NextAction=Followup; Followup->NextAction=Action;
    auto* Pattern=NewObject<UCombatPatternProfile>();
    FCombatPatternEntry Entry; Entry.Id=TEXT("SharedAttack"); Entry.Action=Action;
    Pattern->Patterns.Add(Entry);
    auto* Encounter=NewObject<UCombatEncounterProfile>();
    for(auto* Actor:{First,Second})
    {
        Actor->Action=Action; Actor->PatternProfile=Pattern; Actor->EncounterProfile=Encounter;
        Model->PrepareActor(Actor);
    }
    TestTrue(TEXT("Actors own separate action copies"),First->Action!=Second->Action && First->Action!=Action && Second->Action!=Action);
    TestTrue(TEXT("Cycle stays within first actor's copies"),First->Action->NextAction->NextAction==First->Action);
    TestTrue(TEXT("Followups are isolated across actors"),First->Action->NextAction!=Second->Action->NextAction);
    TestTrue(TEXT("Pattern shares the actor's action copy"),First->PatternProfile->Patterns[0].Action==First->Action);
    TestTrue(TEXT("Profiles are isolated across actors"),First->PatternProfile!=Second->PatternProfile && First->EncounterProfile!=Second->EncounterProfile);
    First->Action->Damage=42.f;
    First->PatternProfile->Patterns[0].Weight=9.f;
    First->EncounterProfile->DetectRadius=950.f;
    TestEqual(TEXT("Original action is untouched"),Action->Damage,17.f);
    TestEqual(TEXT("Second actor action is untouched"),Second->Action->Damage,17.f);
    TestEqual(TEXT("Original pattern is untouched"),Pattern->Patterns[0].Weight,1.f);
    TestEqual(TEXT("Second actor pattern is untouched"),Second->PatternProfile->Patterns[0].Weight,1.f);
    TestEqual(TEXT("Original encounter is untouched"),Encounter->DetectRadius,800.f);
    const int32 Count=Model->Fields.Num();
    Model->PrepareActor(First);
    TestEqual(TEXT("Repeated preparation does not duplicate fields"),Model->Fields.Num(),Count);
    auto* Copy=First->Action.Get();
    Model->PrepareActor(First);
    TestTrue(TEXT("Repeated preparation retains action identity"),First->Action==Copy);
    const TArray<double> Before=Model->ReadValues();
    TArray<double> Fractional=Before;
    const int32 Repeat=FieldIndex(Model,First->PatternProfile,TEXT("MaxConsecutive"));
    if(TestTrue(TEXT("Pattern integer field is exposed"),Repeat!=INDEX_NONE))
    {
        Fractional[Repeat]=1.5;
        FString Error;
        TestFalse(TEXT("Fractional repeat limits are rejected"),Model->ValidateValues(Fractional,Error));
        TestTrue(TEXT("Rejected integer edit leaves values intact"),Model->ReadValues()==Before);
    }
    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatWorkbenchValidationTest,"Constellation.CombatCore.WorkbenchDraftValidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatWorkbenchValidationTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Model=MakeWorkbench();
    auto* Actor=SpawnWorkbenchActor(World);
    Actor->EncounterProfile=NewObject<UCombatEncounterProfile>();
    Model->PrepareActor(Actor);
    FString Error;
    const TArray<double> Before=Model->ReadValues();
    TestTrue(TEXT("Baseline is valid"),Model->ValidateValues(Before,Error));
    auto Reject=[&](const UObject* Object,FName Property,double Value,const TCHAR* Label)
    {
        TArray<double> Draft=Before;
        const int32 Index=FieldIndex(Model,Object,Property);
        if(!TestTrue(TEXT("Editable field exists"),Index!=INDEX_NONE)) return;
        Draft[Index]=Value;
        TestFalse(Label,Model->ApplyValues(Draft,Error));
        TestFalse(TEXT("Rejection explains the problem"),Error.IsEmpty());
        TestTrue(TEXT("Rejected draft leaves every live value intact"),Model->ReadValues()==Before);
    };
    Reject(Actor->Combat,TEXT("MaxHealth"),-1,TEXT("Negative health limit rejected"));
    Reject(Actor->Combat,TEXT("MaxStamina"),std::numeric_limits<double>::quiet_NaN(),TEXT("NaN stamina rejected"));
    Reject(Actor->Combat,TEXT("DodgeDistance"),0,TEXT("Zero dodge distance rejected consistently with runtime"));
    Reject(Actor->Combat,TEXT("DodgeInvulnerableEnd"),.1,TEXT("Empty invulnerability interval rejected consistently with runtime"));
    Reject(Actor->Combat,TEXT("DodgeInvulnerableEnd"),2,TEXT("Invulnerability beyond dodge duration rejected"));
    Reject(Actor->EncounterProfile,TEXT("LoseRadius"),100,TEXT("Loss radius inside detection radius rejected"));
    Reject(Actor->EncounterProfile,TEXT("bRestoreOnReturn"),.5,TEXT("Fractional boolean rejected"));
    TArray<double> Draft=Before;
    const int32 Health=FieldIndex(Model,Actor->Combat,TEXT("MaxHealth"));
    if(TestTrue(TEXT("Health field exists"),Health!=INDEX_NONE))
    {
        Draft[Health]=250;
        TestTrue(TEXT("Valid draft accepted"),Model->ValidateValues(Draft,Error));
        TestTrue(TEXT("Successful validation also rolls back temporary writes"),Model->ReadValues()==Before);
        TestTrue(TEXT("Valid draft stages for restart"),Model->ApplyValues(Draft,Error));
        TestTrue(TEXT("Staging does not alter current combat"),Model->ReadValues()==Before);
    }
    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatWorkbenchPersistenceTest,"Constellation.CombatCore.WorkbenchPresetAndRestart",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatWorkbenchPersistenceTest::RunTest(const FString&)
{
    const FString Token=FGuid::NewGuid().ToString(EGuidFormats::Digits);
    UPackage* Package=CreatePackage(*(TEXT("/Temp/CombatWorkbenchTest_")+Token));
    UWorld* FirstWorld=UWorld::CreateWorld(EWorldType::Game,false,TEXT("BeforeRestart"),Package);
    auto* Model=MakeWorkbench();
    auto* Actor=SpawnWorkbenchActor(FirstWorld,TEXT("Player"));
    Model->PrepareActor(Actor);
    TArray<double> Draft=Model->ReadValues();
    const int32 Health=FieldIndex(Model,Actor->Combat,TEXT("MaxHealth"));
    const int32 Stamina=FieldIndex(Model,Actor->Combat,TEXT("MaxStamina"));
    if(!TestTrue(TEXT("Resource fields exist"),Health!=INDEX_NONE && Stamina!=INDEX_NONE))
    { FirstWorld->DestroyWorld(false); return false; }
    Draft[Health]=250; Draft[Stamina]=60;
    FString Error;
    const FString Name=TEXT("Automation_")+Token;
    const FString Path=FPaths::ProjectSavedDir()/TEXT("CombatTuning")/(Name+TEXT(".json"));
    const bool Saved=Model->SavePreset(Draft,Name,Error);
    TestTrue(TEXT("Unique preset saves"),Saved);
    if(Saved)
    {
        TestTrue(TEXT("Saved preset is listed"),Model->ListPresets().Contains(Name));
        TestFalse(TEXT("Save cannot overwrite existing preset"),Model->SavePreset(Draft,Name,Error));
        TArray<double> Loaded;
        TestTrue(TEXT("Preset loads"),Model->LoadPreset(Name,Loaded,Error));
        TestTrue(TEXT("Preset values round trip exactly"),Loaded==Draft);
        TestEqual(TEXT("Loading leaves live health default intact"),Actor->Combat->MaxHealth,100.f);
        TestTrue(TEXT("Loaded preset stages successfully"),Model->ApplyValues(Loaded,Error));
        FString OriginalJson;
        if(TestTrue(TEXT("Read this test's saved preset"),FFileHelper::LoadFileToString(OriginalJson,*Path)))
        {
            const TArray<double> LiveBefore=Model->ReadValues();
            auto RejectJson=[&](const FString& Json,const TCHAR* Label)
            {
                const bool Written=FFileHelper::SaveStringToFile(Json,*Path,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
                TestTrue(TEXT("Write only this test's GUID preset"),Written);
                if(Written)
                {
                    TArray<double> UnchangedDraft={123.,456.};
                    TestFalse(Label,Model->LoadPreset(Name,UnchangedDraft,Error));
                    TestTrue(TEXT("Rejected JSON preserves caller's draft"),UnchangedDraft==TArray<double>{123.,456.});
                    TestTrue(TEXT("Rejected JSON preserves every live value"),Model->ReadValues()==LiveBefore);
                    TestFalse(TEXT("Rejected JSON explains the problem"),Error.IsEmpty());
                }
                TestTrue(TEXT("Restore original preset after rejection case"),
                    FFileHelper::SaveStringToFile(OriginalJson,*Path,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM));
            };
            RejectJson(TEXT("{broken"),TEXT("Malformed JSON is rejected"));
            auto RejectChangedJson=[&](TFunction<void(FJsonObject&)> Change,const TCHAR* Label)
            {
                TSharedPtr<FJsonObject> Json;
                if(!TestTrue(TEXT("Parse original test preset"),FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(OriginalJson),Json) && Json.IsValid())) return;
                Change(*Json);
                FString Modified;
                if(TestTrue(TEXT("Serialize modified test preset"),FJsonSerializer::Serialize(Json.ToSharedRef(),TJsonWriterFactory<>::Create(&Modified))))
                    RejectJson(Modified,Label);
            };
            RejectChangedJson([](FJsonObject& Json){Json.SetNumberField(TEXT("schema_version"),99);},TEXT("Unsupported schema is rejected"));
            RejectChangedJson([&](FJsonObject& Json)
            {
                Json.GetObjectField(TEXT("values"))->SetStringField(Model->Fields[Health].Key,TEXT("250"));
            },TEXT("Numeric strings cannot bypass strict JSON number validation"));
            RejectChangedJson([&](FJsonObject& Json)
            {
                Json.GetObjectField(TEXT("sources"))->SetStringField(Model->Fields[Health].ActorKey,TEXT("DifferentSourceAsset"));
            },TEXT("Mismatched source assets are rejected"));
            TArray<double> Restored;
            TestTrue(TEXT("Restored original preset still loads"),Model->LoadPreset(Name,Restored,Error));
            TestTrue(TEXT("Restored values still match saved draft"),Restored==Draft);
        }
    }
    else Model->ApplyValues(Draft,Error);
    TArray<double> Sentinel={123.};
    TestFalse(TEXT("Traversal preset name is rejected"),Model->LoadPreset(TEXT("../escape"),Sentinel,Error));
    TestTrue(TEXT("Failed load preserves draft output"),Sentinel==TArray<double>{123.});
    UWorld* NextWorld=UWorld::CreateWorld(EWorldType::Game,false,TEXT("AfterRestart"),Package);
    auto* Restarted=SpawnWorkbenchActor(NextWorld,TEXT("Player"));
    Model->PrepareActor(Restarted);
    Restarted->Combat->InitializeCombat(Restarted);
    TestEqual(TEXT("Restart applies staged maximum health"),Restarted->Combat->GetHealth(),250.f);
    TestEqual(TEXT("Restart applies staged maximum stamina"),Restarted->Combat->GetStamina(),60.f);
    TestEqual(TEXT("Restart replaces old world fields"),Model->Fields.Num(),Draft.Num());
    TestEqual(TEXT("Original actor remains untouched"),Actor->Combat->MaxHealth,100.f);
    if(Saved) TestTrue(TEXT("Remove only this test's preset"),IFileManager::Get().Delete(*Path));
    NextWorld->DestroyWorld(false);
    FirstWorld->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatWorkbenchReportTest,"Constellation.CombatCore.WorkbenchTuningReport",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatWorkbenchReportTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Model=MakeWorkbench();
    auto* Player=SpawnWorkbenchActor(World);
    auto* Enemy=SpawnWorkbenchActor(World);
    Enemy->bTrainingEnemy=true;
    Enemy->EncounterProfile=NewObject<UCombatEncounterProfile>();
    Model->PrepareActor(Player);Model->PrepareActor(Enemy);
    const int32 Health=FieldIndex(Model,Player->Combat,TEXT("MaxHealth"));
    const int32 Restore=FieldIndex(Model,Enemy->EncounterProfile,TEXT("bRestoreOnReturn"));
    if(!TestTrue(TEXT("Report fixture fields exist"),Health!=INDEX_NONE && Restore!=INDEX_NONE))
    {World->DestroyWorld(false);return false;}
    Player->Combat->MaxHealth=175;
    const auto Before=Model->ReadValues();
    auto Draft=Before;Draft[Health]=200;Draft[Restore]=0;
    FString Error;
    const FString Name=TEXT("ReportTest_")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    const FString Path=FPaths::ProjectSavedDir()/TEXT("CombatTuningReports")/(Name+TEXT(".json"));
    TestFalse(TEXT("Unsafe report path rejected"),Model->ExportTuningReport(Draft,TEXT("../escape"),Error));
    auto Invalid=Draft;Invalid[Health]=-1;
    TestFalse(TEXT("Invalid draft rejected"),Model->ExportTuningReport(Invalid,Name,Error));
    TestFalse(TEXT("Invalid draft writes no file"),IFileManager::Get().FileExists(*Path));
    const bool Saved=Model->ExportTuningReport(Draft,Name,Error);
    TestTrue(TEXT("Valid draft report saved"),Saved);
    TestTrue(TEXT("Export leaves live values intact"),Model->ReadValues()==Before);
    if(Saved)
    {
        FString Original;TSharedPtr<FJsonObject> Root;
        const bool Parsed=FFileHelper::LoadFileToString(Original,*Path) &&
            FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Original),Root) && Root.IsValid();
        if(TestTrue(TEXT("Report is readable JSON"),Parsed))
        {
            TestEqual(TEXT("Report format identified"),Root->GetStringField(TEXT("kind")),FString(TEXT("ConstellationCombatTuningReport")));
            TestEqual(TEXT("Report includes all fields"),Root->GetArrayField(TEXT("fields")).Num(),Model->Fields.Num());
            TestEqual(TEXT("Changes from current counted"),Root->GetIntegerField(TEXT("changed_from_current")),2);
            const auto H=Root->GetArrayField(TEXT("fields"))[Health]->AsObject();
            TestEqual(TEXT("Original default distinguished"),H->GetNumberField(TEXT("initial")),100.);
            TestEqual(TEXT("Currently applied distinguished"),H->GetNumberField(TEXT("current")),175.);
            TestEqual(TEXT("Proposed draft distinguished"),H->GetNumberField(TEXT("proposed")),200.);
            TestEqual(TEXT("Human label retained"),H->GetStringField(TEXT("label")),Model->Fields[Health].Label);
            TestEqual(TEXT("Stable field key retained"),H->GetStringField(TEXT("key")),Model->Fields[Health].Key);
            TestEqual(TEXT("Boolean type retained"),Root->GetArrayField(TEXT("fields"))[Restore]->AsObject()->GetStringField(TEXT("value_type")),FString(TEXT("boolean_0_1")));
            const auto Preset=Root->GetObjectField(TEXT("preset"));
            TestEqual(TEXT("Preset includes all proposed values"),Preset->GetObjectField(TEXT("values"))->Values.Num(),Draft.Num());
            TestEqual(TEXT("Both actors' source signatures retained"),Preset->GetObjectField(TEXT("sources"))->Values.Num(),2);
            TestEqual(TEXT("Embedded preset uses proposed value"),Preset->GetObjectField(TEXT("values"))->GetNumberField(Model->Fields[Health].Key),200.);
        }
        TArray<double> Imported;
        TestTrue(TEXT("Report loads without extracting preset"),Model->LoadTuningReport(Name,Imported,Error));
        TestTrue(TEXT("Report draft matches export"),Imported==Draft);
        TestTrue(TEXT("Report picker includes export"),Model->ListTuningReports().Contains(Name));
        auto CheckReport=[&](TFunction<void(FJsonObject&)> Change,bool Accept,const TCHAR* Label)
        {
            TSharedPtr<FJsonObject> Edited;
            if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Original),Edited) || !Edited.IsValid()) return;
            Change(*Edited);FString Modified;
            FJsonSerializer::Serialize(Edited.ToSharedRef(),TJsonWriterFactory<>::Create(&Modified));
            TestTrue(TEXT("Write only test report"),FFileHelper::SaveStringToFile(Modified,*Path));
            TArray<double> Values={123.,456.};
            TestEqual(Label,Model->LoadTuningReport(Name,Values,Error),Accept);
            if(!Accept) TestTrue(TEXT("Rejected report keeps caller draft"),Values==TArray<double>{123.,456.});
            else TestEqual(TEXT("Preset values are the only import authority"),Values[Health],225.);
            TestTrue(TEXT("Import never changes live values"),Model->ReadValues()==Before);
            FFileHelper::SaveStringToFile(Original,*Path);
        };
        CheckReport([&](FJsonObject& R){R.GetObjectField(TEXT("preset"))->GetObjectField(TEXT("values"))->SetNumberField(Model->Fields[Health].Key,225);},
            true,TEXT("AI can change preset while exported metadata stays historical"));
        CheckReport([](FJsonObject& R){R.SetNumberField(TEXT("schema_version"),2);},false,TEXT("Unknown report version rejected"));
        CheckReport([](FJsonObject& R){R.RemoveField(TEXT("preset"));},false,TEXT("Missing preset rejected"));
        CheckReport([&](FJsonObject& R){R.GetObjectField(TEXT("preset"))->GetObjectField(TEXT("values"))->SetNumberField(Model->Fields[Health].Key,-1);},
            false,TEXT("Invalid AI value rejected"));
        CheckReport([&](FJsonObject& R){R.GetObjectField(TEXT("preset"))->GetObjectField(TEXT("values"))->SetStringField(Model->Fields[Health].Key,TEXT("225"));},
            false,TEXT("Numeric string rejected"));
        CheckReport([&](FJsonObject& R){R.GetObjectField(TEXT("preset"))->GetObjectField(TEXT("sources"))->SetStringField(Model->Fields[Health].ActorKey,TEXT("OtherActor"));},
            false,TEXT("Different source rejected"));
        TArray<double> Sentinel={7.};
        TestFalse(TEXT("Unsafe report import name rejected"),Model->LoadTuningReport(TEXT("../escape"),Sentinel,Error));
        TestTrue(TEXT("Invalid name preserves draft"),Sentinel==TArray<double>{7.});
        TestFalse(TEXT("Existing report not overwritten"),Model->ExportTuningReport(Before,Name,Error));
        FString After;FFileHelper::LoadFileToString(After,*Path);
        TestEqual(TEXT("Existing report content preserved"),After,Original);
        TestFalse(TEXT("Report not mixed into preset picker"),Model->ListPresets().Contains(Name));
        TestTrue(TEXT("Remove only this test's report"),IFileManager::Get().Delete(*Path));
    }
    World->DestroyWorld(false);return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatWorkbenchInputWindowTest,"Constellation.CombatCore.WorkbenchInputWindow",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatWorkbenchInputWindowTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=SpawnWorkbenchActor(World);
    Actor->Action=CombatTest::Action(Actor);
    Actor->Action->NextAction=CombatTest::Action(Actor);
    auto* Model=MakeWorkbench();Model->PrepareActor(Actor);
    auto* Action=Actor->Action.Get();
    const int32 Start=FieldIndex(Model,Action,TEXT("InputWindowStart"));
    const int32 End=FieldIndex(Model,Action,TEXT("InputWindowEnd"));
    if(!TestTrue(TEXT("Linked action exposes both input times"),Start!=INDEX_NONE && End!=INDEX_NONE))
    {World->DestroyWorld(false);return false;}
    TestEqual(TEXT("Terminal action has no meaningless input fields"),FieldIndex(Model,Action->NextAction,TEXT("InputWindowStart")),INDEX_NONE);
    const auto Before=Model->ReadValues();
    auto Values=Before;Values[Start]=.2;Values[End]=.6;
    FString Error;
    TestTrue(TEXT("Valid range accepted"),Model->ValidateValues(Values,Error));
    TestTrue(TEXT("Validation preserves runtime"),Model->ReadValues()==Before);
    auto Bad=Values;Bad[End]=Bad[Start];
    TestFalse(TEXT("Empty interval rejected"),Model->ValidateValues(Bad,Error));
    Bad=Values;Bad[End]=Action->Montage->GetPlayLength()+1;
    TestFalse(TEXT("Beyond montage rejected"),Model->ValidateValues(Bad,Error));
    const int32 Allow=FieldIndex(Model,Action,TEXT("bAllowDodgeCancel"));
    const int32 CancelEnd=FieldIndex(Model,Action,TEXT("DodgeCancelEnd"));
    if(TestTrue(TEXT("Dodge transition fields exposed"),Allow!=INDEX_NONE && CancelEnd!=INDEX_NONE))
    {
        Bad=Values;Bad[Allow]=1;Bad[CancelEnd]=.1;
        TestFalse(TEXT("Enabled reversed dodge window rejected"),Model->ValidateValues(Bad,Error));
        Bad[CancelEnd]=Action->Montage->GetPlayLength()+1;
        TestFalse(TEXT("Enabled dodge window beyond montage rejected"),Model->ValidateValues(Bad,Error));
        Values[Allow]=1;
        TestTrue(TEXT("Valid dodge transition settings accepted"),Model->ValidateValues(Values,Error));
    }
    const FString Name=TEXT("WindowTest_")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    const FString Path=FPaths::ProjectSavedDir()/TEXT("CombatTuning")/(Name+TEXT(".json"));
    if(TestTrue(TEXT("Save extended preset"),Model->SavePreset(Values,Name,Error)))
    {
        TArray<double> Loaded;
        TestTrue(TEXT("Extended preset reloads"),Model->LoadPreset(Name,Loaded,Error));
        TestTrue(TEXT("Input times round-trip"),Loaded==Values);
        FString Json;FFileHelper::LoadFileToString(Json,*Path);
        TSharedPtr<FJsonObject> Root;
        if(FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json),Root) && Root.IsValid())
        {
            TestEqual(TEXT("Extended presets use schema 4"),Root->GetIntegerField(TEXT("schema_version")),4);
            auto V=Root->GetObjectField(TEXT("values"));
            // Schema 3 predates ultimate resources; migrate only those additions.
            for(const auto& F:Model->Fields)
                if(F.Property==TEXT("UltimateCost") || F.Property==TEXT("UltimateGain") || F.Property==TEXT("bRadialHit") || F.Property==TEXT("DashDistance") || F.Property==TEXT("DashDuration")) V->RemoveField(F.Key);
            Root->SetNumberField(TEXT("schema_version"),3);
            FString Old3;FJsonSerializer::Serialize(Root.ToSharedRef(),TJsonWriterFactory<>::Create(&Old3));FFileHelper::SaveStringToFile(Old3,*Path);
            TestTrue(TEXT("Schema 3 receives ultimate defaults"),Model->LoadPreset(Name,Loaded,Error));
            for(int32 I=0;I<Model->Fields.Num();++I)
                if(Loaded.IsValidIndex(I) && (Model->Fields[I].Property==TEXT("UltimateCost") || Model->Fields[I].Property==TEXT("UltimateGain")))
                    TestEqual(TEXT("Ultimate migration uses source default"),Loaded[I],Before[I]);
            // Schema 2 knows input windows but predates dodge cancellation.
            for(const auto& F:Model->Fields)
                if(F.Property==TEXT("bAllowDodgeCancel") || F.Property==TEXT("DodgeCancelStart") || F.Property==TEXT("DodgeCancelEnd"))
                    V->RemoveField(F.Key);
            Root->SetNumberField(TEXT("schema_version"),2);
            FString Legacy;FJsonSerializer::Serialize(Root.ToSharedRef(),TJsonWriterFactory<>::Create(&Legacy));FFileHelper::SaveStringToFile(Legacy,*Path);
            TestTrue(TEXT("Schema 2 remains loadable"),Model->LoadPreset(Name,Loaded,Error));
            if(Loaded.IsValidIndex(Allow)) TestEqual(TEXT("Old preset does not silently enable attack cancel"),Loaded[Allow],0.);
            TestFalse(TEXT("Migration reports added defaults"),Error.IsEmpty());
            Root->SetNumberField(TEXT("schema_version"),4);
            V->RemoveField(Model->Fields[Start].Key);V->RemoveField(Model->Fields[End].Key);
            auto Write=[&]{FString Out;FJsonSerializer::Serialize(Root.ToSharedRef(),TJsonWriterFactory<>::Create(&Out));FFileHelper::SaveStringToFile(Out,*Path);};
            Write();Loaded={7.};
            TestFalse(TEXT("Current schema requires all fields"),Model->LoadPreset(Name,Loaded,Error));
            TestTrue(TEXT("Failure retains draft"),Loaded==TArray<double>{7.});
            Root->SetNumberField(TEXT("schema_version"),1);Write();
            Action->InputWindowStart=.3f;
            TestTrue(TEXT("Legacy preset receives only new field defaults"),Model->LoadPreset(Name,Loaded,Error));
            if(Loaded.Num()==Before.Num())
            {
                TestEqual(TEXT("Legacy start uses asset default, not current tuning"),Loaded[Start],Before[Start]);
                TestEqual(TEXT("Legacy end uses asset default"),Loaded[End],Before[End]);
            }
            const int32 Damage=FieldIndex(Model,Action,TEXT("Damage"));
            V->RemoveField(Model->Fields[Damage].Key);Write();
            TestFalse(TEXT("Legacy missing existing field rejected"),Model->LoadPreset(Name,Loaded,Error));
        }
        TestTrue(TEXT("Remove only test preset"),IFileManager::Get().Delete(*Path));
    }
    World->DestroyWorld(false);return true;
}

#endif