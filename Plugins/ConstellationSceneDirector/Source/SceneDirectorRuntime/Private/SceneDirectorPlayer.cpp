#include "SceneDirectorPlayer.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Blueprint/UserWidget.h"
#include "SceneDirectorBranching.h"
#include "SceneDirectorCompiler.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "SDirectorDialogue.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/Texture2D.h"
#include "SceneDirectorPerformance.h"
#include "SceneDirectorNodeTypes.h"
#include "Components/AudioComponent.h"
#include "Components/PrimitiveComponent.h"
#include "GameFramework/HUD.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/GameViewportClient.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Input/SButton.h"
#include "InputCoreTypes.h"
#include "Styling/CoreStyle.h"
#include "SceneDirectorAsset.h"
#include "LevelSequencePlayer.h"
#include "LevelSequenceActor.h"
#include "DefaultLevelSequenceInstanceData.h"
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"
#include "EngineUtils.h"
ASceneDirectorPlayer::ASceneDirectorPlayer()
{
    PrimaryActorTick.bCanEverTick=true;PrimaryActorTick.TickGroup=TG_PostUpdateWork;
    static ConstructorHelpers::FObjectFinder<UTexture2D> Background(TEXT("/Game/Constellation/UI/Dialogue/T_Dialogue_Background"));
    static ConstructorHelpers::FObjectFinder<UTexture2D> Continue(TEXT("/Game/Constellation/UI/Dialogue/T_Dialogue_Continue"));
    static ConstructorHelpers::FObjectFinder<UTexture2D> SpeakerBackground(TEXT("/Game/Constellation/UI/Dialogue/T_Dialogue_SpeakerBackground"));
    DialogueBackground=Background.Object;DialogueContinue=Continue.Object;DialogueSpeakerBackground=SpeakerBackground.Object;
    static ConstructorHelpers::FObjectFinder<UTexture2D> ChoiceFocusedBG(TEXT("/Game/Constellation/UI/Dialogue/T_Dialogue_ChoiceFocusedBG"));
    DialogueChoiceStyle.FocusedBG=ChoiceFocusedBG.Object;
    static ConstructorHelpers::FObjectFinder<UTexture2D> ChoiceFocusedStroke(TEXT("/Game/Constellation/UI/Dialogue/T_Dialogue_ChoiceFocusedStroke"));
    DialogueChoiceStyle.FocusedStroke=ChoiceFocusedStroke.Object;
    static ConstructorHelpers::FObjectFinder<UTexture2D> ChoiceIdleBG(TEXT("/Game/Constellation/UI/Dialogue/T_Dialogue_ChoiceIdleBG"));
    DialogueChoiceStyle.IdleBG=ChoiceIdleBG.Object;
    static ConstructorHelpers::FObjectFinder<UTexture2D> ChoiceIdleStroke(TEXT("/Game/Constellation/UI/Dialogue/T_Dialogue_ChoiceIdleStroke"));
    DialogueChoiceStyle.IdleStroke=ChoiceIdleStroke.Object;
    static ConstructorHelpers::FObjectFinder<UTexture2D> ChoiceCursor(TEXT("/Game/Constellation/UI/Dialogue/T_Dialogue_ChoiceCursor"));
    DialogueChoiceStyle.Cursor=ChoiceCursor.Object;
}
ASceneDirectorPlayer::~ASceneDirectorPlayer()=default;
void ASceneDirectorPlayer::BeginPlay(){Super::BeginPlay();if(bAutoPlay)PlayDirector();}
void ASceneDirectorPlayer::EndPlay(const EEndPlayReason::Type Reason){StopDirector();Super::EndPlay(Reason);}
bool ASceneDirectorPlayer::PlayDirector()
{
    if(bExecutingAction)return false; // An action may stop this session, but cannot replace it during its callback.
    LastError.Reset();
    if(SequencePlayer){LastError=TEXT("이미 실행 중입니다.");return false;}
    USceneDirectorAsset* Selected=Director?(EventKey.IsNone()?Director.Get():Director->FindEvent(EventKey)):nullptr;
    if(!Selected||!Selected->GeneratedSequence||Selected->bNeedsCompile){LastError=TEXT("연출 그래프를 지정하고 생성 및 저장을 먼저 실행하세요.");return false;}
    UWorld* World=GetWorld();
    if(!World||!World->IsGameWorld()){LastError=TEXT("게임 또는 PIE에서 실행하세요.");return false;}
    for(TActorIterator<ASceneDirectorPlayer> It(World);It;++It)
        if(*It!=this && It->IsDirectorPlaying()){LastError=TEXT("다른 연출이 실행 중입니다.");return false;}
    bReturningToGameplay=false;bPlayerHandedBack=false;GameplayPose.Reset();
    RuntimeSource=Selected;OriginDelta=FTransform::Identity;
    if(bUseOrigin)
    {
        if(OriginActor&&OriginActor->GetWorld()!=World){LastError=TEXT("기준 Actor가 다른 월드에 있습니다.");return false;}
        auto Target=OriginActor?OriginActor->GetActorTransform():OriginTransform;auto Source=Director->AuthoringOrigin;
        if(!Target.IsValid()||!Source.IsValid()){LastError=TEXT("기준 Transform이 유효하지 않습니다.");return false;}
        Target.SetScale3D(FVector::OneVector);Source.SetScale3D(FVector::OneVector);OriginDelta=Source.Inverse()*Target;
    }
    TSet<FName> ObjectKeys;
    for(const auto& Entry:Selected->Objects){if(Entry.Key.IsNone()||ObjectKeys.Contains(Entry.Key)){LastError=TEXT("오브젝트 Key가 비어 있거나 중복됩니다.");return false;}ObjectKeys.Add(Entry.Key);}
    for(const auto& S:Selected->Steps)if(S.Type==EDirectorNodeType::BindNPC&&S.ActorSource==EDirectorActorSource::Object&&!ResolveObject(S.ObjectKey)){LastError=TEXT("등록 오브젝트를 찾을 수 없습니다: ")+S.ObjectKey.ToString();return false;}
    for(const auto& C:Selected->Cameras)if(!C.ObjectKey.IsNone()&&!Cast<ACameraActor>(ResolveObject(C.ObjectKey))){LastError=TEXT("등록 카메라를 찾을 수 없습니다: ")+C.ObjectKey.ToString();return false;}
    BoolValues.Reset();for(const auto& Entry:Director->BoolVariables)BoolValues.Add(Entry.Key,Entry.Value);
    IntValues.Reset();for(const auto& Entry:Director->IntVariables)IntValues.Add(Entry.Key,InitialIntOverrides.Contains(Entry.Key)?InitialIntOverrides[Entry.Key]:Entry.Value);
    for(const auto& Entry:InitialBoolOverrides)
    {if(!BoolValues.Contains(Entry.Key)){LastError=TEXT("초기값 변수 Key를 찾을 수 없습니다: ")+Entry.Key.ToString();return false;}BoolValues[Entry.Key]=Entry.Value;}
    if(DirectorBranching::HasBranches(*Selected))
    {
        BranchSource=Selected;BranchInitialOverrides=InitialBoolOverrides;BranchDecisions.Reset();
        if(!CompileBranchPrefix()){StopDirector();return false;}
        Selected=BranchPrefix;
    }
    ActiveActions.Reset();for(const auto& A:Selected->Actions)ActiveActions.Add(A.Key,A.ActionClass);ActionResults.Reset();
    ActiveCues=Selected->Cues;LastChoiceKey=NAME_None;ChoiceInputFrame=MAX_uint64;CurrentChoices.Reset();
    Controller=World->GetFirstPlayerController();
    TMap<FName,AActor*> Existing;
    for(const auto& Cue:ActiveCues)if(!BranchSource&&Cue.Step.Type==EDirectorNodeType::BindNPC)
    {
        const auto& S=Cue.Step;AActor* Found=nullptr;
        if(S.ActorSource==EDirectorActorSource::Player){if(Controller.IsValid())Found=Controller->GetPawn();}
        else if(S.ActorSource==EDirectorActorSource::Object)Found=ResolveObject(S.ObjectKey);
        else for(TActorIterator<AActor> It(World);It;++It)if(It->ActorHasTag(S.ActorTag))
        {if(Found){LastError=TEXT("Actor 태그가 중복됩니다: ")+S.ActorTag.ToString();StopDirector();return false;}Found=*It;}
        if(!Found||!Found->IsA(S.ActorClass)){LastError=TEXT("기존 캐릭터를 찾을 수 없거나 BP가 다릅니다: ")+S.Role.ToString();StopDirector();return false;}
        if(BoundActors.Contains(Found)){LastError=TEXT("같은 실제 캐릭터를 여러 NPC Key에 연결할 수 없습니다.");StopDirector();return false;}
        Existing.Add(S.Role,Found);BoundActors.Add(Found);OriginalTransforms.Add(Found->GetActorTransform());
    }
    if(!BranchSource)for(const auto& C:Selected->Cameras)if(!C.ObjectKey.IsNone())
    {
        auto* Camera=ResolveObject(C.ObjectKey);
        if(BoundActors.Contains(Camera)){LastError=TEXT("같은 실제 Actor를 여러 NPC/카메라 Key에 연결할 수 없습니다.");StopDirector();return false;}
        BoundActors.Add(Camera);OriginalTransforms.Add(Camera->GetActorTransform());
    }
    if(Controller.IsValid()){OriginalViewTarget=Controller->GetViewTarget();OriginalControlRotation=Controller->GetControlRotation();}
    FMovieSceneSequencePlaybackSettings Settings;
    Settings.FinishCompletionStateOverride=EMovieSceneCompletionModeOverride::ForceRestoreState;
    ALevelSequenceActor* Out=nullptr;
    SequencePlayer=ULevelSequencePlayer::CreateLevelSequencePlayer(World,Selected->GeneratedSequence,Settings,Out);
    SequenceActor=Out;
    if(!SequencePlayer){LastError=TEXT("시퀀스 재생기를 만들 수 없습니다.");StopDirector();return false;}
    ApplyOrigin();
    SequencePlayer->OnFinished.AddDynamic(this,&ASceneDirectorPlayer::OnFinished);
    ActiveCameraBindings=Selected->CameraBindings;ActiveNPCBindings=Selected->NPCBindings;
    for(const auto& Pair:Existing)SequenceActor->SetBinding(UE::MovieScene::FRelativeObjectBindingID(ActiveNPCBindings.FindChecked(Pair.Key)),{Pair.Value},false);
    if(!BranchSource)for(const auto& C:Selected->Cameras)if(!C.ObjectKey.IsNone()&&ActiveCameraBindings.Contains(C.Key))
    {auto* Camera=ResolveObject(C.ObjectKey);SequenceActor->SetBinding(UE::MovieScene::FRelativeObjectBindingID(ActiveCameraBindings.FindChecked(C.Key)),{Camera},false);if(!BoundActors.Contains(Camera)){BoundActors.Add(Camera);OriginalTransforms.Add(Camera->GetActorTransform());}}
    if(BranchSource){BindBranchActors();if(!PrepareBranchActors(0)){StopDirector();return false;}}
    bManualClock=BranchSource||ActiveCues.ContainsByPredicate([](const FDirectorCue& C){return DirectorNodes::IsCue(C.Step.Type);});
    ClockSeconds=0;WaitingCue=DialogueCue=INDEX_NONE;AdvancedCues.Reset();FiredControls.Reset();Performance=MakeUnique<FDirectorPerformance>();
    SequencePlayer->Play();if(bManualClock)SequencePlayer->Pause();
    if(bManualClock)
    {
        const TWeakObjectPtr<ASceneDirectorPlayer> Weak=this;
        if(GEngine&&GEngine->GameViewport&&Controller.IsValid()&&ActiveCues.ContainsByPredicate([](const FDirectorCue& C){return C.Step.Type==EDirectorNodeType::Dialogue;}))
        {
            bOriginalCursor=Controller->bShowMouseCursor;bHasCursorSnapshot=true;Controller->bShowMouseCursor=true;
            DialogueWidget=SNew(SBox).Padding(36,24)
                [SAssignNew(DialogueView,SDirectorDialogue).Position_Lambda([Weak]{return Weak.IsValid()?Weak->CurrentDialoguePosition:EDirectorDialoguePosition::Bottom;}).Background(DialogueBackground).Continue(DialogueContinue).SpeakerBackground(DialogueSpeakerBackground)
                 .ChoiceStyle(DialogueChoiceStyle)
                 .Choices_Lambda([Weak]{return Weak.IsValid()&&Weak->IsWaitingForChoice()?Weak->CurrentChoices:TArray<FDirectorChoice>();})
                 .ChoicePrompt_Lambda([Weak]{return Weak.IsValid()?Weak->ChoicePrompt:FGuid();})
                 .OnChoice_Lambda([Weak](FName Key){if(Weak.IsValid())Weak->SelectDialogueChoice(Key);})
                 .Speaker_Lambda([Weak]{return Weak.IsValid()?Weak->CurrentSpeaker:FText::GetEmpty();})
                 .Dialogue_Lambda([Weak]{return Weak.IsValid()?Weak->CurrentDialogue:FText::GetEmpty();})
                 .Waiting_Lambda([Weak]{return Weak.IsValid()&&Weak->IsWaitingForDialogue();})
                 .OnAdvance_Lambda([Weak]{if(Weak.IsValid())Weak->AdvanceDialogue();})];
            GEngine->GameViewport->AddViewportWidgetContent(DialogueWidget.ToSharedRef(),100);
        }
        EvaluateConversation(0);
    }
    ControlCharacters();
    return SequencePlayer!=nullptr;
}
void ASceneDirectorPlayer::StopDirector()
{
    const bool WasPlaying=SequencePlayer!=nullptr;const bool Completed=bNaturalFinish;bNaturalFinish=false;
    RestoreStandIns();
    if(Performance){Performance->Reset();Performance.Reset();}
    if(VoiceComponent){VoiceComponent->Stop();VoiceComponent->DestroyComponent();VoiceComponent=nullptr;}
    if(DialogueWidget&&GEngine&&GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(DialogueWidget.ToSharedRef());DialogueWidget.Reset();DialogueView.Reset();CurrentChoices.Reset();ChoicePrompt.Invalidate();
    CurrentSpeaker=CurrentDialogue=FText::GetEmpty();WaitingCue=DialogueCue=INDEX_NONE;
    RestoreControls();
    if(Controller.IsValid()&&bHasCursorSnapshot)Controller->bShowMouseCursor=bOriginalCursor;bHasCursorSnapshot=false;
    if(SequencePlayer){SequencePlayer->OnFinished.RemoveDynamic(this,&ASceneDirectorPlayer::OnFinished);SequencePlayer->Stop();SequencePlayer=nullptr;}
    if(Controller.IsValid()&&OriginalViewTarget.IsValid())Controller->SetViewTarget(OriginalViewTarget.Get());
    Controller.Reset();OriginalViewTarget.Reset();ActiveNPCBindings.Reset();ActiveCameraBindings.Reset();
    if(IsValid(SequenceActor))SequenceActor->Destroy();SequenceActor=nullptr;
    for(int32 I=0;I<BoundActors.Num();++I)if(IsValid(BoundActors[I])&&!BoundActors[I]->GetActorTransform().Equals(OriginalTransforms[I]))BoundActors[I]->SetActorTransform(OriginalTransforms[I]);
    ApplyActorDeactivations();RestoreCharacters();DeactivatedActors.Reset();
    BoundActors.Reset();OriginalTransforms.Reset();ActiveCues.Reset();ActiveActions.Reset();bManualClock=false;
    for(auto Actor:SessionOwnedActors)if(IsValid(Actor))Actor->Destroy();
    SessionOwnedActors.Reset();SessionNPCs.Reset();SessionCameras.Reset();BranchDecisions.Reset();BranchInitialOverrides.Reset();
    BranchPrefix=nullptr;BranchSource=nullptr;PendingBranchChoice.Invalidate();bRebuildBranch=false;BranchResumeSeconds=0;RuntimeSource=nullptr;
    if(WasPlaying)OnDirectorStopped.Broadcast(Completed);
}
void ASceneDirectorPlayer::OnFinished(){bNaturalFinish=true;StopDirector();}
AActor* ASceneDirectorPlayer::FindNPC(FName Key) const
{
    if(!SequencePlayer)return nullptr;
    if(BranchSource){auto* Found=SessionNPCs.Find(Key);return Found&&IsValid(Found->Get())?Found->Get():nullptr;}
    const FGuid* ID=ActiveNPCBindings.Find(Key);if(!ID)return nullptr;
    for(auto Object:SequencePlayer->GetBoundObjects(UE::MovieScene::FRelativeObjectBindingID(*ID)))
        if(AActor* Actor=Cast<AActor>(Object))return Actor;
    return nullptr;
}


AActor* ASceneDirectorPlayer::FindCamera(FName Key) const
{
    if(!SequencePlayer)return nullptr;
    if(BranchSource){auto* Found=SessionCameras.Find(Key);return Found&&IsValid(Found->Get())?Found->Get():nullptr;}
    const FGuid* ID=ActiveCameraBindings.Find(Key);if(!ID)return nullptr;
    for(auto Object:SequencePlayer->GetBoundObjects(UE::MovieScene::FRelativeObjectBindingID(*ID)))if(auto* Actor=Cast<AActor>(Object))return Actor;
    return nullptr;
}
TArray<FString> ASceneDirectorPlayer::GetEventOptions() const
{
    TArray<FString> Options{TEXT("None")};if(!Director)return Options;
    Options.Add(Director->EventKey.ToString());for(auto Event:Director->EventGraphs)if(Event)Options.Add(Event->EventKey.ToString());return Options;
}

void ASceneDirectorPlayer::HideGameWidgets()
{
 TArray<UUserWidget*> Widgets;UWidgetBlueprintLibrary::GetAllWidgetsOfClass(this,Widgets,UUserWidget::StaticClass(),true);
 for(auto* W:Widgets)if(W&&W->GetWorld()==GetWorld()){if(!WidgetVisibility.Contains(W))WidgetVisibility.Add(W,uint8(W->GetVisibility()));W->SetVisibility(ESlateVisibility::Hidden);}
}
void ASceneDirectorPlayer::RestoreControls()
{
 bHideGameWidgets=false;for(const auto& Pair:WidgetVisibility)if(Pair.Key.IsValid())Pair.Key->SetVisibility(ESlateVisibility(Pair.Value));WidgetVisibility.Reset();
    if(Controller.IsValid())
    {
        if(bInputLocked){Controller->SetIgnoreMoveInput(false);Controller->SetIgnoreLookInput(false);}
        if(bHUDHidden&&Controller->GetHUD())Controller->GetHUD()->bShowHUD=bOriginalHUD;
    }
    if(HiddenPlayer.IsValid())HiddenPlayer->SetActorHiddenInGame(bPlayerWasHidden);HiddenPlayer.Reset();
    bInputLocked=bHUDHidden=false;
}
void ASceneDirectorPlayer::AdvanceDialogue()
{
    if(WaitingCue!=INDEX_NONE&&CurrentChoices.IsEmpty()){AdvancedCues.Add(WaitingCue);WaitingCue=INDEX_NONE;}
}
bool ASceneDirectorPlayer::SelectDialogueChoice(FName Key)
{
    if(!IsWaitingForChoice()||!CurrentChoices.ContainsByPredicate([Key](const FDirectorChoice& C){return C.Key==Key&&C.bEnabled;}))return false;
    const FGuid Id=ChoicePrompt;LastChoiceKey=Key;ChoiceInputFrame=GFrameCounter;
    if(BranchSource&&Id==PendingBranchChoice)
    {BranchDecisions.Add(Id,Key);BranchResumeSeconds=ActiveCues[WaitingCue].EndFrame/30.0;bRebuildBranch=true;}
    AdvancedCues.Add(WaitingCue);WaitingCue=INDEX_NONE;CurrentChoices.Reset();
    OnChoiceSelected.Broadcast(Id,Key);return true;
}
void ASceneDirectorPlayer::Tick(float DeltaSeconds)
{
    if(bHideGameWidgets)HideGameWidgets();
    Super::Tick(DeltaSeconds);
    if(bExecutingAction||!SequencePlayer)return;
    ControlCharacters();
    if(!bManualClock)return;
    if(bRebuildBranch){if(!RebuildBranchPlayback()){StopDirector();return;}}
    if(IsWaitingForChoice())
    {
        if(Controller.IsValid()&&DialogueView)
        {
            if(Controller->WasInputKeyJustPressed(EKeys::Up))DialogueView->MoveChoice(-1);
            if(Controller->WasInputKeyJustPressed(EKeys::Down))DialogueView->MoveChoice(1);
            if(Controller->WasInputKeyJustPressed(EKeys::Enter))DialogueView->ConfirmChoice();
        }
        return;
    }
    if(GFrameCounter!=ChoiceInputFrame&&Controller.IsValid()&&(Controller->WasInputKeyJustPressed(EKeys::SpaceBar)||Controller->WasInputKeyJustPressed(EKeys::Enter)))AdvanceDialogue();
    if(WaitingCue!=INDEX_NONE)return;
    double Next=ClockSeconds+FMath::Max(0.f,DeltaSeconds);
    for(int32 I=0;I<ActiveCues.Num();++I)
    {
        const auto& Cue=ActiveCues[I];
        if(Cue.Step.Type==EDirectorNodeType::Dialogue&&(Cue.Step.DialogueAdvance==EDirectorDialogueAdvance::Click||!Cue.Step.Choices.IsEmpty())&&!AdvancedCues.Contains(I)&&Cue.EndFrame/30.0<=Next)
        {
            // Keep evaluation strictly before the next action boundary, even after a large frame hitch.
            Next=(Cue.EndFrame-.001)/30.0;WaitingCue=I;break;
        }
    }
    const double End=SequencePlayer->GetDuration().AsSeconds();
    ClockSeconds=FMath::Min(Next,End);
    if(BranchSource&&!PrepareBranchActors(FMath::Min(ClockSeconds,End-.0001)*30.)){StopDirector();return;}
    SequencePlayer->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(FFrameTime::FromDecimal(FMath::Min(ClockSeconds,End-.0001)*30.),EUpdatePositionMethod::Play));
    EvaluateConversation(ClockSeconds);
    if(SequencePlayer&&ClockSeconds>=End)OnFinished();
}
void ASceneDirectorPlayer::EvaluateConversation(double Seconds)
{
    RememberStandIns();ControlCharacters();
    int32 NewDialogue=INDEX_NONE;const double Frame=Seconds*30;
    for(int32 I=0;I<ActiveCues.Num();++I)
    {
        const auto& Cue=ActiveCues[I];const auto& S=Cue.Step;
        if(Cue.StartFrame>Frame)continue;
        if(S.Type==EDirectorNodeType::Dialogue&&Frame<Cue.EndFrame)NewDialogue=I;
        if(S.Type==EDirectorNodeType::GameAction&&!FiredControls.Contains(I))
        {
            FiredControls.Add(I);const FDirectorStep ActionStep=S;
            if(!ExecuteGameAction(ActionStep)||!SequencePlayer)return;
        }
        if(!FiredControls.Contains(I)&&((DirectorNodes::IsCamera(S.Type)&&((S.Type!=EDirectorNodeType::CameraMove&&S.Type!=EDirectorNodeType::CameraPreset)||S.bActivateCamera))||(S.Type==EDirectorNodeType::Sequence&&DirectorSequence::HasCamera(S))))
        {SequencePlayer->SetDisableCameraCuts(false);bReturningToGameplay=false;FiredControls.Add(I);}
        if(!FiredControls.Contains(I))
        {
            bool Handled=true;
            switch(S.Type)
            {
            case EDirectorNodeType::PlayerHidden:SetPlayerHidden(S.bHidePlayer);break;
            case EDirectorNodeType::InputLock:SetInputLocked(S.bLockInput);break;
            case EDirectorNodeType::HUDHidden:SetHUDHidden(S.bHideHUD);break;
            case EDirectorNodeType::CloseDialogue:
                CurrentDialogue=CurrentSpeaker=FText::GetEmpty();CurrentChoices.Reset();bKeepCurrentDialogue=false;break;
            case EDirectorNodeType::CameraReturn:
                bReturningToGameplay=true;SequencePlayer->SetDisableCameraCuts(true);
                if(Controller.IsValid()){Controller->SetControlRotation(OriginalControlRotation);if(OriginalViewTarget.IsValid())Controller->SetViewTargetWithBlend(OriginalViewTarget.Get(),S.Duration,VTBlend_Linear,0.f,true);}
                FiredControls.Add(I);OnGameplayReturned.Broadcast();if(!SequencePlayer)return;break;
            default:Handled=false;break;
            }
            if(Handled)FiredControls.Add(I);
        }
        if(S.Type==EDirectorNodeType::SetInt&&!FiredControls.Contains(I)){IntValues.Add(S.IntKey,S.IntValue);FiredControls.Add(I);}
        if(S.Type==EDirectorNodeType::SetBool&&!FiredControls.Contains(I))
        {BoolValues.Add(S.BoolKey,S.BoolValue);FiredControls.Add(I);}
        if((S.Type==EDirectorNodeType::CinematicMode||S.Type==EDirectorNodeType::GameplayReturn)&&!FiredControls.Contains(I))
        {
            FiredControls.Add(I);
            if(S.Type==EDirectorNodeType::GameplayReturn)
            {
                if(GameplayPose.IsSet()&&Controller.IsValid()&&Controller->GetPawn()){Controller->GetPawn()->SetActorLocationAndRotation(GameplayPose->GetLocation(),GameplayPose->Rotator());Controller->SetControlRotation(OriginalControlRotation);}
                RestoreControls();bReturningToGameplay=true;bPlayerHandedBack=true;
                CurrentDialogue=CurrentSpeaker=FText::GetEmpty();CurrentChoices.Reset();
                SequencePlayer->SetDisableCameraCuts(true);
                if(Controller.IsValid()&&OriginalViewTarget.IsValid())Controller->SetViewTargetWithBlend(OriginalViewTarget.Get(),S.Duration,VTBlend_Linear,0.f,true);
                OnGameplayReturned.Broadcast();if(!SequencePlayer)return;
            }
            else
            {
                if(bReturningToGameplay){RestoreStandIns();RememberStandIns();}bReturningToGameplay=false;bPlayerHandedBack=false;
                SequencePlayer->SetDisableCameraCuts(false);
                if(!Controller.IsValid())continue;
                if(S.bHidePlayer&&!HiddenPlayer.IsValid()&&Controller->GetPawn()){HiddenPlayer=Controller->GetPawn();bPlayerWasHidden=HiddenPlayer->IsHidden();HiddenPlayer->SetActorHiddenInGame(true);}
                if(S.bLockInput||S.bHideHUD){bHideGameWidgets=true;HideGameWidgets();}
                if(S.bLockInput&&!bInputLocked){Controller->SetIgnoreMoveInput(true);Controller->SetIgnoreLookInput(true);bInputLocked=true;}
                if((S.bLockInput||S.bHideHUD)&&!bHUDHidden&&Controller->GetHUD()){bOriginalHUD=Controller->GetHUD()->bShowHUD;Controller->GetHUD()->bShowHUD=false;bHUDHidden=true;}
            }
        }
    }
    if(NewDialogue!=DialogueCue)
    {
        if(VoiceComponent){VoiceComponent->Stop();VoiceComponent->DestroyComponent();VoiceComponent=nullptr;}
        DialogueCue=NewDialogue;if(NewDialogue!=INDEX_NONE||!bKeepCurrentDialogue)CurrentSpeaker=CurrentDialogue=FText::GetEmpty();CurrentChoices.Reset();ChoicePrompt.Invalidate();
        if(NewDialogue!=INDEX_NONE)
        {
            const auto& Cue=ActiveCues[NewDialogue];CurrentDialogue=Cue.Step.DialogueText;CurrentChoices=Cue.Step.Choices;ChoicePrompt=Cue.Step.Id;
            CurrentSpeaker=Cue.Step.ResolveSpeaker();CurrentDialoguePosition=Cue.Step.DialoguePosition;bKeepCurrentDialogue=Cue.Step.bKeepDialogueOpen;
            if(Cue.Step.Voice)VoiceComponent=UGameplayStatics::SpawnSound2D(this,Cue.Step.Voice,1,1,float(Seconds-Cue.StartFrame/30.0),nullptr,false,false);
        }
    }
    if(bPlayerHandedBack)for(const auto& C:ActiveCues)if(DirectorNodes::IsNPC(C.Step.Type)&&C.Step.bPlayerStandIn)if(auto* NPC=FindNPC(C.Step.Role);NPC&&(!Controller.IsValid()||NPC!=Controller->GetPawn())){if(!StandInVisibility.Contains(NPC))StandInVisibility.Add(NPC,NPC->IsHidden());NPC->SetActorHiddenInGame(true);}
    ApplyActorDeactivations();ControlCharacters();
    if(Performance&&!Performance->Evaluate(ActiveCues,Frame,[this](FName Key){return FindNPC(Key);},LastError))StopDirector();
}

