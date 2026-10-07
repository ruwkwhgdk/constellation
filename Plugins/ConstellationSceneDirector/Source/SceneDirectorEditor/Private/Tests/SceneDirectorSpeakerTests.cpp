#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorPlayer.h"
#include "Engine/World.h"
#include "Engine/Engine.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorSpeakerDataTest,"Constellation.SceneDirector.SpeakerData",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorSpeakerDataTest::RunTest(const FString&)
{
 auto* Table=NewObject<UDataTable>();Table->RowStruct=FDirectorSpeakerRow::StaticStruct();
 FDirectorSpeakerRow Row;Row.DisplayName=NSLOCTEXT("SpeakerTest","Unknown","???");Table->AddRow(TEXT("Girl_Unknown"),Row);
 FDirectorStep Step;Step.Type=EDirectorNodeType::Dialogue;Step.SpeakerName=FText::FromString(TEXT("Legacy"));
 TestEqual(TEXT("Legacy direct name preserved"),Step.ResolveSpeaker().ToString(),FString(TEXT("Legacy")));
 Step.SpeakerSource=EDirectorSpeakerSource::Table;Step.SpeakerRow.DataTable=Table;Step.SpeakerRow.RowName=TEXT("Girl_Unknown");
 TestTrue(TEXT("Table FText identity preserved"),Step.ResolveSpeaker().IdenticalTo(Row.DisplayName));
 Row.DisplayName=FText::FromString(TEXT("Revealed"));Table->AddRow(TEXT("Girl_Unknown"),Row);
 TestEqual(TEXT("Table edits reflected without copying"),Step.ResolveSpeaker().ToString(),FString(TEXT("Revealed")));
 Step.SpeakerSource=EDirectorSpeakerSource::None;TestTrue(TEXT("None hides even when legacy text exists"),Step.ResolveSpeaker().IsEmpty());
 auto* Asset=NewObject<USceneDirectorAsset>();
 for(auto Type:{EDirectorNodeType::Start,EDirectorNodeType::Dialogue,EDirectorNodeType::End}){FDirectorStep S;S.Type=Type;Asset->Steps.Add(S);}
 Asset->Steps[0].NextNodes={Asset->Steps[1].Id};Asset->Steps[1].NextNodes={Asset->Steps[2].Id};
 Step.Id=Asset->Steps[1].Id;Step.NextNodes=Asset->Steps[1].NextNodes;Step.DialogueText=FText::FromString(TEXT("Hello"));Asset->Steps[1]=Step;
 FDirectorSchedule Schedule;FString Error;TestTrue(TEXT("None compiles"),FSceneDirectorCompiler::Schedule(*Asset,Schedule,Error));
 auto& S=Asset->Steps[1];S.SpeakerSource=EDirectorSpeakerSource::Table;
 TestTrue(TEXT("Valid table row compiles"),FSceneDirectorCompiler::Schedule(*Asset,Schedule,Error));
 if(!TestTrue(TEXT("Compile speaker cue"),FSceneDirectorCompiler::Compile(*Asset,Error))){AddError(Error);return false;}
 Row.DisplayName=FText::FromString(TEXT("Changed after compile"));Table->AddRow(TEXT("Girl_Unknown"),Row);
 auto* World=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);World->InitializeActorsForPlay(FURL());
 auto* Runner=World->SpawnActor<ASceneDirectorPlayer>();Runner->bAutoPlay=false;Runner->Director=Asset;
 TestTrue(TEXT("Play table-backed dialogue"),Runner->PlayDirector());Runner->Tick(.1f);
 TestEqual(TEXT("Runtime reads latest table value"),Runner->CurrentSpeaker.ToString(),Row.DisplayName.ToString());
 Runner->StopDirector();GEngine->DestroyWorldContext(World);World->DestroyWorld(false);
 S.SpeakerRow.RowName=TEXT("Missing");TestFalse(TEXT("Missing row rejected"),FSceneDirectorCompiler::Schedule(*Asset,Schedule,Error));
 S.SpeakerRow.RowName=TEXT("Girl_Unknown");S.SpeakerRow.DataTable=nullptr;TestFalse(TEXT("Missing table rejected"),FSceneDirectorCompiler::Schedule(*Asset,Schedule,Error));
 auto* Wrong=NewObject<UDataTable>();Wrong->RowStruct=FTableRowBase::StaticStruct();S.SpeakerRow.DataTable=Wrong;TestFalse(TEXT("Wrong schema rejected"),FSceneDirectorCompiler::Schedule(*Asset,Schedule,Error));
 S.SpeakerSource=EDirectorSpeakerSource::Direct;S.SpeakerName=FText::FromString(TEXT("  "));TestTrue(TEXT("Blank direct name hides"),S.ResolveSpeaker().IsEmpty());
 return true;
}
#endif
