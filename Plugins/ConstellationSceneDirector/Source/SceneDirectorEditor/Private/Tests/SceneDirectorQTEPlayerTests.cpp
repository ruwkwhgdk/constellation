#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorPlayer.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorLibrary.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "Widgets/SOverlay.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorQTEPlayerTest,"Constellation.SceneDirector.QTE.PlayerLifecycle",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorQTEPlayerTest::RunTest(const FString&)
{
    UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);
    auto& Context=GEngine->CreateNewWorldContext(EWorldType::Game);Context.SetCurrentWorld(W);
    auto* Viewport=NewObject<UGameViewportClient>(GEngine);Context.GameViewport=Viewport;
    auto Overlay=SNew(SOverlay);Viewport->SetViewportOverlayWidget(nullptr,Overlay);
    W->InitializeActorsForPlay(FURL());auto* PC=W->SpawnActor<APlayerController>();
    auto* Runner=W->SpawnActor<ASceneDirectorPlayer>();Runner->bAutoPlay=false;
    auto* Asset=NewObject<USceneDirectorAsset>();Asset->Steps.SetNum(5);auto& S=Asset->Steps;
    S[0].Type=EDirectorNodeType::Start;S[1].Type=EDirectorNodeType::QTE;S[1].QTE.bTimed=false;
    S[2].Type=S[3].Type=EDirectorNodeType::SetInt;S[2].IntKey=S[3].IntKey=TEXT("Outcome");S[2].IntValue=1;S[3].IntValue=-1;
    S[4].Type=EDirectorNodeType::End;S[0].NextNodes={S[1].Id};S[1].ChoiceTargets.Add(TEXT("Success"),S[2].Id);S[1].ChoiceTargets.Add(TEXT("Failure"),S[3].Id);S[2].NextNodes=S[3].NextNodes={S[4].Id};
    FDirectorIntEntry Entry;Entry.Key=TEXT("Outcome");Asset->IntVariables.Add(Entry);Runner->Director=Asset;
    FString Error;const bool Compiled=FSceneDirectorCompiler::Compile(*Asset,Error);TestTrue(TEXT("Compile QTE fixture"),Compiled);
    if(!Compiled)AddError(Error);
    if(Compiled)for(auto Outcome:{EDirectorQTEOutcome::Success,EDirectorQTEOutcome::Failure})
    {
        PC->bShowMouseCursor=false;Viewport->SetIgnoreInput(false);Viewport->SetMouseCaptureMode(EMouseCaptureMode::CaptureDuringMouseDown);Viewport->SetMouseLockMode(EMouseLockMode::LockAlways);
        TestTrue(TEXT("Play real QTE prefix"),Runner->PlayDirector());TestTrue(TEXT("Prompt waits"),Runner->IsWaitingForQTE());
        TestTrue(TEXT("Cursor displayed"),PC->bShowMouseCursor);TestTrue(TEXT("Gameplay input isolated"),Viewport->IgnoreInput());
        const double Clock=Runner->ClockSeconds;Runner->Tick(10);TestEqual(TEXT("Hold does not advance scene"),Runner->ClockSeconds,Clock);
        TestFalse(TEXT("Review injection rejects non-PIE world"),USceneDirectorLibrary::ResolveQTEForReview(Runner,true));
        TestTrue(TEXT("Rejected review injection leaves prompt pending"),Runner->IsWaitingForQTE());
        const FGuid Prompt=Runner->QTEPrompt;
        W->WorldType=EWorldType::PIE;
        TestTrue(TEXT("PIE review injection resolves requested outcome"),USceneDirectorLibrary::ResolveQTEForReview(Runner,Outcome==EDirectorQTEOutcome::Success));
        TestTrue(TEXT("Review overlay explicitly removed"),Runner->RetiringQTEViews.IsEmpty());
        TestFalse(TEXT("Duplicate review injection rejected"),USceneDirectorLibrary::ResolveQTEForReview(Runner,true));
        W->WorldType=EWorldType::Game;
        Runner->ResolveQTE(Prompt,Outcome==EDirectorQTEOutcome::Success?EDirectorQTEOutcome::Failure:EDirectorQTEOutcome::Success);
        TestEqual(TEXT("Result latched exactly once"),Runner->GetLastQTEOutcome(),Outcome);
        TestFalse(TEXT("Cursor restored before exit visual completes"),PC->bShowMouseCursor);TestFalse(TEXT("Input restored"),Viewport->IgnoreInput());
        TestEqual(TEXT("Actual capture policy restored"),Viewport->GetMouseCaptureMode(),EMouseCaptureMode::CaptureDuringMouseDown);
        TestEqual(TEXT("Actual lock policy restored"),Viewport->GetMouseLockMode(),EMouseLockMode::LockAlways);
        Runner->Tick(.01f);TestEqual(TEXT("Real branch control executed"),Runner->IntValues.FindRef(TEXT("Outcome")),Outcome==EDirectorQTEOutcome::Success?1:-1);
        Runner->StopDirector();
    }
    if(Compiled)
    {
        TestTrue(TEXT("Repeat after stop"),Runner->PlayDirector());Runner->StopDirector();
        TestFalse(TEXT("Cancellation clears pending prompt"),Runner->IsWaitingForQTE());
        TestEqual(TEXT("Cancellation never chooses failure"),Runner->IntValues.FindRef(TEXT("Outcome")),0);
        TestFalse(TEXT("Cancellation restores cursor"),PC->bShowMouseCursor);
    }
    Runner->StopDirector();Context.GameViewport=nullptr;GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
#endif