void ASceneDirectorPlayer::ApplyOrigin()
{
    if(!SequenceActor)return;auto* Data=NewObject<UDefaultLevelSequenceInstanceData>(SequenceActor);Data->TransformOrigin=OriginDelta;SequenceActor->DefaultInstanceData=Data;SequenceActor->bOverrideInstanceData=true;
}
AActor* ASceneDirectorPlayer::ResolveObject(FName Key) const
{
    const auto* Source=RuntimeSource?RuntimeSource.Get():Director.Get();if(!Source||Key.IsNone())return nullptr;
    const auto* Entry=Source->Objects.FindByPredicate([Key](const FDirectorObjectEntry& E){return E.Key==Key;});if(!Entry)return nullptr;
    AActor* Result=nullptr;if(const auto* Found=ObjectBindings.Find(Key))Result=Found->Get();
    else if(!Entry->ActorTag.IsNone())for(TActorIterator<AActor> It(GetWorld());It;++It)if(It->ActorHasTag(Entry->ActorTag)){if(Result)return nullptr;Result=*It;}
    return IsValid(Result)&&Result->GetWorld()==GetWorld()&&(!Entry->ActorClass||Result->IsA(Entry->ActorClass))?Result:nullptr;
}


void ASceneDirectorPlayer::RestoreStandIns()
{for(const auto& P:StandInVisibility)if(P.Key.IsValid())P.Key->SetActorHiddenInGame(P.Value);for(const auto& P:StandInComponentVisibility)if(P.Key.IsValid())P.Key->SetVisibility(P.Value);StandInVisibility.Reset();StandInComponentVisibility.Reset();}
void ASceneDirectorPlayer::RememberStandIns()
{for(const auto& C:ActiveCues)if(DirectorNodes::IsNPC(C.Step.Type)&&C.Step.bPlayerStandIn)if(auto* A=FindNPC(C.Step.Role);A&&!StandInVisibility.Contains(A)){StandInVisibility.Add(A,A->IsHidden());for(auto* Comp:A->GetComponents())if(auto* P=Cast<UPrimitiveComponent>(Comp))StandInComponentVisibility.Add(P,P->IsVisible());}}

