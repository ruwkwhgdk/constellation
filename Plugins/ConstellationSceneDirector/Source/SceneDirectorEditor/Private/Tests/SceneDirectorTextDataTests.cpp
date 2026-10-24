#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorPlayer.h"
#include "SceneDirectorGraph.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "UObject/UnrealType.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorTextDataTest,"Constellation.SceneDirector.TextData",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorTextDataTest::RunTest(const FString&)
{
    auto* Source=LoadObject<UDataTable>(nullptr,TEXT("/Game/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData"));
    if(!TestNotNull(TEXT("Existing sequence string DataTable"),Source))return false;
    auto* Table=DuplicateObject<UDataTable>(Source,GetTransientPackage());
    const auto Names=Table->GetRowNames();
    if(!TestTrue(TEXT("Existing string rows"),!Names.IsEmpty()))return false;
    FTextProperty* TextProperty=nullptr;
    for(TFieldIterator<FTextProperty> It(Table->GetRowStruct());It;++It){TextProperty=*It;break;}
    if(!TestNotNull(TEXT("User defined Description FText property"),TextProperty))return false;
    auto* Row=Table->FindRowUnchecked(Names[0]);
    const FText Original=NSLOCTEXT("DirectorTextTest","Original","Original dialogue");
    TextProperty->SetPropertyValue_InContainer(Row,Original);

    auto* Asset=NewObject<USceneDirectorAsset>();
    for(auto Type:{EDirectorNodeType::Start,EDirectorNodeType::Dialogue,EDirectorNodeType::End}){FDirectorStep Step;Step.Type=Type;Asset->Steps.Add(Step);}
    Asset->Steps[0].NextNodes={Asset->Steps[1].Id};Asset->Steps[1].NextNodes={Asset->Steps[2].Id};
    auto& Step=Asset->Steps[1];Step.DialogueText=FText::FromString(TEXT("Legacy direct dialogue"));
    FDirectorSchedule Schedule;FString Error;
    TestEqual(TEXT("Legacy direct dialogue remains"),Step.ResolveDialogue().ToString(),Step.DialogueText.ToString());
    TestTrue(TEXT("Legacy direct dialogue compiles"),FSceneDirectorCompiler::Schedule(*Asset,Schedule,Error));
    Step.DialogueRow.DataTable=Table;Step.DialogueRow.RowName=Names[0];
    TestTrue(TEXT("DataTable text preserves localization identity"),Step.ResolveDialogue().IdenticalTo(Original));
    if(!TestTrue(TEXT("Compile table backed dialogue"),FSceneDirectorCompiler::Compile(*Asset,Error))){AddError(Error);return false;}
    const FText Edited=NSLOCTEXT("DirectorTextTest","Edited","Edited after compile");
    TextProperty->SetPropertyValue_InContainer(Row,Edited);
    TestTrue(TEXT("Table edits apply without copying"),Step.ResolveDialogue().IdenticalTo(Edited));
    TestTrue(TEXT("Compiled cues retain live row references"),Asset->Cues.ContainsByPredicate([&](const FDirectorCue& Cue){return Cue.Step.Type==EDirectorNodeType::Dialogue&&Cue.Step.ResolveDialogue().IdenticalTo(Edited);}));
    auto* Node=NewObject<USceneDirectorGraphNode>();Node->Step=Step;
    TestTrue(TEXT("Graph title resolves edited text"),Node->GetNodeTitle(ENodeTitleType::FullTitle).ToString().Contains(Edited.ToString()));
    auto* World=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);World->InitializeActorsForPlay(FURL());
    auto* Runner=World->SpawnActor<ASceneDirectorPlayer>();Runner->bAutoPlay=false;Runner->Director=Asset;
    TestTrue(TEXT("Play table backed dialogue"),Runner->PlayDirector());Runner->Tick(.1f);
    TestTrue(TEXT("Runtime resolves table edits after compile"),Runner->CurrentDialogue.IdenticalTo(Edited));
    Runner->StopDirector();GEngine->DestroyWorldContext(World);World->DestroyWorld(false);

    Step.DialogueRow.RowName=TEXT("Missing_Director_Text_Row");
    TestFalse(TEXT("Missing dialogue row rejected"),FSceneDirectorCompiler::Schedule(*Asset,Schedule,Error));
    TestTrue(TEXT("Invalid reference cannot silently use legacy text"),Step.ResolveDialogue().IsEmpty());
    Step.DialogueRow.RowName=NAME_None;
    TestFalse(TEXT("Table without row rejected"),FSceneDirectorCompiler::Schedule(*Asset,Schedule,Error));
    Step.DialogueRow.DataTable=nullptr;Step.DialogueRow.RowName=Names[0];
    TestFalse(TEXT("Row without table rejected"),FSceneDirectorCompiler::Schedule(*Asset,Schedule,Error));
    auto* Wrong=NewObject<UDataTable>();Wrong->RowStruct=FTableRowBase::StaticStruct();Step.DialogueRow.DataTable=Wrong;
    TestFalse(TEXT("Non-text schema rejected"),FSceneDirectorCompiler::Schedule(*Asset,Schedule,Error));
    Step.DialogueRow.DataTable=Table;

    FDirectorChoice Choice;Choice.Key=TEXT("Inspect");Choice.Text=FText::FromString(TEXT("Legacy choice"));Choice.DisabledReason=FText::FromString(TEXT("Legacy reason"));
    TestEqual(TEXT("Legacy choice remains"),Choice.ResolveText().ToString(),Choice.Text.ToString());
    TestEqual(TEXT("Legacy reason remains"),Choice.ResolveDisabledReason().ToString(),Choice.DisabledReason.ToString());
    Choice.TextRow=Step.DialogueRow;Choice.DisabledReasonRow=Step.DialogueRow;
    Step.Choices={Choice};
    TestTrue(TEXT("Table backed choice compiles"),FSceneDirectorCompiler::Schedule(*Asset,Schedule,Error));
    TestTrue(TEXT("Choice preserves table FText"),Choice.ResolveText().IdenticalTo(Edited));
    TestTrue(TEXT("Reason preserves table FText"),Choice.ResolveDisabledReason().IdenticalTo(Edited));
    TextProperty->SetPropertyValue_InContainer(Row,Original);
    TestTrue(TEXT("Choice reflects later row edits"),Choice.ResolveText().IdenticalTo(Original));
    TestTrue(TEXT("Reason reflects later row edits"),Choice.ResolveDisabledReason().IdenticalTo(Original));
    FDirectorChoice Other=Choice;Other.Key=TEXT("Leave");Step.Choices.Add(Other);
    TestTrue(TEXT("Compile table backed runtime choices"),FSceneDirectorCompiler::Compile(*Asset,Error));
    TextProperty->SetPropertyValue_InContainer(Row,Edited);
    World=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);World->InitializeActorsForPlay(FURL());
    Runner=World->SpawnActor<ASceneDirectorPlayer>();Runner->bAutoPlay=false;Runner->Director=Asset;
    TestTrue(TEXT("Play table backed choices"),Runner->PlayDirector());Runner->Tick(5);
    TestTrue(TEXT("Runtime waits for choices"),Runner->IsWaitingForChoice());
    if(TestEqual(TEXT("Runtime choice count"),Runner->CurrentChoices.Num(),2))
    {
        TestTrue(TEXT("Runtime choice reads edited row"),Runner->CurrentChoices[0].Text.IdenticalTo(Edited));
        TestTrue(TEXT("Runtime reason reads edited row"),Runner->CurrentChoices[0].DisabledReason.IdenticalTo(Edited));
        const FText Override=NSLOCTEXT("DirectorTextTest","RuntimeReason","Explicit runtime reason");
        TestTrue(TEXT("Runtime reason can override a row"),Runner->SetChoiceAvailability(Choice.Key,false,Override));
        TestTrue(TEXT("Runtime reason override is resolved"),Runner->CurrentChoices[0].ResolveDisabledReason().IdenticalTo(Override));
        TestTrue(TEXT("Authored reason reference unchanged"),Step.Choices[0].DisabledReasonRow.DataTable==Table);
    }
    Runner->StopDirector();GEngine->DestroyWorldContext(World);World->DestroyWorld(false);
    Step.Choices[0].TextRow.RowName=TEXT("Missing_Director_Text_Row");
    TestFalse(TEXT("Missing choice row rejected"),FSceneDirectorCompiler::Schedule(*Asset,Schedule,Error));
    Step.Choices[0]=Choice;Step.Choices[0].DisabledReasonRow.RowName=TEXT("Missing_Director_Text_Row");
    TestFalse(TEXT("Missing reason row rejected"),FSceneDirectorCompiler::Schedule(*Asset,Schedule,Error));
    return true;
}
#endif
