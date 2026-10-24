#include "SceneDirectorPlayer.h"
#include "SDirectorQTE.h"
#include "LevelSequencePlayer.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "Framework/Application/SlateApplication.h"
#include "Kismet/GameplayStatics.h"

namespace { TWeakObjectPtr<ASceneDirectorPlayer> ActiveQTEPlayer; }

void ASceneDirectorPlayer::SetDirectorPaused(bool bPaused)
{
    bDirectorPaused=bPaused;
    if(SequencePlayer&&!bManualClock){if(bPaused)SequencePlayer->Pause();else SequencePlayer->Play();}
    if(QTEView)QTEView->SetPaused(bPaused);
}

bool ASceneDirectorPlayer::StartQTE(int32 CueIndex)
{
    if(!ActiveCues.IsValidIndex(CueIndex)||QTEPrompt.IsValid())return false;
    if(ActiveQTEPlayer.IsValid()&&ActiveQTEPlayer.Get()!=this)
    {LastError=TEXT("다른 QTE가 실행 중입니다.");return false;}
    auto* Viewport=GetWorld()?GetWorld()->GetGameViewport():nullptr;
    if(!Viewport||!Controller.IsValid()||!FSlateApplication::IsInitialized())
    {LastError=TEXT("QTE 입력을 위한 게임 화면이 없습니다.");return false;}
    const auto& Cue=ActiveCues[CueIndex];
    if(!Cue.Step.QTE.Validate(LastError))return false;
    QTEPrompt=Cue.Step.Id;LastQTEOutcome=EDirectorQTEOutcome::Pending;ActiveQTEPlayer=this;
    auto& Slate=FSlateApplication::Get();QTEPreviousFocus=Slate.GetUserFocusedWidget(0);
    bQTECursor=Controller->bShowMouseCursor;bQTEIgnoreInput=Viewport->IgnoreInput();
    QTEMouseCapture=uint8(Viewport->GetMouseCaptureMode());QTEMouseLock=uint8(Viewport->GetMouseLockMode());
    bQTEHideCapture=Viewport->HideCursorDuringCapture();bQTEInputSnapshot=true;
    // Preserve the actual viewport flags; SetInputMode has no readable inverse.
    Controller->bShowMouseCursor=true;Viewport->SetIgnoreInput(true);
    Viewport->SetMouseCaptureMode(EMouseCaptureMode::NoCapture);
    Viewport->SetMouseLockMode(EMouseLockMode::DoNotLock);Viewport->SetHideCursorDuringCapture(false);
    const TWeakObjectPtr<ASceneDirectorPlayer> Weak=this;const FGuid Prompt=QTEPrompt;
    QTEView=SNew(SDirectorQTE).Settings(Cue.Step.QTE).OnCompleted_Lambda([Weak,Prompt](EDirectorQTEOutcome Outcome)
    {if(Weak.IsValid())Weak->ResolveQTE(Prompt,Outcome);});
    Viewport->AddViewportWidgetContent(QTEView.ToSharedRef(),200);
    Slate.SetUserFocus(0,QTEView,EFocusCause::SetDirectly);
    QTEView->SetPaused(bDirectorPaused||UGameplayStatics::IsGamePaused(this));
    return true;
}

void ASceneDirectorPlayer::ResolveQTE(FGuid Prompt,EDirectorQTEOutcome Outcome)
{
    if(!QTEPrompt.IsValid()||QTEPrompt!=Prompt||Outcome==EDirectorQTEOutcome::Pending)return;
    // Latch before cleanup or sound callbacks; cancellation never chooses a branch.
    LastQTEOutcome=Outcome;
    const int32 Index=ActiveCues.IndexOfByPredicate([Prompt](const FDirectorCue& C){return C.Step.Id==Prompt;});
    QTEPrompt.Invalidate();
    if(Outcome==EDirectorQTEOutcome::Cancelled){CleanupQTE(true);return;}
    if(!ActiveCues.IsValidIndex(Index)||!BranchSource||PendingBranchChoice!=Prompt)
    {LastError=TEXT("QTE 결과의 분기 대상을 찾을 수 없습니다.");StopDirector();return;}
    const auto Cue=ActiveCues[Index];
    auto* Source=BranchSource->Steps.FindByPredicate([Prompt](const FDirectorStep& S){return S.Id==Prompt;});
    if(!Source){StopDirector();return;}
    // A continued timed window contracts to the actual resolution point. This keeps
    // the very next branch cue responsive without waiting out the unused window.
    Source->QTEElapsedSeconds=FMath::Max(1.f/30.f,float(ClockSeconds-Cue.StartFrame/30.0));
    BranchResumeSeconds=(Cue.StartFrame+FMath::Max(1,FMath::RoundToInt(Source->QTEElapsedSeconds*30)))/30.0;
    BranchDecisions.Add(Prompt,Outcome==EDirectorQTEOutcome::Success?FName(TEXT("Success")):FName(TEXT("Failure")));
    AdvancedCues.Add(Index);bRebuildBranch=true;
    CleanupQTE(false);
    if(USoundBase* Sound=Outcome==EDirectorQTEOutcome::Success?Cue.Step.QTE.SuccessSound.Get():Cue.Step.QTE.FailureSound.Get())
        UGameplayStatics::PlaySound2D(this,Sound,.4f);
}

void ASceneDirectorPlayer::CleanupQTE(bool bCancel)
{
    if(bCancel&&QTEPrompt.IsValid())LastQTEOutcome=EDirectorQTEOutcome::Cancelled;
    QTEPrompt.Invalidate();
    auto* Viewport=GetWorld()?GetWorld()->GetGameViewport():nullptr;
    if(QTEView)
    {
        auto View=QTEView;QTEView.Reset();
        if(bCancel){View->Cancel();if(Viewport)Viewport->RemoveViewportWidgetContent(View.ToSharedRef());}
        else RetiringQTEViews.Add(View);
    }
    if(bQTEInputSnapshot)
    {
        if(Controller.IsValid())Controller->bShowMouseCursor=bQTECursor;
        if(Viewport)
        {
            Viewport->SetIgnoreInput(bQTEIgnoreInput);Viewport->SetMouseCaptureMode(EMouseCaptureMode(QTEMouseCapture));
            Viewport->SetMouseLockMode(EMouseLockMode(QTEMouseLock));Viewport->SetHideCursorDuringCapture(bQTEHideCapture);
        }
        if(FSlateApplication::IsInitialized())FSlateApplication::Get().SetUserFocus(0,QTEPreviousFocus.Pin(),EFocusCause::SetDirectly);
        QTEPreviousFocus.Reset();bQTEInputSnapshot=false;
    }
    if(ActiveQTEPlayer.Get()==this)ActiveQTEPlayer.Reset();
    if(bCancel)
    {
        for(auto& View:RetiringQTEViews){View->Cancel();if(Viewport)Viewport->RemoveViewportWidgetContent(View.ToSharedRef());}
        RetiringQTEViews.Reset();
    }
}

void ASceneDirectorPlayer::TickQTE()
{
    if(QTEView)QTEView->SetPaused(bDirectorPaused||UGameplayStatics::IsGamePaused(this));
    auto* Viewport=GetWorld()?GetWorld()->GetGameViewport():nullptr;
    for(int32 I=RetiringQTEViews.Num()-1;I>=0;--I)if(RetiringQTEViews[I]->IsRetired())
    {if(Viewport)Viewport->RemoveViewportWidgetContent(RetiringQTEViews[I].ToSharedRef());RetiringQTEViews.RemoveAt(I);}
}