bool ASceneDirectorPlayer::CaptureGameplayPose(AActor* Target){if(!IsValid(Target))return false;GameplayPose=Target->GetActorTransform();return true;}

void ASceneDirectorPlayer::SetActorDeactivated(AActor* Target,bool bDeactivated)
{
    if(!IsValid(Target))return;
    if(bDeactivated)DeactivatedActors.Add(Target);else DeactivatedActors.Remove(Target);
    Target->SetActorHiddenInGame(bDeactivated);
}
void ASceneDirectorPlayer::ApplyActorDeactivations()
{
    for(auto Target:DeactivatedActors)if(Target.IsValid())Target->SetActorHiddenInGame(true);
}
// Sequencer transforms and CharacterMovement must never drive the same character concurrently.
// Keep this in the player so object bindings and spawned NPCs obey the same lifecycle.
void ASceneDirectorPlayer::ControlCharacters()
{
    for(const auto& Cue:ActiveCues)if(DirectorNodes::IsNPC(Cue.Step.Type))
    {
        auto* Character=Cast<ACharacter>(FindNPC(Cue.Step.Role));if(!Character)continue;
        if(bPlayerHandedBack&&Controller.IsValid()&&Character==Controller->GetPawn())
        {
            if(auto* State=ControlledCharacters.Find(Character)){RestoreCharacter(Character,*State,false);ControlledCharacters.Remove(Character);}
            continue;
        }
        auto* Move=Character->GetCharacterMovement();if(!Move)continue;
        auto* State=ControlledCharacters.Find(Character);
        if(!State)
        {
            FControlledCharacter Snapshot;Snapshot.MovementMode=uint8(Move->MovementMode);Snapshot.CustomMode=Move->CustomMovementMode;Snapshot.Velocity=Move->Velocity;
            State=&ControlledCharacters.Add(Character,MoveTemp(Snapshot));
        }
        State->bStandIn|=Cue.Step.bPlayerStandIn&&(!Controller.IsValid()||Character!=Controller->GetPawn());
        for(auto* Component:Character->GetComponents())if(auto* Primitive=Cast<UPrimitiveComponent>(Component))
        {
            if(!State->Collisions.Contains(Primitive))State->Collisions.Add(Primitive,Primitive->GetCollisionEnabled());
            Primitive->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        }
        Move->StopMovementImmediately();Move->DisableMovement();
    }
}
void ASceneDirectorPlayer::RestoreCharacter(ACharacter* Character,const FControlledCharacter& State,bool bKeepInactive)
{
    if(auto* Move=Character->GetCharacterMovement())
    {
        if(bKeepInactive){Move->StopMovementImmediately();Move->DisableMovement();}
        else{Move->SetMovementMode(EMovementMode(State.MovementMode),State.CustomMode);Move->Velocity=State.Velocity;}
    }
    for(const auto& Pair:State.Collisions)if(Pair.Key.IsValid())Pair.Key->SetCollisionEnabled(bKeepInactive?ECollisionEnabled::NoCollision:Pair.Value);
}
void ASceneDirectorPlayer::RestoreCharacters()
{
    for(const auto& Pair:ControlledCharacters)if(auto* Character=Pair.Key.Get())
        RestoreCharacter(Character,Pair.Value,DeactivatedActors.Contains(Character)||(Pair.Value.bStandIn&&Character->IsHidden()));
    ControlledCharacters.Reset();
}

