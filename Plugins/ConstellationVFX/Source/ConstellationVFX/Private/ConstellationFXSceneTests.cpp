#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "ConstellationGlass.h"
#include "ConstellationFXActor.h"
#include "ConstellationSceneFXAction.h"
#include "SceneDirectorPlayer.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorAsset.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFXScenePlaybackTest,"Constellation.VFX.ScenePlayback",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FFXScenePlaybackTest::RunTest(const FString&){
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());
 W->SpawnActor<APlayerController>();auto* R=W->SpawnActor<ASceneDirectorPlayer>();R->bAutoPlay=false;auto* Glass=W->SpawnActor<AConstellationGlass>();
 auto* A=NewObject<USceneDirectorAsset>();A->Steps.SetNum(6);auto& S=A->Steps;
 S[0].Type=EDirectorNodeType::Start;S[1].Type=EDirectorNodeType::BindNPC;S[1].Role=TEXT("Glass");S[1].ActorClass=AConstellationGlass::StaticClass();S[1].ActorSource=EDirectorActorSource::Object;S[1].ObjectKey=TEXT("ExistingGlass");
 for(int I:{2,3}){S[I].Type=EDirectorNodeType::GameAction;S[I].ActionKey=TEXT("FX");S[I].ActionTarget=TEXT("Glass");}S[2].ActionParameters.Identifier=TEXT("GlassBreak");S[3].ActionParameters.Identifier=TEXT("SwordParry");
 S[4].Type=EDirectorNodeType::Wait;S[4].Duration=1;S[5].Type=EDirectorNodeType::End;for(int I=0;I<5;++I)S[I].NextNodes={S[I+1].Id};
 FDirectorObjectEntry O;O.Key=TEXT("ExistingGlass");O.ActorClass=AConstellationGlass::StaticClass();A->Objects.Add(O);FDirectorActionEntry E;E.Key=TEXT("FX");E.ActionClass=UConstellationSceneFXAction::StaticClass();A->Actions.Add(E);
 FString Error;TestTrue(TEXT("VFX graph compiles"),FSceneDirectorCompiler::Compile(*A,Error));R->Director=A;R->ObjectBindings.Add(TEXT("ExistingGlass"),Glass);
 auto Count=[&](){int N=0;for(TActorIterator<AConstellationFXActor> It(W);It;++It)if(It->GetOwner()==R&&!It->IsActorBeingDestroyed())++N;return N;};
 TestTrue(TEXT("Actual director starts"),R->PlayDirector());TestTrue(TEXT("Action broke glass"),Glass->bBroken);TestEqual(TEXT("Scene spawned visible effect"),Count(),1);R->StopDirector();TestFalse(TEXT("Abort restores pane"),Glass->bBroken);TestEqual(TEXT("Abort clears scene effects"),Count(),0);
 TestTrue(TEXT("Actual director restarts"),R->PlayDirector());R->Tick(2);TestFalse(TEXT("Natural completion"),R->IsDirectorPlaying());TestTrue(TEXT("Completed break persists"),Glass->bBroken);TestEqual(TEXT("Complete clears scene effects"),Count(),0);
 TestTrue(TEXT("Repeat on already broken glass"),R->PlayDirector());R->StopDirector();TestTrue(TEXT("Repeat abort preserves existing break"),Glass->bBroken);
 GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
#endif
