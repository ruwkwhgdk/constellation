#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorDetails.h"
#include "SceneDirectorNodeMenu.h"
#include "GameFramework/Character.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorPlayer.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/HUD.h"
#include "Camera/CameraActor.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorSplitControls,"Constellation.SceneDirector.SplitControls",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorSplitControls::RunTest(const FString&)
{
 auto* A=NewObject<USceneDirectorAsset>();
 // Appended enum values preserve existing asset ordinals.
 for(auto T:{EDirectorNodeType::Start,EDirectorNodeType(25),EDirectorNodeType::Wait,EDirectorNodeType(24),EDirectorNodeType(26),EDirectorNodeType(27),EDirectorNodeType::Wait,EDirectorNodeType(25),EDirectorNodeType::Wait,EDirectorNodeType::End})
 {FDirectorStep S;S.Type=T;S.Duration=1;S.bHidePlayer=true;S.bHideHUD=true;S.bLockInput=true;A->Steps.Add(S);}
 A->Steps[7].bLockInput=false;for(int I=0;I<A->Steps.Num()-1;++I)A->Steps[I].NextNodes={A->Steps[I+1].Id};
 FString Error;if(!TestTrue(TEXT("Independent control nodes compile"),FSceneDirectorCompiler::Compile(*A,Error))){AddError(Error);return false;}
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());
 auto* PC=W->SpawnActor<APlayerController>();auto* Pawn=W->SpawnActor<APawn>();PC->Possess(Pawn);PC->ClientSetHUD(AHUD::StaticClass());
 auto* R=W->SpawnActor<ASceneDirectorPlayer>();R->bAutoPlay=false;R->Director=A;TestTrue(TEXT("Play"),R->PlayDirector());
 TestTrue(TEXT("Input locked"),PC->IsMoveInputIgnored());TestFalse(TEXT("Input lock does not hide player"),Pawn->IsHidden());
 if(PC->GetHUD())TestTrue(TEXT("Input lock does not hide HUD"),PC->GetHUD()->bShowHUD);
 R->Tick(1.1f);TestTrue(TEXT("Visibility node hides player"),Pawn->IsHidden());if(PC->GetHUD())TestFalse(TEXT("HUD node hides HUD"),PC->GetHUD()->bShowHUD);
 TestTrue(TEXT("Camera return leaves input locked"),PC->IsMoveInputIgnored());TestTrue(TEXT("Camera return leaves player hidden"),Pawn->IsHidden());
 R->Tick(2.f);TestFalse(TEXT("Unlock node releases input"),PC->IsMoveInputIgnored());TestTrue(TEXT("Unlock does not show player"),Pawn->IsHidden());if(PC->GetHUD())TestFalse(TEXT("Unlock does not show HUD"),PC->GetHUD()->bShowHUD);
 R->StopDirector();TestFalse(TEXT("Cancel restores player"),Pawn->IsHidden());if(PC->GetHUD())TestTrue(TEXT("Cancel restores HUD"),PC->GetHUD()->bShowHUD);
 GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorControlMigration,"Constellation.SceneDirector.ControlMigration",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorControlMigration::RunTest(const FString&)
{
 auto* A=NewObject<USceneDirectorAsset>();for(auto T:{EDirectorNodeType::Start,EDirectorNodeType::CinematicMode,EDirectorNodeType::Wait,EDirectorNodeType::GameplayReturn,EDirectorNodeType::End}){FDirectorStep S;S.Type=T;S.bHidePlayer=true;S.Duration=1;A->Steps.Add(S);}
 for(int I=0;I<4;++I)A->Steps[I].NextNodes={A->Steps[I+1].Id};
 FDirectorSchedule Before,After;FString E;TestTrue(TEXT("Old schedule"),FSceneDirectorCompiler::Schedule(*A,Before,E));
 TestTrue(TEXT("Migrated"),A->UpgradeControlNodes());TestFalse(TEXT("Idempotent"),A->UpgradeControlNodes());TestTrue(TEXT("New schedule"),FSceneDirectorCompiler::Schedule(*A,After,E));TestEqual(TEXT("Same total time"),After.EndFrame,Before.EndFrame);
 TestFalse(TEXT("No compound controls remain"),A->Steps.ContainsByPredicate([](const FDirectorStep& S){return S.Type==EDirectorNodeType::CinematicMode||S.Type==EDirectorNodeType::GameplayReturn;}));return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorUnifiedVariables,"Constellation.SceneDirector.UnifiedVariables",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorUnifiedVariables::RunTest(const FString&)
{
 auto* A=NewObject<USceneDirectorAsset>();FDirectorBoolEntry B;B.Key=TEXT("Seen");B.Value=true;A->BoolVariables.Add(B);FDirectorIntEntry N;N.Key=TEXT("Count");N.Value=3;A->IntVariables.Add(N);
 A->RefreshVariableEntries();TestEqual(TEXT("Both types in one list"),A->Variables.Num(),2);
 A->Variables[1].IntValue=9;A->ApplyVariableEntries();TestEqual(TEXT("Integer update preserved"),A->IntVariables[0].Value,9);TestTrue(TEXT("Boolean preserved"),A->BoolVariables[0].Value);
 A->Variables.Reset();A->ApplyVariableEntries();A->RefreshVariableEntries();TestTrue(TEXT("Deleting all variables stays deleted"),A->Variables.IsEmpty());return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorReferenceLists,"Constellation.SceneDirector.ReferenceLists",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorReferenceLists::RunTest(const FString&)
{
 auto* A=NewObject<USceneDirectorAsset>();FDirectorStep NPC;NPC.Type=EDirectorNodeType::BindNPC;NPC.ActorClass=ACharacter::StaticClass();NPC.Role=TEXT("Girl");A->Steps.Add(NPC);NPC.ActorClass=AActor::StaticClass();NPC.Role=TEXT("SequenceManager");A->Steps.Add(NPC);
 const auto Characters=DirectorAuthoring::ReferenceKeys(*A,TEXT("NPC"));TestTrue(TEXT("Character available"),Characters.Contains(TEXT("Girl")));TestFalse(TEXT("Manager excluded from NPC list"),Characters.Contains(TEXT("SequenceManager")));TestTrue(TEXT("Manager remains valid action target"),DirectorAuthoring::ReferenceKeys(*A,TEXT("Actor")).Contains(TEXT("SequenceManager")));
 const auto Menu=DirectorNodeMenuEntries();TestFalse(TEXT("Compound mode not creatable"),Menu.ContainsByPredicate([](const FDirectorNodeMenuEntry& E){return E.Type==EDirectorNodeType::CinematicMode||E.Type==EDirectorNodeType::GameplayReturn;}));return true;
}
#endif