void ASceneDirectorPlayer::SetInputLocked(bool Locked)
{
    if(Controller.IsValid()&&Locked!=bInputLocked)
    {Controller->SetIgnoreMoveInput(Locked);Controller->SetIgnoreLookInput(Locked);bInputLocked=Locked;}
}
void ASceneDirectorPlayer::SetHUDHidden(bool Hidden)
{
    bHideGameWidgets=Hidden;
    if(Hidden)HideGameWidgets();
    else{for(const auto& Pair:WidgetVisibility)if(Pair.Key.IsValid())Pair.Key->SetVisibility(ESlateVisibility(Pair.Value));WidgetVisibility.Reset();}
    if(Controller.IsValid()&&Controller->GetHUD())
    {
        if(Hidden&&!bHUDHidden){bOriginalHUD=Controller->GetHUD()->bShowHUD;Controller->GetHUD()->bShowHUD=false;}
        else if(!Hidden&&bHUDHidden)Controller->GetHUD()->bShowHUD=bOriginalHUD;
    }
    bHUDHidden=Hidden;
}
void ASceneDirectorPlayer::SetPlayerHidden(bool Hidden)
{
    if(Hidden)
    {
        if(bPlayerHandedBack){RestoreStandIns();RememberStandIns();}bPlayerHandedBack=false;
        if(Controller.IsValid()&&!HiddenPlayer.IsValid()&&Controller->GetPawn())
        {HiddenPlayer=Controller->GetPawn();bPlayerWasHidden=HiddenPlayer->IsHidden();HiddenPlayer->SetActorHiddenInGame(true);}
    }
    else
    {
        // Transfer the stand-in pose before displaying the player, in the same game-thread update.
        if(GameplayPose.IsSet()&&Controller.IsValid()&&Controller->GetPawn())Controller->GetPawn()->SetActorLocationAndRotation(GameplayPose->GetLocation(),GameplayPose->Rotator());
        if(HiddenPlayer.IsValid())HiddenPlayer->SetActorHiddenInGame(bPlayerWasHidden);HiddenPlayer.Reset();bPlayerHandedBack=true;
    }
}
