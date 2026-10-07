#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CombatLabEditorLibrary.h"
#include "CombatLabCharacter.h"
#include "CombatEncounterProfile.h"
#include "CombatPatternProfile.h"
#include "CombatActionDefinition.h"
#include "Engine/World.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonSerializer.h"
#include "ToolMenus.h"
#include <limits>
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatReportTest,"Constellation.CombatCore.EditorCharacterReport",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatReportTest::RunTest(const FString&)
{
    auto* Menu=UToolMenus::Get()->FindMenu("LevelEditor.MainMenu.Tools");
    auto* Section=Menu?Menu->FindSection("ConstellationCombat"):nullptr;
    TestTrue(TEXT("Report save menu registered"),Section && Section->FindEntry("CombatSaveSelectedReport"));
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);
    auto* Enemy=World->SpawnActor<ACombatLabCharacter>(); Enemy->bTrainingEnemy=true;
    Enemy->SetActorLabel(TEXT("Report \"enemy\""));
    Enemy->EncounterProfile=NewObject<UCombatEncounterProfile>(Enemy);
    Enemy->EncounterProfile->MoveSpeed=237;
    Enemy->PatternProfile=NewObject<UCombatPatternProfile>(Enemy);
    FCombatPatternEntry Pattern; Pattern.Id=TEXT("Broken");
    Pattern.Action=NewObject<UCombatActionDefinition>(Enemy);
    Pattern.Action->Damage=37; Pattern.Action->StaminaCost=101;
    Enemy->PatternProfile->Patterns.Add(Pattern);
    FString Path,Error,Text;
    const bool Saved=UCombatLabEditorLibrary::SaveCombatCharacterReport(Enemy,Path,Error);
    TestTrue(TEXT("Invalid configuration still produces a report"),Saved);
    if(Saved)
    {
        TestTrue(TEXT("Report exists"),FFileHelper::LoadFileToString(Text,*Path));
        TSharedPtr<FJsonObject> Json;
        const bool Parsed=FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Json);
        TestTrue(TEXT("Report is valid JSON"),Parsed);
        if(Parsed)
        {
            TestFalse(TEXT("Invalidity is separate from save success"),Json->GetBoolField(TEXT("valid")));
            TestEqual(TEXT("Unsaved live movement captured"),Json->GetObjectField(TEXT("encounter"))->GetNumberField(TEXT("move_speed")),237.);
            TestEqual(TEXT("Unsaved live damage captured"),Json->GetArrayField(TEXT("patterns"))[0]->AsObject()->GetObjectField(TEXT("action"))->GetNumberField(TEXT("damage")),37.);
            TestTrue(TEXT("Errors included"),Json->GetArrayField(TEXT("errors")).Num()>0);
            TestEqual(TEXT("Label escaping roundtrips"),Json->GetStringField(TEXT("actor_label")),Enemy->GetActorLabel());
        }
        Enemy->PatternProfile->Patterns[0].Action->Damage=std::numeric_limits<float>::quiet_NaN();
        FString Second;
        TestTrue(TEXT("Repeated saves supported"),UCombatLabEditorLibrary::SaveCombatCharacterReport(Enemy,Second,Error));
        TestNotEqual(TEXT("Reports never overwrite each other"),Path,Second);
        if(FFileHelper::LoadFileToString(Text,*Second))
        {
            TSharedPtr<FJsonObject> NonFinite;
            TestTrue(TEXT("Nonfinite data remains valid JSON"),FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),NonFinite));
            if(NonFinite.IsValid())
                TestEqual(TEXT("NaN is represented explicitly"),NonFinite->GetArrayField(TEXT("patterns"))[0]->AsObject()->GetObjectField(TEXT("action"))->GetStringField(TEXT("damage")),FString(TEXT("NaN")));
        }
        else AddError(TEXT("Second report was not readable"));
    }
    TestEqual(TEXT("Live setting not modified"),Enemy->EncounterProfile->MoveSpeed,237.f);
    TestFalse(TEXT("No report for empty selection"),UCombatLabEditorLibrary::SaveCombatCharacterReport(nullptr,Path,Error));
    TestTrue(TEXT("Failure clears previous output path"),Path.IsEmpty());
    TestFalse(TEXT("Failure provides reason"),Error.IsEmpty());
    World->DestroyWorld(false); return true;
}
#endif
